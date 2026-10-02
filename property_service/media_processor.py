import os
import shutil
import uuid
import logging
from PIL import Image
from typing import Tuple, Dict, Any
import shared_storage

logger = logging.getLogger("property_service.media")

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

class MediaProcessor:
    @staticmethod
    def process_and_store(file_obj, filename: str) -> Dict[str, Any]:
        """
        Saves the raw file locally for WebP processing, uploads processed files to centralized S3/R2 storage,
        and deletes temporary local copies.
        """
        unique_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1].lower()
        
        # Temp local paths
        raw_filename = f"raw_{unique_id}{ext}"
        webp_filename = f"p_{unique_id}.webp"
        thumb_filename = f"t_{unique_id}.webp"
        
        raw_path = os.path.join(TEMP_DIR, raw_filename)
        webp_path = os.path.join(TEMP_DIR, webp_filename)
        thumb_path = os.path.join(TEMP_DIR, thumb_filename)
        
        # Save original temporarily
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
        with open(raw_path, "wb") as buffer:
            if hasattr(file_obj, "read"):
                buffer.write(file_obj.read())
            else:
                shutil.copyfileobj(file_obj, buffer)
            
        file_size = os.path.getsize(raw_path)
        mime = f"image/{ext[1:]}" if ext in ['.jpg', '.jpeg', '.png', '.webp'] else "application/octet-stream"
        width, height = 0, 0
        
        uploaded_raw_key = f"properties/{raw_filename}"
        uploaded_webp_key = f"properties/{webp_filename}"
        uploaded_thumb_key = f"properties/{thumb_filename}"
        
        final_url = None
        final_thumb = None
        
        # Process Image
        if ext in ['.jpg', '.jpeg', '.png', '.webp']:
            try:
                with Image.open(raw_path) as img:
                    width, height = img.size
                    # Convert to WebP Main (Resized to 1200 max)
                    main_img = img.copy()
                    main_img.thumbnail((1200, 1200))
                    main_img.save(webp_path, "WEBP", quality=80)
                    
                    # Generate Thumbnail WebP
                    thumb_img = img.copy()
                    thumb_img.thumbnail((400, 300))
                    thumb_img.save(thumb_path, "WEBP", quality=60)
                    
                mime = "image/webp"
                
                # Upload webp main and thumb to shared storage
                with open(webp_path, "rb") as f:
                    final_url = shared_storage.upload_file(f, uploaded_webp_key, "image/webp")
                with open(thumb_path, "rb") as f:
                    final_thumb = shared_storage.upload_file(f, uploaded_thumb_key, "image/webp")
            except Exception as e:
                logger.error(f"Error processing image: {e}")
                # Fallback to uploading raw file directly
                with open(raw_path, "rb") as f:
                    final_url = shared_storage.upload_file(f, uploaded_raw_key, mime)
                final_thumb = None
        else:
            # Video or other media attachment, upload directly
            with open(raw_path, "rb") as f:
                final_url = shared_storage.upload_file(f, uploaded_raw_key, mime)
            final_thumb = None
            
        # Clean up temporary local files
        for p in [raw_path, webp_path, thumb_path]:
            if os.path.exists(p):
                try:
                    os.remove(p)
                except Exception as e:
                    logger.warning(f"Could not delete temp file {p}: {e}")
                
        return {
            "url": final_url,
            "thumbnailUrl": final_thumb,
            "mime": mime,
            "size": file_size,
            "width": width,
            "height": height
        }

