"""Application configuration using Pydantic settings."""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost/face_groups"
    POSTGRES_DB: str = "face_groups"
    
    # Object Storage (MinIO)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "photos"
    MINIO_USE_SSL: bool = False
    
    # Face Recognition
    INSIGHTFACE_MODEL_PATH: str = "buffalo_l"  # Default model name or path
    FACE_SIMILARITY_THRESHOLD: float = 0.6
    
    # Celery (optional)
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"
    
    # API
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]
    
    # Processing
    ENABLE_AUTO_PROCESSING: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
