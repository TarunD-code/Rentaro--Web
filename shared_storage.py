import os
import shutil
import uuid
import logging
from typing import List, Optional

# CENTRALIZED LOGGER
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("shared_storage")

# MANUALLY LOAD .ENV IF EXISTS
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, val = line.split("=", 1)
                os.environ[key.strip()] = val.strip()

# ENVIRONMENT CONFIGURATIONS
STORAGE_PROVIDER = os.environ.get("STORAGE_PROVIDER", "local").lower()  # local, s3, r2
R2_ACCESS_KEY = os.environ.get("R2_ACCESS_KEY", "")
R2_SECRET_KEY = os.environ.get("R2_SECRET_KEY", "")
R2_BUCKET = os.environ.get("R2_BUCKET", "rentora-bucket")
R2_ENDPOINT = os.environ.get("R2_ENDPOINT", "")
S3_REGION = os.environ.get("S3_REGION", "us-east-1")
S3_BUCKET = os.environ.get("S3_BUCKET", "rentora-bucket")

# MINIO / AWS FALLBACKS
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")

# LOCAL SIMULATION CONFIG
LOCAL_UPLOAD_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
os.makedirs(LOCAL_UPLOAD_DIR, exist_ok=True)
STATIC_HOST_URL = "http://127.0.0.1:8000/static"

# LAZY BOTO3 INITIALIZER
_s3_client = None

def _get_s3_client():
    global _s3_client
    if _s3_client is not None:
        return _s3_client
        
    try:
        import boto3
        from botocore.config import Config
    except ImportError:
        logger.error("boto3 package not installed! Defaulting to local storage provider simulation.")
        return None

    try:
        if STORAGE_PROVIDER == "r2":
            logger.info("Initializing Cloudflare R2 Connection pool...")
            _s3_client = boto3.client(
                "s3",
                aws_access_key_id=R2_ACCESS_KEY,
                aws_secret_access_key=R2_SECRET_KEY,
                endpoint_url=R2_ENDPOINT,
                config=Config(signature_version="s3v4")
            )
        else:
            logger.info("Initializing AWS S3 Connection pool...")
            _s3_client = boto3.client(
                "s3",
                aws_access_key_id=AWS_ACCESS_KEY_ID,
                aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                region_name=S3_REGION
            )
        return _s3_client
    except Exception as e:
        logger.error(f"Failed to initialize S3/R2 client: {e}. Falling back to local simulation.")
        return None

# CORE STORAGE API
def upload_file(file_obj, file_key: str, content_type: str = None) -> str:
    """
    Uploads a file (file-like object or bytes) to object storage or local simulation.
    Returns the CDN/publicly-accessible access URL.
    """
    # Standardize path slashes inside keys
    file_key = file_key.replace("\\", "/")
    
    # 1. LOCAL SIMULATION FALLBACK
    if STORAGE_PROVIDER == "local" or _get_s3_client() is None:
        target_path = os.path.join(LOCAL_UPLOAD_DIR, file_key)
        target_dir = os.path.dirname(target_path)
        os.makedirs(target_dir, exist_ok=True)
        
        # Write bytes or copy file object
        if hasattr(file_obj, "seek"):
            file_obj.seek(0)
            with open(target_path, "wb") as buffer:
                shutil.copyfileobj(file_obj, buffer)
        else:
            # Assumed bytes
            with open(target_path, "wb") as buffer:
                buffer.write(file_obj)
                
        logger.info(f"[Local Storage] Uploaded: {file_key}")
        return f"{STATIC_HOST_URL}/{file_key}"

    # 2. S3/R2 OBJECT STORAGE PROVIDER
    bucket = R2_BUCKET if STORAGE_PROVIDER == "r2" else S3_BUCKET
    client = _get_s3_client()
    
    try:
        # Prepare bytes
        if hasattr(file_obj, "read"):
            if hasattr(file_obj, "seek"):
                file_obj.seek(0)
            data = file_obj.read()
        else:
            data = file_obj
            
        extra_args = {}
        if content_type:
            extra_args["ContentType"] = content_type
            
        client.put_object(
            Bucket=bucket,
            Key=file_key,
            Body=data,
            **extra_args
        )
        logger.info(f"[Object Storage] Uploaded to {STORAGE_PROVIDER}: {file_key}")
        return get_public_url(file_key)
    except Exception as e:
        logger.error(f"Object Storage upload failed: {e}. Writing to local simulation.")
        # Graceful fallback to prevent crash in request paths
        fallback_url = upload_file_fallback(file_obj, file_key)
        return fallback_url

