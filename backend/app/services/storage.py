"""Object storage service for MinIO/S3."""
from minio import Minio
from minio.error import S3Error
from io import BytesIO
from typing import Optional
import uuid
from app.config import settings


class StorageService:
    """Service for object storage operations."""
    
    def __init__(self):
        """Initialize MinIO client."""
        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """Ensure bucket exists, create if not."""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            raise Exception(f"Failed to create bucket: {e}")
    
    def upload_file(self, file_data: bytes, filename: str, content_type: str) -> tuple[str, str]:
        """
        Upload file to object storage.
        
        Returns:
            tuple: (storage_key, storage_url)
        """
        # Generate unique storage key
        file_ext = filename.split('.')[-1] if '.' in filename else 'jpg'
        storage_key = f"{uuid.uuid4()}.{file_ext}"
        
        try:
            # Upload file
            self.client.put_object(
                self.bucket,
                storage_key,
                BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )
            
            # Generate URL
            storage_url = self._get_object_url(storage_key)
            
            return storage_key, storage_url
        except S3Error as e:
            raise Exception(f"Failed to upload file: {e}")
    
    def get_object(self, storage_key: str) -> bytes:
        """Get object from storage."""
        try:
            response = self.client.get_object(self.bucket, storage_key)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise Exception(f"Failed to get object: {e}")
    
    def delete_object(self, storage_key: str):
        """Delete object from storage."""
        try:
            self.client.remove_object(self.bucket, storage_key)
        except S3Error as e:
            raise Exception(f"Failed to delete object: {e}")
    
    def _get_object_url(self, storage_key: str) -> str:
        """Generate object URL."""
        protocol = "https" if settings.MINIO_USE_SSL else "http"
        return f"{protocol}://{settings.MINIO_ENDPOINT}/{self.bucket}/{storage_key}"


# Singleton instance
storage_service = StorageService()
