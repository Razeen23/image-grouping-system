"""Face detection and embedding service using InsightFace."""
import cv2
import numpy as np
from typing import List, Tuple, Optional, Any
from dataclasses import dataclass
from app.config import settings


@dataclass
class FaceDetection:
    """Face detection result."""
    bbox: Tuple[int, int, int, int]  # (x, y, width, height)
    confidence: float
    cropped_image: np.ndarray
    landmarks: Optional[np.ndarray] = None
    face_object: Optional[Any] = None  # Store the original InsightFace face object for embedding extraction


class FaceDetector:
    """Service for face detection and embedding extraction using InsightFace."""
    
    def __init__(self):
        """Initialize InsightFace model."""
        try:
            import insightface
            import logging
            logger = logging.getLogger(__name__)
            
            self.model = insightface.app.FaceAnalysis(
                name=settings.INSIGHTFACE_MODEL_PATH,
                providers=['CPUExecutionProvider']  # Use GPU if available: ['CUDAExecutionProvider', 'CPUExecutionProvider']
            )
            # Try to set lower detection threshold and larger detection size for better detection
            # Larger det_size helps with smaller or occluded faces
            # Lower threshold helps with faces that have sunglasses or partial occlusions
            try:
                # Try with very low threshold (0.2) for difficult cases like sunglasses
                # Some InsightFace versions support det_thresh parameter
                self.model.prepare(ctx_id=0, det_size=(832, 832), det_thresh=0.2)
                logger.info("Face detector initialized with det_size=(832,832) and det_thresh=0.2 (very sensitive)")
            except TypeError:
                # If det_thresh parameter not supported, try setting it on the detector model
                try:
                    # Some versions require setting threshold on the detector directly
                    if hasattr(self.model, 'det_model') and hasattr(self.model.det_model, 'threshold'):
                        self.model.det_model.threshold = 0.2
                        logger.info("Set detection threshold to 0.2 on det_model")
                    self.model.prepare(ctx_id=0, det_size=(832, 832))
                    logger.info("Face detector initialized with det_size=(832,832) - threshold may be set separately")
                except Exception as e2:
                    logger.warning(f"Could not set threshold separately: {e2}")
                    self.model.prepare(ctx_id=0, det_size=(832, 832))
                    logger.info("Face detector initialized with det_size=(832,832) - using default threshold")
            except Exception as e:
                # Fallback to default if anything else fails
                logger.warning(f"Could not set custom detection parameters: {e}, using defaults")
                self.model.prepare(ctx_id=0, det_size=(640, 640))
        except ImportError:
            raise ImportError("insightface not installed. Install with: pip install insightface")
        except Exception as e:
            raise Exception(f"Failed to initialize InsightFace model: {e}")
    
    def detect_faces(self, image: np.ndarray) -> List[FaceDetection]:
        """
        Detect all faces in an image.
        
        Args:
            image: Input image as numpy array (BGR format)
        
        Returns:
            List of FaceDetection objects
        """
        # Convert BGR to RGB if needed (InsightFace expects RGB)
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        # Detect faces
        import logging
        logger = logging.getLogger(__name__)
        
        logger.info(f"Running face detection on image: shape={image_rgb.shape}, dtype={image_rgb.dtype}")
        faces = self.model.get(image_rgb)
        
        # Log detection results for debugging
        logger.info(f"InsightFace detected {len(faces)} raw face detections")
        
        if len(faces) == 0:
            logger.warning("No faces detected by InsightFace model. This could be due to:")
            logger.warning("  - Face not clearly visible")
            logger.warning("  - Face occluded (sunglasses, mask, etc.)")
            logger.warning("  - Face too small or at extreme angle")
            logger.warning("  - Image quality issues")
            logger.warning(f"  - Detection threshold too high (current: det_thresh=0.3)")
        
        detections = []
        for idx, face in enumerate(faces):
            # Log confidence score for debugging
            confidence = getattr(face, 'det_score', None)
            bbox = face.bbox if hasattr(face, 'bbox') else None
            if confidence is not None and bbox is not None:
                logger.info(f"Face {idx + 1}: confidence={confidence:.4f}, bbox={bbox}")
            else:
                logger.warning(f"Face {idx + 1}: missing confidence or bbox attributes")
            # Get bounding box
            bbox = face.bbox.astype(int)
            x1, y1, x2, y2 = bbox
            
            # Ensure coordinates are within image bounds
            height, width = image.shape[:2]
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(width, x2)
            y2 = min(height, y2)
            
            # Calculate width and height
            bbox_width = x2 - x1
            bbox_height = y2 - y1
            
            # Skip if bbox is too small
            if bbox_width < 20 or bbox_height < 20:
                logger.warning(f"Skipping face {idx + 1}: bbox too small ({bbox_width}x{bbox_height}) - minimum is 20x20")
                continue
            
            # Crop face region (with some padding)
            padding = 10
            x1_pad = max(0, x1 - padding)
            y1_pad = max(0, y1 - padding)
            x2_pad = min(width, x2 + padding)
            y2_pad = min(height, y2 + padding)
            
            cropped = image[y1_pad:y2_pad, x1_pad:x2_pad]
            
            # Get landmarks if available
            landmarks = face.landmark_2d_106 if hasattr(face, 'landmark_2d_106') else None
            
            detection = FaceDetection(
                bbox=(x1, y1, bbox_width, bbox_height),
                confidence=face.det_score,
                cropped_image=cropped,
                landmarks=landmarks,
                face_object=face  # Store the original face object for embedding extraction
            )
            detections.append(detection)
            logger.info(f"✅ Added face detection {len(detections)}: confidence={face.det_score:.4f}, size={bbox_width}x{bbox_height}, position=({x1},{y1})")
        
        if len(detections) == 0 and len(faces) > 0:
            logger.warning(f"⚠️ All {len(faces)} detected faces were filtered out (too small or invalid)")
        elif len(detections) == 0:
            logger.warning("⚠️ No face detections returned - InsightFace found 0 faces in the image")
        
        logger.info(f"Returning {len(detections)} face detections after filtering (from {len(faces)} raw detections)")
        return detections
    
    def extract_embedding(self, face_image: np.ndarray = None, face_object: Any = None) -> np.ndarray:
        """
        Extract face embedding from either a face object or cropped face image.
        
        Args:
            face_image: Cropped face image as numpy array (optional if face_object is provided)
            face_object: Original InsightFace face object (preferred, contains embedding already)
        
        Returns:
            512-dimensional embedding vector
        """
        import logging
        logger = logging.getLogger(__name__)
        
        # If we have the original face object, use its embedding directly
        if face_object is not None:
            logger.debug(f"Extracting embedding from face_object (type: {type(face_object).__name__})")
            # Try different attribute names for embedding
            if hasattr(face_object, 'norm_embeddings'):
                logger.debug("Using norm_embeddings attribute")
                embedding = face_object.norm_embeddings
            elif hasattr(face_object, 'embedding_norm'):
                logger.debug("Using embedding_norm attribute")
                embedding = face_object.embedding_norm
            elif hasattr(face_object, 'embedding'):
                logger.debug("Using embedding attribute")
                embedding = face_object.embedding
            else:
                # Log available attributes for debugging
                attrs = [attr for attr in dir(face_object) if not attr.startswith('_')]
                logger.warning(f"Face object has no embedding attribute. Available attributes: {attrs[:10]}...")
                # Fallback to re-detection if embedding not available
                if face_image is None:
                    raise ValueError("Face object has no embedding and face_image not provided")
                logger.info("Falling back to re-detection from cropped image")
                return self._extract_embedding_from_image(face_image)
        elif face_image is not None:
            # Fallback to re-detection if no face object provided
            logger.info("No face_object provided, using re-detection from cropped image")
            return self._extract_embedding_from_image(face_image)
        else:
            raise ValueError("Either face_object or face_image must be provided")
        
        # Ensure it's a numpy array and has correct shape
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)
        
        # Flatten if needed
        if len(embedding.shape) > 1:
            embedding = embedding.flatten()
        
        # Normalize to unit vector (ensure it's normalized)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        else:
            raise ValueError("Embedding has zero norm")
        
        return embedding.astype(np.float32)
    
    def _extract_embedding_from_image(self, face_image: np.ndarray) -> np.ndarray:
        """
        Extract face embedding from cropped face image (fallback method).
        
        Args:
            face_image: Cropped face image as numpy array
        
        Returns:
            512-dimensional embedding vector
        """
        # Convert BGR to RGB if needed
        if len(face_image.shape) == 3 and face_image.shape[2] == 3:
            face_rgb = cv2.cvtColor(face_image, cv2.COLOR_BGR2RGB)
        else:
            face_rgb = face_image
        
        # Get embedding
        faces = self.model.get(face_rgb)
        
        if len(faces) == 0:
            raise ValueError("No face detected in cropped image")
        
        # Get the first (and likely only) face embedding
        face = faces[0]
        
        # Try different attribute names for embedding
        if hasattr(face, 'norm_embeddings'):
            embedding = face.norm_embeddings
        elif hasattr(face, 'embedding_norm'):
            embedding = face.embedding_norm
        elif hasattr(face, 'embedding'):
            embedding = face.embedding
        else:
            raise ValueError("Face object does not have embedding attribute")
        
        # Ensure it's a numpy array and has correct shape
        if not isinstance(embedding, np.ndarray):
            embedding = np.array(embedding)
        
        # Flatten if needed
        if len(embedding.shape) > 1:
            embedding = embedding.flatten()
        
        # Normalize to unit vector (ensure it's normalized)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        else:
            raise ValueError("Embedding has zero norm")
        
        return embedding.astype(np.float32)


# Singleton instance (lazy initialization)
_face_detector: Optional[FaceDetector] = None


def get_face_detector() -> FaceDetector:
    """Get or create face detector instance."""
    global _face_detector
    if _face_detector is None:
        _face_detector = FaceDetector()
    return _face_detector
