"""Face Group Assignment model."""
from sqlalchemy import Column, ForeignKey, Float, DateTime, PrimaryKeyConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class FaceGroupAssignment(Base):
    """Face-to-PersonGroup assignment (many-to-many relationship)."""
    __tablename__ = "face_group_assignments"
    
    face_id = Column(UUID(as_uuid=True), ForeignKey("faces.id", ondelete="CASCADE"), nullable=False)
    person_group_id = Column(UUID(as_uuid=True), ForeignKey("person_groups.id", ondelete="CASCADE"), nullable=False)
    similarity_score = Column(Float, nullable=True)  # Cosine similarity at assignment time
    assigned_at = Column(DateTime(timezone=True), server_default=func.now())
    
    __table_args__ = (
        PrimaryKeyConstraint('face_id', 'person_group_id'),
    )
    
    # Relationships
    face = relationship("Face", back_populates="assignments")
    person_group = relationship("PersonGroup", back_populates="assignments")