def upload_file_fallback(file_obj, file_key: str) -> str:
    target_path = os.path.join(LOCAL_UPLOAD_DIR, file_key)
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    if hasattr(file_obj, "seek"):
        file_obj.seek(0)
        with open(target_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
    else:
        with open(target_path, "wb") as buffer:
            buffer.write(file_obj)
    return f"{STATIC_HOST_URL}/{file_key}"

def delete_file(file_key: str) -> bool:
    """ Deletes a file from storage provider. """
    file_key = file_key.replace("\\", "/")
    
    if STORAGE_PROVIDER == "local" or _get_s3_client() is None:
        target_path = os.path.join(LOCAL_UPLOAD_DIR, file_key)
        if os.path.exists(target_path):
            try:
                os.remove(target_path)
                logger.info(f"[Local Storage] Deleted file: {file_key}")
                return True
            except Exception as e:
                logger.error(f"Failed to delete local file: {e}")
                return False
        return False
        
    bucket = R2_BUCKET if STORAGE_PROVIDER == "r2" else S3_BUCKET
    client = _get_s3_client()
    try:
        client.delete_object(Bucket=bucket, Key=file_key)
        logger.info(f"[Object Storage] Deleted from {STORAGE_PROVIDER}: {file_key}")
        return True
    except Exception as e:
        logger.error(f"Failed to delete object from storage: {e}")
        return False

def get_public_url(file_key: str) -> str:
    """ Computes the public URL for standard CDN routing. """
    file_key = file_key.replace("\\", "/")
    
    if STORAGE_PROVIDER == "local" or _get_s3_client() is None:
        return f"{STATIC_HOST_URL}/{file_key}"
        
    if STORAGE_PROVIDER == "r2":
        # Extract base custom domain or public endpoint if set
        if R2_ENDPOINT:
            endpoint_clean = R2_ENDPOINT.rstrip("/")
            if "r2.cloudflarestorage.com" in R2_ENDPOINT:
                # Direct bucket endpoint or public CDN url helper
                return f"{endpoint_clean}/{R2_BUCKET}/{file_key}"
            return f"{endpoint_clean}/{file_key}"
        return f"https://{R2_BUCKET}.r2.cloudflarestorage.com/{file_key}"
        
    # AWS S3 URL Standard format
    return f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file_key}"

def get_signed_url(file_key: str, expires_in: int = 3600) -> str:
    """ Generates a presigned GET URL for protected documents. """
    file_key = file_key.replace("\\", "/")
    
    if STORAGE_PROVIDER == "local" or _get_s3_client() is None:
        # Local fallback does not support signatures, return public url
        return f"{STATIC_HOST_URL}/{file_key}"
        
    bucket = R2_BUCKET if STORAGE_PROVIDER == "r2" else S3_BUCKET
    client = _get_s3_client()
    try:
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": file_key},
            ExpiresIn=expires_in
        )
        return url
    except Exception as e:
        logger.error(f"Failed to generate presigned URL: {e}")
        return get_public_url(file_key)

def list_files(prefix: str = "") -> List[str]:
    """ Lists keys stored inside the storage bucket matching the prefix. """
    prefix = prefix.replace("\\", "/")
    
    if STORAGE_PROVIDER == "local" or _get_s3_client() is None:
        folder_path = os.path.join(LOCAL_UPLOAD_DIR, prefix)
        if not os.path.exists(folder_path):
            return []
        keys = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, LOCAL_UPLOAD_DIR)
                keys.append(rel_path.replace("\\", "/"))
        return keys
        
    bucket = R2_BUCKET if STORAGE_PROVIDER == "r2" else S3_BUCKET
    client = _get_s3_client()
    try:
        response = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        if "Contents" not in response:
            return []
        return [obj["Key"] for obj in response["Contents"]]
    except Exception as e:
        logger.error(f"Failed to list objects: {e}")
        return []

def retrieve_file(file_key: str) -> bytes:
    """ Retrieves binary content of a file from storage. """
    file_key = file_key.replace("\\", "/")
    
    if STORAGE_PROVIDER == "local" or _get_s3_client() is None:
        target_path = os.path.join(LOCAL_UPLOAD_DIR, file_key)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"File not found: {file_key}")
        with open(target_path, "rb") as f:
            return f.read()
            
    bucket = R2_BUCKET if STORAGE_PROVIDER == "r2" else S3_BUCKET
    client = _get_s3_client()
    try:
        response = client.get_object(Bucket=bucket, Key=file_key)
        return response["Body"].read()
    except Exception as e:
        logger.error(f"Failed to retrieve file from object storage: {e}")
        # Try local fallback
        target_path = os.path.join(LOCAL_UPLOAD_DIR, file_key)
        if os.path.exists(target_path):
            with open(target_path, "rb") as f:
                return f.read()
        raise e

