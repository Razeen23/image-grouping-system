"""Upload route for image uploads."""
from fastapi import APIRouter, UploadFile, File, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from uuid import uuid4
from datetime import datetime
from app.database import get_db
from app.models import Image
from app.schemas.upload import UploadResponse
from app.services.storage import storage_service
from app.services.image_processor import image_processor
from app.workers.face_processor import process_image
from app.config import settings

router = APIRouter(prefix="/api/upload", tags=["upload"])


@router.post("", response_model=List[UploadResponse])
async def upload_images(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db)
):
    """
    Upload one or more images.
    
    Images are uploaded to object storage and processing is triggered in background.
    """
    responses = []
    
    for file in files:
        try:
            # Read file data
            file_data = await file.read()
            filename = file.filename or f"image_{uuid4()}"
            content_type = file.content_type or "image/jpeg"
            
            # Convert HEIC if needed
            if image_processor.is_heic_format(content_type):
                file_data = image_processor.convert_heic_to_jpeg(file_data)
                content_type = "image/jpeg"
                # Update filename extension
                if filename.lower().endswith(('.heic', '.heif')):
                    filename = filename.rsplit('.', 1)[0] + '.jpg'
            
            # Upload to object storage
            storage_key, storage_url = storage_service.upload_file(
                file_data, filename, content_type
            )
            
            # Get image dimensions
            image_array = image_processor.load_image_from_bytes(file_data)
            width, height = image_processor.get_image_dimensions(image_array)
            
            # Create image record
            image = Image(
                filename=filename,
                storage_key=storage_key,
                storage_url=storage_url,
                mime_type=content_type,
                file_size=len(file_data),
                width=width,
                height=height,
                processing_status="pending"
            )
            db.add(image)
            db.commit()
            db.refresh(image)
            
            # Trigger background processing if enabled
            if settings.ENABLE_AUTO_PROCESSING and background_tasks:
                background_tasks.add_task(process_image, image.id)
            
            responses.append(UploadResponse(
                image_id=image.id,
                filename=filename,
                message="Image uploaded successfully"
            ))
            
        except Exception as e:
            # Log error but continue with other files
            responses.append(UploadResponse(
                image_id=uuid4(),  # Dummy ID
                filename=file.filename or "unknown",
                message=f"Upload failed: {str(e)}"
            ))
    
    return responses
