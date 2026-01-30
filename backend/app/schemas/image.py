"""Image schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class ImageBase(BaseModel):
    """Base image schema."""
    filename: str
    storage_key: str
    storage_url: Optional[str] = None
    mime_type: Optional[str] = None
    file_size: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None


class ImageCreate(ImageBase):
    """Schema for creating an image."""
    pass


class ImageResponse(ImageBase):
    """Schema for image response."""
    id: UUID
    uploaded_at: datetime
    processed_at: Optional[datetime] = None
    processing_status: str
    
    class Config:
        from_attributes = True


class Image(ImageResponse):
    """Full image schema."""
    pass
