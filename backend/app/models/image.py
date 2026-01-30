"""Image model."""
from sqlalchemy import Column, String, BigInteger, Integer, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base


class Image(Base):
    """Image model representing uploaded photos."""
    __tablename__ = "images"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    storage_key = Column(String(500), nullable=False, unique=True)
    storage_url = Column(Text)
    mime_type = Column(String(100))
    file_size = Column(BigInteger)
    width = Column(Integer)
    height = Column(Integer)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_status = Column(String(20), default="pending")  # pending, processing, completed, failed
    
    # Relationships
    faces = relationship("Face", back_populates="image", cascade="all, delete-orphan")
