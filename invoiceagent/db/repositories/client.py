"""Client repository for database operations."""
from typing import List, Optional

from sqlalchemy.orm import Session, joinedload

from invoiceagent.db.models import Client
from invoiceagent.db.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    """Repository for Client model operations."""

    def __init__(self):
        """Initialize the repository with the Client model."""
        super().__init__(Client)

    def get_by_name(self, session: Session, name: str) -> Optional[Client]:
        """Find a client by name.

        Args:
            session: The database session
            name: The client name to search for

        Returns:
            The matching client or None if not found
        """
        return session.query(Client).filter(Client.name == name).first()

    def get_all_with_projects(self, session: Session) -> List[Client]:
        """Get all clients and eagerly load their associated projects.

        Args:
            session: The database session

        Returns:
            List of clients with their projects loaded
        """
        return session.query(Client).options(
            joinedload(Client.projects)
        ).all()

    def search_by_name(self, session: Session, name_pattern: str) -> List[Client]:
        """Search for clients with names matching a pattern.

        Args:
            session: The database session
            name_pattern: The pattern to search for (using SQL LIKE)

        Returns:
            List of matching clients
        """
        return session.query(Client).filter(
            Client.name.like(f'%{name_pattern}%')
        ).all() 