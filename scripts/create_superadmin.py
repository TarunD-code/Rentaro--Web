"""
Rentora — Superadmin Seeder
============================
Creates an admin account directly in the database, bypassing the public
registration endpoint (which hard-blocks the 'admin' role).

Usage:
    # From the project root (venv activated):
    python scripts/create_superadmin.py --email admin@rentora.com --password <secure_password>

    # Or let it prompt interactively:
    python scripts/create_superadmin.py

Security notes:
    - Never pass the password as a positional argument in shared environments
      (it will appear in shell history). Use the interactive prompt or
      set SUPERADMIN_PASSWORD in your environment instead.
    - The password is hashed with bcrypt before storage; the plaintext
      never reaches the database.
"""

import os
import sys
import argparse
import getpass
import logging

# ---------------------------------------------------------------------------
# Path setup — allow running from any directory
# ---------------------------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("create_superadmin")

# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed a Rentora admin account directly into the database."
    )
    parser.add_argument(
        "--email",
        default=os.environ.get("SUPERADMIN_EMAIL"),
        help="Admin email address (default: $SUPERADMIN_EMAIL)",
    )
    parser.add_argument(
        "--password",
        default=os.environ.get("SUPERADMIN_PASSWORD"),
        help="Admin password (default: $SUPERADMIN_PASSWORD). "
             "Omit to be prompted securely.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()

    # --- Collect credentials ------------------------------------------------
    email = args.email
    if not email:
        email = input("Admin email: ").strip()
    if not email:
        logger.error("Email cannot be empty.")
        sys.exit(1)

    password = args.password
    if not password:
        password = getpass.getpass("Admin password: ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            logger.error("Passwords do not match.")
            sys.exit(1)

    if len(password) < 8:
        logger.error("Password must be at least 8 characters.")
        sys.exit(1)

    # --- Hash password ------------------------------------------------------
    try:
        import bcrypt
    except ImportError:
        logger.error("bcrypt not installed. Run: pip install bcrypt")
        sys.exit(1)

    hashed_password: str = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    # --- Database connection -------------------------------------------------
    try:
        import shared_database
        from sqlalchemy import text
    except ImportError as exc:
        logger.error(f"Cannot import shared_database: {exc}")
        logger.error("Ensure you are running from the project root with venv active.")
        sys.exit(1)

    if not shared_database.sync_engine:
        logger.error(
            "sync_engine is None — check DATABASE_URL in .env and that "
            "PostgreSQL is reachable."
        )
        sys.exit(1)

    # --- Upsert admin record ------------------------------------------------
    with shared_database.sync_engine.connect() as conn:
        # Ensure the auth schema and users table exist
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS auth"))
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS auth.users (
                id               SERIAL PRIMARY KEY,
                email_or_phone   VARCHAR UNIQUE NOT NULL,
                hashed_password  VARCHAR NOT NULL,
                role             VARCHAR NOT NULL DEFAULT 'tenant',
                is_verified      BOOLEAN NOT NULL DEFAULT FALSE,
                otp_code         VARCHAR
            )
        """))
        conn.commit()

        # Check if admin already exists
        existing = conn.execute(
            text("SELECT id, role FROM auth.users WHERE email_or_phone = :email"),
            {"email": email},
        ).fetchone()

        if existing:
            if existing[1] == "admin":
                logger.warning(f"Admin account '{email}' already exists (id={existing[0]}). Nothing changed.")
                sys.exit(0)
            else:
                # Promote existing account
                conn.execute(
                    text("""
                        UPDATE auth.users
                        SET role = 'admin',
                            hashed_password = :pwd,
                            is_verified = TRUE
                        WHERE email_or_phone = :email
                    """),
                    {"pwd": hashed_password, "email": email},
                )
                conn.commit()
                logger.info(f"Existing account '{email}' promoted to admin and verified.")
        else:
            conn.execute(
                text("""
                    INSERT INTO auth.users
                        (email_or_phone, hashed_password, role, is_verified)
                    VALUES
                        (:email, :pwd, 'admin', TRUE)
                """),
                {"email": email, "pwd": hashed_password},
            )
            conn.commit()
            logger.info(f"Admin account '{email}' created successfully (is_verified=True).")

    logger.info("Done. You can now log in at /login with the admin credentials.")


if __name__ == "__main__":
    main()
