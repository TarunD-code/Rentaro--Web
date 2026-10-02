"""
Rentora KYC — Column-Level Encryption Engine
=============================================

Uses Fernet symmetric encryption (AES-128-CBC via cryptography library)
for at-rest protection of PII fields (Aadhaar, PAN).

SECURITY NOTES:
- The Fernet key MUST be stored in an environment variable, never committed to VCS.
- Key rotation requires re-encrypting all existing records (migrate script needed).
- All encrypt/decrypt operations happen in application memory — never at the DB level.
"""

import os
import re
import logging
from cryptography.fernet import Fernet, InvalidToken

logger = logging.getLogger("kyc_service.encryption")

# ─────────────────────────────────────────────────────────────
# Fernet Key Bootstrap
# ─────────────────────────────────────────────────────────────
# SECURITY: In production, inject via secrets manager (AWS SSM, Vault, etc.)
# For local dev, we auto-generate if missing and warn loudly.
_ENV_KEY = os.environ.get("KYC_ENCRYPTION_KEY")

if not _ENV_KEY:
    logger.warning(
        "⚠️  KYC_ENCRYPTION_KEY not set — generating ephemeral key. "
        "THIS IS UNSUITABLE FOR PRODUCTION. Data encrypted with this key "
        "will be UNRECOVERABLE after restart."
    )
    _ENV_KEY = Fernet.generate_key().decode()
    os.environ["KYC_ENCRYPTION_KEY"] = _ENV_KEY


class CipherEngine:
    """
    Application-level symmetric encryption wrapper for PII fields.
    
    Usage:
        cipher = CipherEngine()
        encrypted = cipher.encrypt("123456781234")   # → bytes
        plaintext = cipher.decrypt(encrypted)          # → "123456781234"
    """

    def __init__(self):
        try:
            self._fernet = Fernet(_ENV_KEY.encode() if isinstance(_ENV_KEY, str) else _ENV_KEY)
        except Exception as e:
            logger.critical(f"Failed to initialize Fernet cipher: {e}")
            raise RuntimeError(
                "KYC_ENCRYPTION_KEY is invalid. Must be a valid Fernet key "
                "(base64-encoded 32-byte key). Generate with: "
                "python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'"
            ) from e

    def encrypt(self, plaintext: str) -> bytes:
        """
        Encrypt a plaintext string to Fernet ciphertext bytes.
        
        SECURITY: Input is encoded to UTF-8 before encryption.
        The output includes an embedded timestamp for key rotation auditing.
        """
        if not plaintext:
            return b""
        return self._fernet.encrypt(plaintext.encode("utf-8"))

    def decrypt(self, ciphertext: bytes) -> str:
        """
        Decrypt Fernet ciphertext bytes back to plaintext string.
        
        Raises InvalidToken if the key doesn't match or data is corrupted.
        """
        if not ciphertext:
            return ""
        try:
            return self._fernet.decrypt(ciphertext).decode("utf-8")
        except InvalidToken:
            logger.error(
                "Fernet decryption failed — possible key mismatch or data corruption. "
                "Check KYC_ENCRYPTION_KEY matches the key used during encryption."
            )
            raise

    # ─────────────────────────────────────────────────────────
    # PII Masking Helpers
    # ─────────────────────────────────────────────────────────

    @staticmethod
    def mask_aadhaar(aadhaar: str) -> str:
        """
        Mask Aadhaar number for safe display.
        
        Input:  "123456781234" (12 digits)
        Output: "XXXX-XXXX-1234"
        
        COMPLIANCE: Only the last 4 digits are retained per
        UIDAI masking guidelines and DPDP Act requirements.
        """
        if not aadhaar:
            return ""
        # Strip any existing formatting (spaces, dashes)
        clean = re.sub(r"[^0-9]", "", aadhaar)
        if len(clean) < 4:
            return "XXXX-XXXX-XXXX"
        return f"XXXX-XXXX-{clean[-4:]}"

    @staticmethod
    def mask_pan(pan: str) -> str:
        """
        Mask PAN number for safe display.
        
        Input:  "ABCDE1234F" (10 alphanumeric)
        Output: "XXXXXX234F"
        
        COMPLIANCE: First 6 characters are redacted,
        last 4 retained for user identification.
        """
        if not pan:
            return ""
        clean = pan.strip().upper()
        if len(clean) < 4:
            return "XXXXXXXXXX"
        return f"XXXXXX{clean[-4:]}"


# Module-level singleton for import convenience
cipher_engine = CipherEngine()
