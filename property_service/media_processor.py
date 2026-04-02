import os
import shutil
import uuid
from PIL import Image
from typing import Tuple, Dict, Any

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class MediaProcessor:
    @staticmethod
    def process_and_store(file_obj, filename: str) -> Dict[str, Any]:
        """
        Saves the raw file, converts to WebP, and generates thumbnails.
        Returns a dictionary of metadata (raw_url, thumb_url, mime, size, width, height)
        """
        unique_id = str(uuid.uuid4())
        ext = os.path.splitext(filename)[1].lower()
        
        # Paths
        raw_filename = f"raw_{unique_id}{ext}"
        webp_filename = f"p_{unique_id}.webp"
        thumb_filename = f"t_{unique_id}.webp"
        
        raw_path = os.path.join(UPLOAD_DIR, raw_filename)
        webp_path = os.path.join(UPLOAD_DIR, webp_filename)
        thumb_path = os.path.join(UPLOAD_DIR, thumb_filename)
        
        # Save original first
        file_obj.seek(0)
        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(file_obj, buffer)
            
        file_size = os.path.getsize(raw_path)
        mime = f"image/{ext[1:]}" if ext in ['.jpg', '.jpeg', '.png', '.webp'] else "application/octet-stream"
        width, height = 0, 0
        
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
                # Use WebP as the "raw" url for the frontend for performance
                final_url = f"http://127.0.0.1:8000/static/{webp_filename}"
                final_thumb = f"http://127.0.0.1:8000/static/{thumb_filename}"
            except Exception as e:
                print(f"Error processing image: {e}")
                final_url = f"http://127.0.0.1:8000/static/{raw_filename}"
                final_thumb = None
        else:
            final_url = f"http://127.0.0.1:8000/static/{raw_filename}"
            final_thumb = None
                
        return {
            "url": final_url,
            "thumbnailUrl": final_thumb,
            "mime": mime,
            "size": file_size,
            "width": width,
            "height": height
        }
