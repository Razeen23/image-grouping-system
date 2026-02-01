"""Processing routes."""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from app.database import get_db
from app.models import Image
from app.workers.face_processor import process_image_sync

router = APIRouter(prefix="/api/process", tags=["processing"])


@router.post("/{image_id}")
async def trigger_processing(
    image_id: UUID,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Trigger face processing for an image."""
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Add background task
    background_tasks.add_task(process_image_sync, image_id)
    
    return {"message": "Processing started", "image_id": str(image_id)}


@router.get("/status")
def get_processing_status(
    db: Session = Depends(get_db)
):
    """Get processing queue status."""
    pending = db.query(Image).filter(Image.processing_status == "pending").count()
    processing = db.query(Image).filter(Image.processing_status == "processing").count()
    completed = db.query(Image).filter(Image.processing_status == "completed").count()
    failed = db.query(Image).filter(Image.processing_status == "failed").count()
    
    return {
        "pending": pending,
        "processing": processing,
        "completed": completed,
        "failed": failed,
        "total": pending + processing + completed + failed
    }
