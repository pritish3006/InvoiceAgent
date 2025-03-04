"""WorkLog repository for database operations."""

from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from invoiceagent.db.models import Project, WorkLog
from invoiceagent.db.repositories.base import BaseRepository


class WorkLogRepository(BaseRepository[WorkLog]):
    """Repository for WorkLog model operations."""

    def __init__(self):
        """Initialize the repository with the WorkLog model."""
        super().__init__(WorkLog)

    def get_by_date_range(
        self, session: Session, start_date: date, end_date: date
    ) -> List[WorkLog]:
        """Get work logs within a specific date range.

        Args:
            session: The database session
            start_date: The start date (inclusive)
            end_date: The end date (inclusive)

        Returns:
            List of work logs in the date range
        """
        return (
            session.query(WorkLog)
            .filter(WorkLog.work_date >= start_date, WorkLog.work_date <= end_date)
            .order_by(WorkLog.work_date)
            .all()
        )

    def get_by_project_id(self, session: Session, project_id: int) -> List[WorkLog]:
        """Get all work logs for a specific project.

        Args:
            session: The database session
            project_id: The project ID to filter by

        Returns:
            List of work logs for the project
        """
        return (
            session.query(WorkLog)
            .filter(WorkLog.project_id == project_id)
            .order_by(WorkLog.work_date)
            .all()
        )

    def get_by_client_id(self, session: Session, client_id: int) -> List[WorkLog]:
        """Get all work logs for a specific client.

        Args:
            session: The database session
            client_id: The client ID to filter by

        Returns:
            List of work logs for the client
        """
        return (
            session.query(WorkLog)
            .join(WorkLog.project)
            .filter(WorkLog.project.has(client_id=client_id))
            .order_by(WorkLog.work_date)
            .all()
        )

    def get_unbilled(self, session: Session) -> List[WorkLog]:
        """Get all work logs that have not been billed yet.

        Args:
            session: The database session

        Returns:
            List of unbilled work logs
        """
        return (
            session.query(WorkLog)
            .filter(WorkLog.billable == True, WorkLog.invoice_id == None)
            .order_by(WorkLog.work_date)
            .all()
        )

    def get_total_hours_by_project(
        self, session: Session, start_date: date, end_date: date
    ) -> List[tuple]:
        """Get total hours worked per project in a date range.

        Args:
            session: The database session
            start_date: The start date (inclusive)
            end_date: The end date (inclusive)

        Returns:
            List of tuples with (project_id, project_name, total_hours)
        """
        return (
            session.query(
                WorkLog.project_id, Project.name, func.sum(WorkLog.hours).label("total_hours")
            )
            .join(WorkLog.project)
            .filter(WorkLog.work_date >= start_date, WorkLog.work_date <= end_date)
            .group_by(WorkLog.project_id, Project.name)
            .all()
        )

    def get_with_project_and_client(self, session: Session, work_log_id: int) -> Optional[WorkLog]:
        """Get a work log by ID and eagerly load its project and client.

        Args:
            session: The database session
            work_log_id: The work log ID to retrieve

        Returns:
            The work log with project and client loaded, or None if not found
        """
        return (
            session.query(WorkLog)
            .options(joinedload(WorkLog.project).joinedload(Project.client))
            .filter(WorkLog.id == work_log_id)
            .first()
        )
