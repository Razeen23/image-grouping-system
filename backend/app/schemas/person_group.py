"""Person Group schemas."""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID


class PersonGroupBase(BaseModel):
    """Base person group schema."""
    name: Optional[str] = None


class PersonGroupCreate(PersonGroupBase):
    """Schema for creating a person group."""
    representative_face_id: Optional[UUID] = None


class PersonGroupResponse(PersonGroupBase):
    """Schema for person group response."""
    id: UUID
    representative_face_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PersonGroup(PersonGroupResponse):
    """Full person group schema."""
    pass
