"""Image preprocessing service."""
import cv2
import numpy as np
from PIL import Image as PILImage
from io import BytesIO
from typing import Tuple, Optional


class ImageProcessor:
    """Service for image preprocessing."""
    
    @staticmethod
    def load_image_from_bytes(image_data: bytes) -> np.ndarray:
        """Load image from bytes to numpy array."""
        nparr = np.frombuffer(image_data, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError("Failed to decode image")
        return image
    
    @staticmethod
    def get_image_dimensions(image: np.ndarray) -> Tuple[int, int]:
        """Get image dimensions (width, height)."""
        height, width = image.shape[:2]
        return width, height
    
    @staticmethod
    def resize_image(image: np.ndarray, max_size: int = 1920) -> np.ndarray:
        """
        Resize image while maintaining aspect ratio.
        
        Args:
            image: Input image as numpy array
            max_size: Maximum dimension (width or height)
        
        Returns:
            Resized image
        """
        height, width = image.shape[:2]
        
        if max(height, width) <= max_size:
            return image
        
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))
        
        return cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
    
    @staticmethod
    def convert_heic_to_jpeg(heic_data: bytes) -> bytes:
        """Convert HEIC image to JPEG bytes."""
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()
        except ImportError:
            raise ValueError("pillow-heif not installed. Install with: pip install pillow-heif")
        
        image = PILImage.open(BytesIO(heic_data))
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        
        output = BytesIO()
        image.save(output, format='JPEG', quality=95)
        return output.getvalue()
    
    @staticmethod
    def is_heic_format(mime_type: str) -> bool:
        """Check if image is HEIC format."""
        return mime_type in ['image/heic', 'image/heif']


# Singleton instance
image_processor = ImageProcessor()
