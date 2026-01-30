"""Person group management service."""
from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import distinct
from app.models import PersonGroup, Face, Image, FaceGroupAssignment


class GroupManager:
    """Service for managing person groups."""
    
    def __init__(self, db: Session):
        """Initialize group manager with database session."""
        self.db = db
    
    def create_person_group(
        self, 
        representative_face_id: Optional[UUID] = None,
        name: Optional[str] = None
    ) -> PersonGroup:
        """
        Create a new person group.
        
        Args:
            representative_face_id: Optional face ID to use as representative
            name: Optional name for the group
        
        Returns:
            Created PersonGroup
        """
        person_group = PersonGroup(
            name=name,
            representative_face_id=representative_face_id
        )
        self.db.add(person_group)
        self.db.flush()  # Flush to get the ID
        
        # If no representative face was provided and we have a face_id, set it
        if representative_face_id and not person_group.representative_face_id:
            person_group.representative_face_id = representative_face_id
        
        return person_group
    
    def assign_face_to_group(
        self, 
        face_id: UUID, 
        person_group_id: UUID, 
        similarity: float
    ) -> FaceGroupAssignment:
        """
        Assign a face to a person group.
        
        Args:
            face_id: Face ID to assign
            person_group_id: Person group ID
            similarity: Similarity score at assignment time
        
        Returns:
            FaceGroupAssignment
        """
        # Check if assignment already exists
        existing = self.db.query(FaceGroupAssignment).filter(
            FaceGroupAssignment.face_id == face_id,
            FaceGroupAssignment.person_group_id == person_group_id
        ).first()
        
        if existing:
            existing.similarity_score = similarity
            return existing
        
        # Create new assignment
        assignment = FaceGroupAssignment(
            face_id=face_id,
            person_group_id=person_group_id,
            similarity_score=similarity
        )
        self.db.add(assignment)
        
        # Update face's person_group_id
        face = self.db.query(Face).filter(Face.id == face_id).first()
        if face:
            face.person_group_id = person_group_id
        
        return assignment
    
    def get_group_faces(self, person_group_id: UUID) -> List[Face]:
        """Get all faces in a person group."""
        return self.db.query(Face).filter(
            Face.person_group_id == person_group_id
        ).all()
    
    def get_group_images(self, person_group_id: UUID) -> List[Image]:
        """Get all images containing faces from a person group."""
        # Get distinct images that have faces in this group
        images = self.db.query(Image).join(Face).filter(
            Face.person_group_id == person_group_id
        ).distinct().all()
        return images
    
    def update_group_representative(self, person_group_id: UUID, face_id: UUID):
        """Update the representative face for a group."""
        group = self.db.query(PersonGroup).filter(
            PersonGroup.id == person_group_id
        ).first()
        if group:
            group.representative_face_id = face_id
    
    def merge_groups(self, source_group_id: UUID, target_group_id: UUID):
        """
        Merge two person groups.
        
        Args:
            source_group_id: Group to merge from (will be deleted)
            target_group_id: Group to merge into
        """
        # Update all faces from source group to target group
        self.db.query(Face).filter(
            Face.person_group_id == source_group_id
        ).update({"person_group_id": target_group_id})
        
        # Update all assignments
        self.db.query(FaceGroupAssignment).filter(
            FaceGroupAssignment.person_group_id == source_group_id
        ).update({"person_group_id": target_group_id})
        
        # Delete source group
        self.db.query(PersonGroup).filter(
            PersonGroup.id == source_group_id
        ).delete()
    
    def delete_group(self, person_group_id: UUID):
        """Delete a person group (faces will have person_group_id set to NULL)."""
        # Update faces to remove group assignment
        self.db.query(Face).filter(
            Face.person_group_id == person_group_id
        ).update({"person_group_id": None})
        
        # Delete assignments
        self.db.query(FaceGroupAssignment).filter(
            FaceGroupAssignment.person_group_id == person_group_id
        ).delete()
        
        # Delete group
        self.db.query(PersonGroup).filter(
            PersonGroup.id == person_group_id
        ).delete()
