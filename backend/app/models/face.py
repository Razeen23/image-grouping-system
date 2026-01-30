"""Face model."""
from sqlalchemy import Column, ForeignKey, Float, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
import uuid
from app.database import Base


class Face(Base):
    """Face model - the primary entity for face recognition."""
    __tablename__ = "faces"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_id = Column(UUID(as_uuid=True), ForeignKey("images.id", ondelete="CASCADE"), nullable=False)
    embedding = Column(Vector(512), nullable=False)  # InsightFace 512-dim embedding
    bounding_box = Column(JSON, nullable=False)  # {x, y, width, height}
    confidence = Column(Float, nullable=True)
    detected_at = Column(DateTime(timezone=True), server_default=func.now())
    person_group_id = Column(UUID(as_uuid=True), ForeignKey("person_groups.id", ondelete="SET NULL"), nullable=True)
    
    # Relationships
    image = relationship("Image", back_populates="faces")
    person_group = relationship("PersonGroup", foreign_keys=[person_group_id], back_populates="faces")
    assignments = relationship("FaceGroupAssignment", back_populates="face", cascade="all, delete-orphan")
