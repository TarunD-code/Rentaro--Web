import time
import uuid
import httpx
import logging

class SignNowProvider:
    """ 
    Integration wrapper for SignNow API. 
    Uses simulated mock logic if tokens are missing.
    """
    def __init__(self, token: str = None):
        self.token = token
        
    async def request_signature(self, document_id: int, signer_role: str, email: str) -> dict:
        """
        In production, calls POST /document/{id}/invite
        """
        # Mock API Call Delay
        time.sleep(0.5) 
        signnow_id = str(uuid.uuid4())
        
        logging.info(f"[SignNow] Requested signature for Doc {document_id} to {email} ({signer_role}) -> Session: {signnow_id}")
        return {
            "status": "success",
            "session_id": signnow_id,
            "provider": "SignNow Mock"
        }
    
    def verify_signature(self, session_id: str) -> dict:
        """
        Mock verification of an e-signature event.
        Calculates a mock signature hash.
        """
        sig_hash = f"sig_hash_{uuid.uuid4().hex[:12]}"
        return {
            "is_valid": True,
            "signature_hash": sig_hash,
            "timestamp": time.time()
        }
