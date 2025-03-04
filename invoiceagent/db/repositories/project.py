"""Project repository for database operations."""

from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from invoiceagent.db.models import Project
from invoiceagent.db.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    """Repository for Project model operations."""

    def __init__(self):
        """Initialize the repository with the Project model."""
        super().__init__(Project)

    def get_by_name(self, session: Session, name: str) -> Optional[Project]:
        """Find a project by name.

        Args:
            session: The database session
            name: The project name to search for

        Returns:
            The matching project or None if not found
        """
        return session.query(Project).filter(Project.name == name).first()

    def get_by_client_id(self, session: Session, client_id: int) -> List[Project]:
        """Get all projects for a specific client.

        Args:
            session: The database session
            client_id: The client ID to filter by

        Returns:
            List of projects belonging to the client
        """
        return session.query(Project).filter(Project.client_id == client_id).all()

    def get_with_client(self, session: Session, project_id: int) -> Optional[Project]:
        """Get a project by ID and eagerly load its client.

        Args:
            session: The database session
            project_id: The project ID to retrieve

        Returns:
            The project with client loaded, or None if not found
        """
        return (
            session.query(Project)
            .options(joinedload(Project.client))
            .filter(Project.id == project_id)
            .first()
        )

    def get_active_projects(self, session: Session) -> List[Project]:
        """Get all active projects.

        Args:
            session: The database session

        Returns:
            List of active projects
        """
        return session.query(Project).filter(Project.active == True).all()
