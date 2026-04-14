import os
import hashlib
import json
from datetime import datetime

STORAGE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'storage', 'agreements')

class DocumentVault:
    def __init__(self):
        os.makedirs(STORAGE_DIR, exist_ok=True)
        # Setup Audit Logs Directory
        self.audit_dir = os.path.join(STORAGE_DIR, 'audit_logs')
        os.makedirs(self.audit_dir, exist_ok=True)
        
    def store_document(self, doc_id: int, pdf_bytes: bytes) -> str:
        """ Store PDF securely and return its SHA-256 hash """
        file_path = os.path.join(STORAGE_DIR, f"agreement_{doc_id}.pdf")
        with open(file_path, "wb") as f:
            f.write(pdf_bytes)
            
        doc_hash = hashlib.sha256(pdf_bytes).hexdigest()
        self._log_audit_event(doc_id, "STORE", f"Document stored with hash {doc_hash}")
        return doc_hash
        
    def retrieve_document(self, doc_id: int) -> bytes:
        """ Fetch binary PDF data """
        file_path = os.path.join(STORAGE_DIR, f"agreement_{doc_id}.pdf")
        if not os.path.exists(file_path):
            raise FileNotFoundError("Document not found in vault")
            
        self._log_audit_event(doc_id, "RETRIEVE", "Document downloaded")
        with open(file_path, "rb") as f:
            return f.read()
            
    def sign_document_event(self, doc_id: int, role: str, actor_id: str, sig_hash: str):
        self._log_audit_event(doc_id, "SIGN", f"Signature applied by {role} ({actor_id}). Sig Hash: {sig_hash}")
        
    def _log_audit_event(self, doc_id: int, action: str, details: str):
        # We write JSON audit lines
        log_file = os.path.join(self.audit_dir, f"audit_{doc_id}.jsonl")
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "details": details
        }
        with open(log_file, "a") as f:
            f.write(json.dumps(event) + "\n")
