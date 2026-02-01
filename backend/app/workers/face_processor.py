"""Background worker for processing images and detecting faces."""
from uuid import UUID
import logging
from datetime import datetime
from app.database import SessionLocal
from app.models import Image, Face, FaceGroupAssignment
from app.services.storage import storage_service
from app.services.image_processor import image_processor
from app.services.face_detector import get_face_detector
from app.services.face_matcher import FaceMatcher
from app.services.group_manager import GroupManager
import numpy as np

logger = logging.getLogger(__name__)


def process_image_sync(image_id: UUID) -> dict:
    """
    Process an image: detect faces, extract embeddings, and assign to groups.
    This is the main entry point used by FastAPI BackgroundTasks.
    
    Args:
        image_id: Image ID to process
    
    Returns:
        Dictionary with processing results
    """
    # Since all operations are synchronous, we don't need async
    return _process_image_internal(image_id)


def _process_image_internal(image_id: UUID) -> dict:
    """
    Process an image: detect faces, extract embeddings, and assign to groups.
    
    Args:
        image_id: Image ID to process
    
    Returns:
        Dictionary with processing results
    """
    # Create new database session for background task
    db = SessionLocal()
    image = None
    try:
        logger.info(f"🚀 Starting processing for image {image_id}")
        
        # Get image
        image = db.query(Image).filter(Image.id == image_id).first()
        if not image:
            raise ValueError(f"Image {image_id} not found")
        
        # Update status
        image.processing_status = "processing"
        db.commit()
        logger.info(f"Image {image_id} status set to processing")
        
        # Initialize services
        try:
            face_detector = get_face_detector()
            logger.info(f"Face detector initialized for image {image_id}")
        except Exception as e:
            logger.error(f"Failed to initialize face detector for image {image_id}: {e}")
            raise
        
        face_matcher = FaceMatcher(db)
        group_manager = GroupManager(db)
        
        # Load image from object storage
        try:
            logger.info(f"Loading image {image_id} from storage (key: {image.storage_key})")
            image_data = storage_service.get_object(image.storage_key)
            logger.info(f"Image {image_id} loaded, size: {len(image_data)} bytes")
        except Exception as e:
            logger.error(f"Failed to load image {image_id} from storage: {e}")
            raise
        
        # Convert HEIC if needed
        if image_processor.is_heic_format(image.mime_type or ""):
            try:
                logger.info(f"Converting HEIC image {image_id} to JPEG")
                image_data = image_processor.convert_heic_to_jpeg(image_data)
            except Exception as e:
                logger.error(f"Failed to convert HEIC image {image_id}: {e}")
                raise
        
        # Load image as numpy array
        try:
            image_array = image_processor.load_image_from_bytes(image_data)
            logger.info(f"Image {image_id} loaded as numpy array, shape: {image_array.shape}")
        except Exception as e:
            logger.error(f"Failed to load image {image_id} as numpy array: {e}")
            raise
        
        # Resize if too large (for faster processing)
        image_array = image_processor.resize_image(image_array, max_size=1920)
        
        # Update image dimensions if not set
        if not image.width or not image.height:
            width, height = image_processor.get_image_dimensions(image_array)
            image.width = width
            image.height = height
            logger.info(f"Updated image {image_id} dimensions: {width}x{height}")
        
        # Detect all faces
        try:
            logger.info(f"Detecting faces in image {image_id}")
            logger.info(f"Image array info: shape={image_array.shape}, dtype={image_array.dtype}, min={image_array.min()}, max={image_array.max()}")
            face_detections = face_detector.detect_faces(image_array)
            if len(face_detections) == 0:
                logger.warning(f"❌ No faces detected in image {image_id} (filename: {image.filename})")
                logger.warning(f"   Image dimensions: {image.width}x{image.height}")
                logger.warning(f"   Image type: {image.mime_type}")
                logger.warning(f"   This could mean:")
                logger.warning(f"   - Face is occluded (sunglasses, mask, etc.)")
                logger.warning(f"   - Face is too small or at extreme angle")
                logger.warning(f"   - Detection threshold is too high")
                logger.warning(f"   - Image quality issues")
            else:
                logger.info(f"✅ Detected {len(face_detections)} faces in image {image_id}")
                for idx, det in enumerate(face_detections):
                    logger.info(f"   Face {idx + 1}: confidence={det.confidence:.4f}, bbox={det.bbox}")
        except Exception as e:
            logger.error(f"Face detection failed for image {image_id}: {e}", exc_info=True)
            raise
        
        results = {
            "faces_detected": len(face_detections),
            "groups_matched": [],
            "groups_created": []
        }
        
        # Process each face
        faces_processed = 0
        faces_skipped = 0
        for idx, detection in enumerate(face_detections):
            try:
                logger.info(f"Processing face {idx + 1}/{len(face_detections)} in image {image_id}")
                logger.info(f"  Face bbox: {detection.bbox}, confidence: {detection.confidence}")
                
                # Check if face_object is available
                face_object = getattr(detection, 'face_object', None)
                if face_object is not None:
                    logger.info(f"  Face object available, will use pre-computed embedding")
                else:
                    logger.warning(f"  Face object not available, will use fallback extraction from cropped image")
                
                # Extract embedding (use face_object if available, otherwise fallback to cropped image)
                try:
                    embedding = face_detector.extract_embedding(
                        face_image=detection.cropped_image,
                        face_object=face_object
                    )
                    logger.info(f"✅ Extracted embedding for face {idx + 1} in image {image_id}, shape: {embedding.shape}")
                except Exception as e:
                    logger.error(f"❌ Failed to extract embedding for face {idx + 1} in image {image_id}: {e}", exc_info=True)
                    logger.error(f"   Error type: {type(e).__name__}")
                    logger.error(f"   Cropped image shape: {detection.cropped_image.shape if hasattr(detection, 'cropped_image') else 'N/A'}")
                    faces_skipped += 1
                    continue  # Skip this face but continue with others
                
                # Find matching group
                try:
                    match = face_matcher.find_matching_group(embedding)
                except Exception as e:
                    logger.warning(f"Failed to find matching group for face {idx + 1} in image {image_id}: {e}")
                    match = None
                
                person_group_id = None
                similarity = 1.0
                
                if match:
                    person_group_id, similarity = match
                    results["groups_matched"].append(str(person_group_id))
                    logger.info(f"Face {idx + 1} in image {image_id} matched to group {person_group_id} (similarity: {similarity:.3f})")
                else:
                    # Create new group
                    try:
                        person_group = group_manager.create_person_group()
                        person_group_id = person_group.id
                        results["groups_created"].append(str(person_group_id))
                        logger.info(f"Created new group {person_group_id} for face {idx + 1} in image {image_id}")
                    except Exception as e:
                        logger.error(f"Failed to create group for face {idx + 1} in image {image_id}: {e}")
                        raise
                
                # Save face record
                try:
                    face_record = Face(
                        image_id=image_id,
                        embedding=embedding.tolist(),  # Convert numpy array to list for pgvector
                        bounding_box={
                            "x": int(detection.bbox[0]),
                            "y": int(detection.bbox[1]),
                            "width": int(detection.bbox[2]),
                            "height": int(detection.bbox[3])
                        },
                        confidence=float(detection.confidence),
                        person_group_id=person_group_id
                    )
                    db.add(face_record)
                    db.flush()  # Flush to get face ID
                    logger.info(f"✅ Created face record {face_record.id} for face {idx + 1} in image {image_id}")
                    faces_processed += 1
                except Exception as e:
                    logger.error(f"❌ Failed to save face record for face {idx + 1} in image {image_id}: {e}", exc_info=True)
                    raise
                
                # If this is a new group, set this face as representative
                if person_group_id:
                    # Check if this group was just created in this processing run
                    group_was_created = any(
                        str(person_group_id) == created_id 
                        for created_id in results["groups_created"]
                    )
                    if group_was_created:
                        try:
                            group_manager.update_group_representative(person_group_id, face_record.id)
                            logger.debug(f"Set face {face_record.id} as representative for group {person_group_id}")
                        except Exception as e:
                            logger.warning(f"Failed to set representative for group {person_group_id}: {e}")
                
                # Create assignment
                try:
                    assignment = FaceGroupAssignment(
                        face_id=face_record.id,
                        person_group_id=person_group_id,
                        similarity_score=similarity
                    )
                    db.add(assignment)
                except Exception as e:
                    logger.warning(f"Failed to create assignment for face {face_record.id}: {e}")
            except Exception as e:
                # Catch any unexpected errors during face processing
                logger.error(f"Unexpected error processing face {idx + 1} in image {image_id}: {e}", exc_info=True)
                # Continue with next face
                continue
        
        # Log processing summary
        logger.info(f"Face processing summary for image {image_id}:")
        logger.info(f"  Total faces detected: {len(face_detections)}")
        logger.info(f"  Faces successfully processed: {faces_processed}")
        logger.info(f"  Faces skipped (embedding failed): {faces_skipped}")
        
        if faces_processed == 0 and len(face_detections) > 0:
            logger.error(f"⚠️ WARNING: {len(face_detections)} faces detected but NONE were processed successfully!")
            logger.error(f"   All faces failed during embedding extraction. Check logs above for details.")
        
        # Ensure all pending changes are flushed before final commit
        try:
            db.flush()
            logger.info(f"Flushed database changes for image {image_id}")
        except Exception as e:
            logger.error(f"Failed to flush database changes for image {image_id}: {e}")
            raise
        
        # Update image status
        image.processed_at = datetime.utcnow()
        image.processing_status = "completed"
        
        # Final commit - this commits all changes (person groups, faces, assignments)
        try:
            db.commit()
            logger.info(f"Committed database changes for image {image_id}")
            logger.info(f"Successfully processed image {image_id}: {results['faces_detected']} faces detected, {faces_processed} faces saved, {len(results['groups_matched'])} matched, {len(results['groups_created'])} created")
            if results['groups_created']:
                logger.info(f"Created person groups for image {image_id}: {', '.join(results['groups_created'])}")
            if results['groups_matched']:
                logger.info(f"Matched to existing groups for image {image_id}: {', '.join(results['groups_matched'])}")
        except Exception as e:
            logger.error(f"Failed to commit database changes for image {image_id}: {e}", exc_info=True)
            db.rollback()
            raise
        
        return results
        
    except Exception as e:
        # Update status to failed
        logger.error(f"Processing failed for image {image_id}: {e}", exc_info=True)
        if image:
            try:
                image.processing_status = "failed"
                db.commit()
            except Exception as commit_error:
                logger.error(f"Failed to update status to failed for image {image_id}: {commit_error}")
        raise e
    finally:
        db.close()
        logger.debug(f"Closed database session for image {image_id}")


# Alias for backward compatibility
process_image = process_image_sync
process_image_async = process_image_sync  # Keep for any existing references
