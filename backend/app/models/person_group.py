"""Person Group model."""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class PersonGroup(Base):
    """Person Group model representing a unique person."""
    __tablename__ = "person_groups"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=True)  # Optional: user-assigned name
    representative_face_id = Column(UUID(as_uuid=True), ForeignKey("faces.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    representative_face = relationship("Face", foreign_keys=[representative_face_id])
    faces = relationship("Face", foreign_keys="Face.person_group_id", back_populates="person_group")
    assignments = relationship("FaceGroupAssignment", back_populates="person_group", cascade="all, delete-orphan")
