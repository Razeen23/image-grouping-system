"""Face routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.database import get_db
from app.models import Face
from app.schemas.face import FaceResponse

router = APIRouter(prefix="/api/faces", tags=["faces"])


@router.get("", response_model=List[FaceResponse])
def list_faces(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all faces."""
    faces = db.query(Face).offset(skip).limit(limit).all()
    return faces


@router.get("/{face_id}", response_model=FaceResponse)
def get_face(
    face_id: UUID,
    db: Session = Depends(get_db)
):
    """Get face details."""
    face = db.query(Face).filter(Face.id == face_id).first()
    if not face:
        raise HTTPException(status_code=404, detail="Face not found")
    return face
