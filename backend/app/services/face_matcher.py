"""Face matching service using cosine similarity with pgvector."""
import numpy as np
from typing import Optional, Tuple
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import PersonGroup, Face
from app.config import settings


class FaceMatcher:
    """Service for matching faces to person groups using cosine similarity."""
    
    def __init__(self, db: Session):
        """Initialize face matcher with database session."""
        self.db = db
        self.threshold = settings.FACE_SIMILARITY_THRESHOLD
    
    def find_matching_group(
        self, 
        embedding: np.ndarray, 
        threshold: Optional[float] = None
    ) -> Optional[Tuple[UUID, float]]:
        """
        Find matching person group for a face embedding.
        
        Args:
            embedding: Face embedding vector (512-dim, normalized)
            threshold: Similarity threshold (defaults to config value)
        
        Returns:
            Tuple of (person_group_id, similarity_score) if match found, else None
        """
        if threshold is None:
            threshold = self.threshold
        
        # Normalize embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding_norm = embedding / norm
        else:
            return None
        
        # Convert to list for pgvector
        embedding_list = embedding_norm.tolist()
        
        # Query using pgvector cosine distance (<=> operator)
        # Cosine distance = 1 - cosine similarity
        # We want similarity > threshold, so distance < (1 - threshold)
        query = text("""
            SELECT pg.id, 
                   1 - (f.embedding <=> :embedding::vector) as similarity
            FROM person_groups pg
            JOIN faces f ON f.id = pg.representative_face_id
            WHERE 1 - (f.embedding <=> :embedding::vector) > :threshold
            ORDER BY f.embedding <=> :embedding::vector
            LIMIT 1
        """)
        
        result = self.db.execute(
            query,
            {
                "embedding": embedding_list,
                "threshold": threshold
            }
        )
        row = result.first()
        
        if row:
            return (row.id, float(row.similarity))
        return None
    
    def find_matching_group_from_faces(
        self,
        embedding: np.ndarray,
        threshold: Optional[float] = None
    ) -> Optional[Tuple[UUID, float]]:
        """
        Find matching person group by comparing against all faces in groups.
        This is an alternative approach that compares against all faces, not just representative ones.
        
        Args:
            embedding: Face embedding vector (512-dim, normalized)
            threshold: Similarity threshold
        
        Returns:
            Tuple of (person_group_id, similarity_score) if match found, else None
        """
        if threshold is None:
            threshold = self.threshold
        
        # Normalize embedding
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding_norm = embedding / norm
        else:
            return None
        
        embedding_list = embedding_norm.tolist()
        
        # Query comparing against all faces with person_group_id
        query = text("""
            SELECT DISTINCT ON (f.person_group_id) 
                   f.person_group_id,
                   1 - (f.embedding <=> :embedding::vector) as similarity
            FROM faces f
            WHERE f.person_group_id IS NOT NULL
              AND 1 - (f.embedding <=> :embedding::vector) > :threshold
            ORDER BY f.person_group_id, f.embedding <=> :embedding::vector
            LIMIT 1
        """)
        
        result = self.db.execute(
            query,
            {
                "embedding": embedding_list,
                "threshold": threshold
            }
        )
        row = result.first()
        
        if row:
            return (row.person_group_id, float(row.similarity))
        return None
