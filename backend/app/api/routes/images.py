"""Image routes."""
from fastapi import APIRouter, Depends, HTTPException, Response, BackgroundTasks
from sqlalchemy.orm import Session
from uuid import UUID
from typing import List
from app.database import get_db
from app.models import Image, Face
from app.schemas.image import ImageResponse
from app.services.storage import storage_service
from app.workers.face_processor import process_image_sync

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


@router.get("/{image_id}/detection-debug")
def get_detection_debug(
    image_id: UUID,
    db: Session = Depends(get_db)
):
    """Get detailed face detection debugging information for an image."""
    import logging
    import traceback
    logger = logging.getLogger(__name__)
    
    # Default error response
    error_response = {
        "image_id": str(image_id),
        "error": "Unknown error",
        "error_type": "Unknown",
        "detection_results": {"faces_detected": 0, "detections": []},
        "message": "Face detection test failed. Check backend logs for details."
    }
    
    try:
        from app.services.image_processor import image_processor
        from app.services.face_detector import get_face_detector
    except Exception as e:
        logger.error(f"Failed to import required modules: {e}", exc_info=True)
        error_response.update({
            "error": f"Failed to import modules: {str(e)}",
            "error_type": type(e).__name__,
            "traceback": traceback.format_exc()
        })
        return error_response
    
    try:
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            return {
                "error": "Image not found",
                "image_id": str(image_id),
                "detection_results": {"faces_detected": 0, "detections": []}
            }
        
        logger.info(f"Starting detection debug for image {image_id}")
        
        # Load image from storage
        try:
            image_data = storage_service.get_object(image.storage_key)
            logger.info(f"Loaded image data: {len(image_data)} bytes")
        except Exception as e:
            logger.error(f"Failed to load image from storage: {e}")
            return {
                "image_id": str(image_id),
                "filename": image.filename,
                "error": f"Failed to load image from storage: {str(e)}",
                "error_type": type(e).__name__,
                "detection_results": {"faces_detected": 0, "detections": []}
            }
        
        # Convert HEIC if needed
        if image_processor.is_heic_format(image.mime_type or ""):
            try:
                image_data = image_processor.convert_heic_to_jpeg(image_data)
                logger.info("Converted HEIC to JPEG")
            except Exception as e:
                logger.error(f"Failed to convert HEIC: {e}")
                return {
                    "image_id": str(image_id),
                    "filename": image.filename,
                    "error": f"Failed to convert HEIC: {str(e)}",
                    "error_type": type(e).__name__,
                    "detection_results": {"faces_detected": 0, "detections": []}
                }
        
        # Load image as numpy array
        try:
            image_array = image_processor.load_image_from_bytes(image_data)
            image_array = image_processor.resize_image(image_array, max_size=1920)
            logger.info(f"Image array loaded: shape={image_array.shape}, dtype={image_array.dtype}")
        except Exception as e:
            logger.error(f"Failed to load image array: {e}")
            return {
                "image_id": str(image_id),
                "filename": image.filename,
                "error": f"Failed to load image array: {str(e)}",
                "error_type": type(e).__name__,
                "detection_results": {"faces_detected": 0, "detections": []}
            }
        
        # Get face detector
        try:
            face_detector = get_face_detector()
            logger.info("Face detector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize face detector: {e}")
            return {
                "image_id": str(image_id),
                "filename": image.filename,
                "error": f"Failed to initialize face detector: {str(e)}",
                "error_type": type(e).__name__,
                "detection_results": {"faces_detected": 0, "detections": []}
            }
        
        # Try detection
        try:
            face_detections = face_detector.detect_faces(image_array)
            logger.info(f"Face detection completed: {len(face_detections)} faces detected")
        except Exception as e:
            logger.error(f"Face detection failed: {e}", exc_info=True)
            return {
                "image_id": str(image_id),
                "filename": image.filename,
                "error": f"Face detection failed: {str(e)}",
                "error_type": type(e).__name__,
                "traceback": traceback.format_exc(),
                "detection_results": {"faces_detected": 0, "detections": []}
            }
        
        # Ensure all data is JSON serializable
        detections_list = []
        for det in face_detections:
            # Convert bbox tuple to list and ensure all values are native Python types
            bbox_list = [int(x) for x in det.bbox]
            detections_list.append({
                "confidence": float(det.confidence),
                "bbox": bbox_list,
                "bbox_size": f"{bbox_list[2]}x{bbox_list[3]}"
            })
        
        return {
            "image_id": str(image_id),
            "filename": image.filename,
            "image_info": {
                "width": int(image.width) if image.width else None,
                "height": int(image.height) if image.height else None,
                "mime_type": image.mime_type,
                "file_size": int(image.file_size) if image.file_size else None,
                "array_shape": [int(x) for x in image_array.shape],
                "array_dtype": str(image_array.dtype),
            },
            "detection_results": {
                "faces_detected": len(face_detections),
                "detections": detections_list
            },
            "message": "Face detection test completed. Check backend logs for detailed information."
        }
    except HTTPException:
        # Re-raise HTTP exceptions (like 404)
        raise
    except Exception as e:
        error_trace = traceback.format_exc()
        logger.error(f"Detection debug failed for image {image_id}: {e}", exc_info=True)
        
        # Return error details but don't raise HTTPException to avoid 500
        try:
            image = db.query(Image).filter(Image.id == image_id).first()
            filename = image.filename if image else "unknown"
        except:
            filename = "unknown"
        
        return {
            "image_id": str(image_id),
            "filename": filename,
            "error": str(e),
            "error_type": type(e).__name__,
            "traceback": error_trace,
            "message": "Face detection test failed. Check error details and backend logs.",
            "detection_results": {
                "faces_detected": 0,
                "detections": []
            }
        }


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
    """Retry processing for an image (works for any status: pending, failed, or completed)."""
    import logging
    logger = logging.getLogger(__name__)
    
    image = db.query(Image).filter(Image.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Delete existing faces and assignments for this image before reprocessing
    from app.models import Face, FaceGroupAssignment
    existing_faces = db.query(Face).filter(Face.image_id == image_id).all()
    face_ids = [face.id for face in existing_faces]
    
    # Delete assignments first (cascade should handle this, but being explicit)
    if face_ids:
        db.query(FaceGroupAssignment).filter(
            FaceGroupAssignment.face_id.in_(face_ids)
        ).delete(synchronize_session=False)
    
    # Delete faces (cascade will handle assignments, but we already deleted them)
    for face in existing_faces:
        db.delete(face)
    
    # Reset status to pending
    image.processing_status = "pending"
    image.processed_at = None
    db.commit()
    logger.info(f"Reset image {image_id} to pending status and deleted {len(existing_faces)} existing faces")
    
    # Trigger background processing (use sync wrapper for BackgroundTasks)
    background_tasks.add_task(process_image_sync, image_id)
    logger.info(f"Added background task to process image {image_id}")
    
    return {"message": "Processing retried - face detection will be redone", "image_id": str(image_id)}


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
