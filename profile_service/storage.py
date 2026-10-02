import uuid
import shared_storage

class S3StubStorage:
    @staticmethod
    def upload_file(file_obj, filename: str) -> str:
        """
        Uploads a file to centralized object storage or local simulation under the profiles prefix.
        """
        unique_filename = f"profiles/{uuid.uuid4()}_{filename}"
        public_url = shared_storage.upload_file(file_obj, unique_filename)
        return public_url

