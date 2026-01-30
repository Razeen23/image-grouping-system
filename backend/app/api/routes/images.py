"""Image routes."""
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.database import get_db
from app.models import Image, Face
from app.schemas.image import ImageResponse
from app.services.storage import storage_service
from app.workers.face_processor import process_image

router = APIRouter(prefix="/api/images", tags=["images"])


@router.get("", response_model=List[ImageResponse])
def list_images(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all images."""
    images = db.query(Image).offset(skip).limit(limit).all()
    return images


@router.get("/{image_id}", response_model=ImageResponse)
def get_image(
    image_id: UUID,
    db: Session = Depends(get_db)
):
    """Get image details."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    return image


@router.get("/{image_id}/file")
def get_image_file(
    image_id: UUID,
    db: Session = Depends(get_db)
):
    """Get image file from storage."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    try:
        image_data = storage_service.get_object(image.storage_key)
        return Response(
            content=image_data,
            media_type=image.mime_type or "image/jpeg"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve image: {str(e)}")


@router.get("/{image_id}/faces", response_model=List[dict])
def get_image_faces(
    image_id: UUID,
    db: Session = Depends(get_db)
):
    """Get all faces detected in an image."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    faces = db.query(Face).filter(Face.image_id == image_id).all()
    return [
        {
            "id": str(face.id),
            "bounding_box": face.bounding_box,
            "confidence": face.confidence,
            "person_group_id": str(face.person_group_id) if face.person_group_id else None,
            "detected_at": face.detected_at.isoformat() if face.detected_at else None
        }
        for face in faces
    ]


@router.post("/{image_id}/retry")
async def retry_processing(
    image_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Retry processing for a failed or pending image."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Reset status to pending
    image.processing_status = "pending"
    db.commit()
    
    # Trigger background processing
    background_tasks.add_task(process_image, image_id)
    
    return {"message": "Processing retried", "image_id": str(image_id)}


@router.get("/diagnostics/stats")
def get_diagnostics(
    db: Session = Depends(get_db)
):
    """Get diagnostic information about images, faces, and groups."""
    from app.models import PersonGroup
    
    total_images = db.query(Image).count()
    completed_images = db.query(Image).filter(Image.processing_status == "completed").count()
    pending_images = db.query(Image).filter(Image.processing_status == "pending").count()
    processing_images = db.query(Image).filter(Image.processing_status == "processing").count()
    failed_images = db.query(Image).filter(Image.processing_status == "failed").count()
    
    total_faces = db.query(Face).count()
    faces_with_groups = db.query(Face).filter(Face.person_group_id.isnot(None)).count()
    
    total_groups = db.query(PersonGroup).count()
    
    # Get images with faces but no groups
    images_with_faces_no_groups = db.query(Image).join(Face).filter(
        Face.person_group_id.is_(None)
    ).distinct().count()
    
    # Get completed images with no faces detected
    completed_with_no_faces = db.query(Image).filter(
        Image.processing_status == "completed"
    ).outerjoin(Face).filter(Face.id.is_(None)).count()
    
    # Get sample of completed images to check face counts
    sample_completed = db.query(Image).filter(
        Image.processing_status == "completed"
    ).limit(5).all()
    
    sample_info = []
    for img in sample_completed:
        face_count = db.query(Face).filter(Face.image_id == img.id).count()
        sample_info.append({
            "image_id": str(img.id),
            "filename": img.filename,
            "faces_detected": face_count
        })
    
    return {
        "images": {
            "total": total_images,
            "completed": completed_images,
            "pending": pending_images,
            "processing": processing_images,
            "failed": failed_images,
            "completed_with_no_faces": completed_with_no_faces
        },
        "faces": {
            "total": total_faces,
            "with_groups": faces_with_groups,
            "without_groups": total_faces - faces_with_groups
        },
        "person_groups": {
            "total": total_groups
        },
        "issues": {
            "images_with_faces_but_no_groups": images_with_faces_no_groups,
            "completed_images_with_no_faces": completed_with_no_faces
        },
        "sample_completed_images": sample_info,
        "diagnosis": {
            "no_groups_reason": "No faces detected in images" if total_faces == 0 and completed_images > 0 else 
                               "Faces detected but groups not created" if total_faces > 0 and total_groups == 0 else
                               "Everything looks normal" if total_groups > 0 else
                               "No images processed yet"
        }
    }
