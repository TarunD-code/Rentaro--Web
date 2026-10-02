import sqlite3
import os
import sys
import logging
import json
from datetime import datetime

# Add root folder to python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import shared_database

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sqlite_to_postgres")

# Define SQLite database mappings to PostgreSQL schemas
DB_MAPPING = {
    "rentora_auth.db": "auth",
    "rentora_profile.db": "profile",
    "rentora_properties_v2.db": "property",
    "rentora_payments.db": "payment",
    "rentora_maintenance.db": "maintenance",
    "rentora_onboarding.db": "onboarding",
    "rentora_agreements.db": "agreements",
    "rentora_billing.db": "billing",
    "rentora_owner_dashboard.db": "owner_dashboard",
    "rentora_subscriptions.db": "subscriptions",
    "rentora_support.db": "support",
    "rentora_notifications.db": "notifications",
    "rentora_communication.db": "communication"
}

def clean_value(col_name, val, target_type):
    """Formats SQLite values into PostgreSQL compatible types."""
    if val is None:
        return None
        
    # Convert SQLite 1/0 integers to Boolean for Postgres
    if "boolean" in target_type.lower() or col_name.startswith("is_") or col_name.endswith("_verified"):
        if isinstance(val, int):
            return True if val == 1 else False
        if isinstance(val, str):
            return val.lower() in ("true", "1", "yes")
            
    # Convert string timestamps to datetime objects
    if "timestamp" in target_type.lower() or "datetime" in target_type.lower() or col_name.endswith("_at") or col_name == "requested_slot" or col_name == "expected_vacate_date" or col_name == "actual_vacate_date":
        if isinstance(val, str):
            # Strip trailing Z or +00:00 to match standard formats
            val_clean = val.split("+")[0].rstrip("Z")
            for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(val_clean, fmt)
                except ValueError:
                    continue
        return val

    # Convert string stored JSON back to dictionary objects for PostgreSQL JSON fields
    if "json" in target_type.lower() or col_name == "metadata_json" or col_name == "details" or col_name == "payload" or col_name == "deductions_json":
        if isinstance(val, str):
            try:
                return json.loads(val)
            except Exception:
                pass
                
    return val

def migrate_data():
    logger.info("Initializing Rentora SQLite-to-PostgreSQL ETL Engine...")
    
    if not shared_database.sync_engine:
        logger.error("PostgreSQL sync engine not available. Is PostgreSQL running?")
        return False
        
    success_count = 0
    failure_count = 0
    
    for db_file, schema in DB_MAPPING.items():
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), db_file)
        if not os.path.exists(db_path):
            logger.warning(f"SQLite file not found, skipping: {db_file}")
            continue
            
        logger.info(f"Processing database: {db_file} -> Postgres schema: {schema}")
        
        try:
            sqlite_conn = sqlite3.connect(db_path)
            sqlite_cur = sqlite_conn.cursor()
            
            # Retrieve all tables
            sqlite_cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in sqlite_cur.fetchall() if not row[0].startswith('sqlite_')]
            
            with shared_database.sync_engine.connect() as pg_conn:
                for table in tables:
                    logger.info(f"  Migrating Table: {table}...")
                    
                    # Get table columns and their types
                    sqlite_cur.execute(f"PRAGMA table_info([{table}])")
                    cols_info = sqlite_cur.fetchall()
                    col_names = [col[1] for col in cols_info]
                    col_types = {col[1]: col[2] for col in cols_info}
                    
                    # Fetch all rows from SQLite
                    sqlite_cur.execute(f"SELECT * FROM [{table}]")
                    rows = sqlite_cur.fetchall()
                    sqlite_count = len(rows)
                    
                    if sqlite_count == 0:
                        logger.info(f"    Table {table} is empty in SQLite. Skipping migration.")
                        continue
                        
                    # Clear target PostgreSQL table first to prevent duplicate keys on re-runs
                    pg_table = f"{schema}.{table}"
                    try:
                        pg_conn.execute(f"TRUNCATE TABLE {pg_table} RESTART IDENTITY CASCADE")
                        pg_conn.commit()
                    except Exception as e:
                        logger.warning(f"    Failed to truncate {pg_table} (perhaps table or cascade not supported): {e}")
                    
                    # Determine target database types in PostgreSQL
                    pg_cols_info = pg_conn.execute(f"""
                        SELECT column_name, data_type 
                        FROM information_schema.columns 
                        WHERE table_schema = '{schema}' AND table_name = '{table}'
                    """).fetchall()
                    pg_types = {row[0]: row[1] for row in pg_cols_info}
                    
                    inserted_rows = 0
                    for row in rows:
                        row_dict = dict(zip(col_names, row))
                        
                        # Process and clean values for PG
                        cleaned_row = {}
                        for col, val in row_dict.items():
                            target_type = pg_types.get(col, "varchar")
                            cleaned_row[col] = clean_value(col, val, target_type)
                            
                        # Build dynamic insert statement
                        cols_placeholder = ", ".join([f"%({col})s" for col in cleaned_row.keys()])
                        cols_names_str = ", ".join(cleaned_row.keys())
                        query = f"INSERT INTO {schema}.{table} ({cols_names_str}) VALUES ({cols_placeholder})"
                        
                        try:
                            pg_conn.execute(query, cleaned_row)
                            inserted_rows += 1
                        except Exception as e:
                            logger.error(f"    Error inserting row {row_dict.get('id')} into {pg_table}: {e}")
                            pg_conn.rollback()
                            
                    pg_conn.commit()
                    
                    # Verify count matching
                    pg_count = pg_conn.execute(f"SELECT COUNT(*) FROM {pg_table}").fetchone()[0]
                    
                    if sqlite_count == pg_count:
                        logger.info(f"    ✅ Success: {pg_table} count matched! ({sqlite_count} rows)")
                        success_count += 1
                    else:
                        logger.error(f"    ❌ Count mismatch on {pg_table}! SQLite={sqlite_count}, Postgres={pg_count}")
                        failure_count += 1
                        
            sqlite_conn.close()
        except Exception as e:
            logger.error(f"Failed to migrate database {db_file}: {e}")
            failure_count += 1
            
    logger.info(f"\nMigration Summary: {success_count} tables migrated successfully, {failure_count} failures.")
    return True if failure_count == 0 else False

if __name__ == "__main__":
    migrate_data()
