"""
Base Repository module with common CRUD operations.

This module provides a BaseRepository class with common database operations
that can be extended by specific model repositories.
"""
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from sqlalchemy.orm import Session

from invoiceagent.db.models import Base

# Define a generic type variable for SQLAlchemy models
T = TypeVar('T', bound=Base)


class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations for all models."""

    def __init__(self, model_class: Type[T]):
        """Initialize with the model class this repository is responsible for.

        Args:
            model_class: The SQLAlchemy model class this repository handles
        """
        self.model_class = model_class

    def get_by_id(self, session: Session, id: int) -> Optional[T]:
        """Retrieve a single entity by its ID.

        Args:
            session: The database session
            id: The entity ID to retrieve

        Returns:
            The entity if found, None otherwise
        """
        return session.query(self.model_class).filter(self.model_class.id == id).first()

    def get_all(self, session: Session) -> List[T]:
        """Retrieve all entities of this type.

        Args:
            session: The database session

        Returns:
            A list of all entities
        """
        return session.query(self.model_class).all()

    def create(self, session: Session, **kwargs) -> T:
        """Create a new entity.

        Args:
            session: The database session
            **kwargs: Entity attributes

        Returns:
            The newly created entity
        """
        entity = self.model_class(**kwargs)
        session.add(entity)
        session.flush()  # Flush to get the ID without committing
        return entity

    def update(self, session: Session, id: int, update_data: Dict[str, Any]) -> Optional[T]:
        """Update an existing entity.

        Args:
            session: The database session
            id: The entity ID to update
            update_data: Dictionary of attributes to update

        Returns:
            The updated entity if found, None otherwise
        """
        entity = self.get_by_id(session, id)
        if entity:
            for key, value in update_data.items():
                setattr(entity, key, value)
            session.flush()
        return entity

    def delete(self, session: Session, id: int) -> bool:
        """Delete an entity by ID.

        Args:
            session: The database session
            id: The entity ID to delete

        Returns:
            True if deleted, False if not found
        """
        entity = self.get_by_id(session, id)
        if entity:
            session.delete(entity)
            session.flush()
            return True
        return False 