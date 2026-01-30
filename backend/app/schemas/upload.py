"""Upload schemas."""
from pydantic import BaseModel
from typing import List
from uuid import UUID


class UploadResponse(BaseModel):
    """Response schema for image upload."""
    image_id: UUID
    filename: str
    message: str
