"""Person group routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from pydantic import BaseModel
import logging
from app.database import get_db
from app.models import PersonGroup, Face, Image
from app.schemas.person_group import PersonGroupResponse
from app.services.group_manager import GroupManager

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/groups", tags=["groups"])


class MergeGroupsRequest(BaseModel):
    """Request schema for merging groups."""
    target_group_id: UUID


@router.get("", response_model=List[PersonGroupResponse])
def list_groups(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all person groups."""
    # Get total count for logging
    total_count = db.query(PersonGroup).count()
    logger.info(f"Listing person groups: total={total_count}, skip={skip}, limit={limit}")
    
    groups = db.query(PersonGroup).offset(skip).limit(limit).all()
    logger.info(f"Returning {len(groups)} person groups")
    
    return groups


@router.get("/{group_id}", response_model=PersonGroupResponse)
def get_group(
    group_id: UUID,
    db: Session = Depends(get_db)
):
    """Get person group details."""
    group = db.query(PersonGroup).filter(PersonGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    return group


@router.get("/{group_id}/faces", response_model=List[dict])
def get_group_faces(
    group_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all faces in a person group."""
    group = db.query(PersonGroup).filter(PersonGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_manager = GroupManager(db)
    faces = group_manager.get_group_faces(group_id)
    
    return [
        {
            "id": str(face.id),
            "image_id": str(face.image_id),
            "bounding_box": face.bounding_box,
            "confidence": face.confidence,
            "detected_at": face.detected_at.isoformat() if face.detected_at else None
        }
        for face in faces
    ]


@router.get("/{group_id}/images", response_model=List[dict])
def get_group_images(
    group_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all images containing faces from a person group."""
    group = db.query(PersonGroup).filter(PersonGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_manager = GroupManager(db)
    images = group_manager.get_group_images(group_id)
    
    return [
        {
            "id": str(image.id),
            "filename": image.filename,
            "storage_url": image.storage_url,
            "uploaded_at": image.uploaded_at.isoformat() if image.uploaded_at else None
        }
        for image in images
    ]


@router.post("/{group_id}/merge")
def merge_groups(
    group_id: UUID,
    request: MergeGroupsRequest,
    db: Session = Depends(get_db)
):
    """Merge two person groups."""
    source_group = db.query(PersonGroup).filter(PersonGroup.id == group_id).first()
    target_group = db.query(PersonGroup).filter(PersonGroup.id == request.target_group_id).first()
    
    if not source_group:
        raise HTTPException(status_code=404, detail="Source group not found")
    if not target_group:
        raise HTTPException(status_code=404, detail="Target group not found")
    
    group_manager = GroupManager(db)
    group_manager.merge_groups(group_id, request.target_group_id)
    db.commit()
    
    return {"message": "Groups merged successfully"}


@router.delete("/{group_id}")
def delete_group(
    group_id: UUID,
    db: Session = Depends(get_db)
):
    """Delete a person group."""
    group = db.query(PersonGroup).filter(PersonGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    group_manager = GroupManager(db)
    group_manager.delete_group(group_id)
    db.commit()
    
    return {"message": "Group deleted successfully"}
