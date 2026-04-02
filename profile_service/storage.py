import os
import shutil
import uuid

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class S3StubStorage:
    @staticmethod
    def upload_file(file_obj, filename: str) -> str:
        """
        Simulates uploading to S3 by saving to a local directory and returning a mock URL.
        """
        unique_filename = f"{uuid.uuid4()}_{filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        # Mock S3 URL
        mock_s3_url = f"https://mock-s3-rentora.amazon.com/bucket/{unique_filename}"
        return mock_s3_url
