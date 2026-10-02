import sys
import os
import logging
from sqlalchemy import text

# Add parent workspace to system path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_database
import shared_storage

# Setup centralized logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("migrate_to_storage")

LOCAL_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")

def run_asset_migration():
    logger.info("Initializing Rentora Asset Migration Engine...")
    
    if not shared_database.sync_engine:
        logger.error("Centralized PostgreSQL Sync Engine is offline! Ensure Postgres is active.")
        return False
        
    try:
        with shared_database.sync_engine.connect() as conn:
            # 1. PROFILE PHOTO MIGRATION
            logger.info("Examining profile.profiles photo_url columns...")
            try:
                profiles = conn.execute(text("SELECT id, photo_url FROM profile.profiles WHERE photo_url IS NOT NULL")).fetchall()
                for p_id, photo in profiles:
                    new_url = process_url(photo, f"profiles/photo_{p_id}")
                    if new_url != photo:
                        conn.execute(
                            text("UPDATE profile.profiles SET photo_url = :new_url WHERE id = :id"),
                            {"new_url": new_url, "id": p_id}
                        )
                        conn.commit()
                        logger.info(f"Updated Profile photo_url for ID {p_id}: {new_url}")
            except Exception as e:
                logger.warning(f"Could not process profiles table (perhaps unseeded yet): {e}")

            # 2. KYC DOCUMENTS MIGRATION
            logger.info("Examining profile.kyc_documents s3_url columns...")
            try:
                kyc_docs = conn.execute(text("SELECT id, document_type, s3_url FROM profile.kyc_documents WHERE s3_url IS NOT NULL")).fetchall()
                for d_id, doc_type, s3_url in kyc_docs:
                    new_url = process_url(s3_url, f"profiles/kyc_{d_id}_{doc_type}")
                    if new_url != s3_url:
                        conn.execute(
                            text("UPDATE profile.kyc_documents SET s3_url = :new_url WHERE id = :id"),
                            {"new_url": new_url, "id": d_id}
                        )
                        conn.commit()
                        logger.info(f"Updated KYC Document s3_url for ID {d_id}: {new_url}")
            except Exception as e:
                logger.warning(f"Could not process kyc_documents table: {e}")

            # 3. PROPERTY MEDIA MIGRATION
            logger.info("Examining property.property_media urls...")
            try:
                media = conn.execute(text("SELECT id, raw_url, thumb_url FROM property.property_media")).fetchall()
                for m_id, raw, thumb in media:
                    new_raw = process_url(raw, f"properties/raw_{m_id}") if raw else None
                    new_thumb = process_url(thumb, f"properties/thumb_{m_id}") if thumb else None
                    if new_raw != raw or new_thumb != thumb:
                        conn.execute(
                            text("UPDATE property.property_media SET raw_url = :raw, thumb_url = :thumb WHERE id = :id"),
                            {"raw": new_raw, "thumb": new_thumb, "id": m_id}
                        )
                        conn.commit()
                        logger.info(f"Updated PropertyMedia ID {m_id}: raw={new_raw}, thumb={new_thumb}")
            except Exception as e:
                logger.warning(f"Could not process property_media table: {e}")

            # 4. RENTAL AGREEMENTS MIGRATION
            logger.info("Examining property.rental_agreements pdf_url columns...")
            try:
                agreements = conn.execute(text("SELECT id, pdf_url FROM property.rental_agreements WHERE pdf_url IS NOT NULL")).fetchall()
                for a_id, pdf in agreements:
                    new_url = process_url(pdf, f"agreements/agreement_{a_id}")
                    if new_url != pdf:
                        conn.execute(
                            text("UPDATE property.rental_agreements SET pdf_url = :new_url WHERE id = :id"),
                            {"new_url": new_url, "id": a_id}
                        )
                        conn.commit()
                        logger.info(f"Updated RentalAgreement pdf_url for ID {a_id}: {new_url}")
            except Exception as e:
                logger.warning(f"Could not process rental_agreements table: {e}")

            # 5. PAYMENTS RECEIPTS MIGRATION
            logger.info("Examining payment.payment_transactions receipt_url columns...")
            try:
                payments = conn.execute(text("SELECT id, receipt_url FROM payment.payment_transactions WHERE receipt_url IS NOT NULL")).fetchall()
                for pm_id, receipt in payments:
                    new_url = process_url(receipt, f"payments/receipt_{pm_id}")
                    if new_url != receipt:
                        conn.execute(
                            text("UPDATE payment.payment_transactions SET receipt_url = :new_url WHERE id = :id"),
                            {"new_url": new_url, "id": pm_id}
                        )
                        conn.commit()
                        logger.info(f"Updated Payment receipt_url for ID {pm_id}: {new_url}")
            except Exception as e:
                logger.warning(f"Could not process payment_transactions table: {e}")

            # 6. REPORTS MIGRATION
            logger.info("Examining owner_dashboard.owner_reports report_path columns...")
            try:
                reports = conn.execute(text("SELECT id, report_path FROM owner_dashboard.owner_reports WHERE report_path IS NOT NULL")).fetchall()
                for r_id, path in reports:
                    new_url = process_url(path, f"reports/report_{r_id}")
                    if new_url != path:
                        conn.execute(
                            text("UPDATE owner_dashboard.owner_reports SET report_path = :new_url WHERE id = :id"),
                            {"new_url": new_url, "id": r_id}
                        )
                        conn.commit()
                        logger.info(f"Updated OwnerReport report_path for ID {r_id}: {new_url}")
            except Exception as e:
                logger.warning(f"Could not process owner_reports table: {e}")

            logger.info("✅ Rentora asset migration finished successfully!")
            return True
            
    except Exception as e:
        logger.error(f"Failed to run migration: {e}")
        return False

def process_url(url: str, storage_key_base: str) -> str:
    """
    Checks if a URL refers to a local file or standard simulation URL.
    Uploads the file from the local path to the target S3/R2 storage and returns the new public URL.
    Otherwise, returns the url unchanged.
    """
    # Exclude already processed s3/r2 cdn urls
    if url.startswith("https://") and "r2.cloudflarestorage.com" in url:
        return url
    if url.startswith("https://") and "s3.amazonaws.com" in url:
        return url
        
    filename = os.path.basename(url)
    ext = os.path.splitext(filename)[1]
    storage_key = f"{storage_key_base}{ext}"
    
    # 1. Resolve Local Static Mount or Relative Upload Directory
    local_filename = filename
    if "static/" in url:
        # e.g., /static/reports/report_x.pdf or http://127.0.0.1:8000/static/reports/report_x.pdf
        parts = url.split("static/")[-1].split("/")
        local_filename = os.path.join(*parts)
        
    local_filepath = os.path.join(LOCAL_UPLOAD_DIR, local_filename)
    
    # If the file really exists locally, upload it
    if os.path.exists(local_filepath):
        try:
            logger.info(f"Uploading legacy asset: {local_filepath} -> Key: {storage_key}...")
            with open(local_filepath, "rb") as f:
                new_url = shared_storage.upload_file(f, storage_key)
            return new_url
        except Exception as e:
            logger.error(f"Failed to migrate file {local_filepath}: {e}")
            return url
            
    # Mock URLs check (e.g. from seeders)
    if "mock-s3-rentora" in url or "docusign" in url:
        # Just convert them to our standard public/signed URL key mapping
        return shared_storage.get_public_url(storage_key)
        
    return url

if __name__ == "__main__":
    run_asset_migration()
