"""Face schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


class FaceBase(BaseModel):
    """Base face schema."""
    bounding_box: Dict[str, Any]
    confidence: Optional[float] = None


class FaceResponse(FaceBase):
    """Schema for face response."""
    id: UUID
    image_id: UUID
    detected_at: datetime
    person_group_id: Optional[UUID] = None
    
    class Config:
        from_attributes = True


class Face(FaceResponse):
    """Full face schema."""
    pass
