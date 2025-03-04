"""WorkLog repository for database operations."""

from datetime import date
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from invoiceagent.db.models import Project, WorkLog
from invoiceagent.db.repositories.base import BaseRepository


class WorkLogRepository(BaseRepository[WorkLog]):
    """Repository for WorkLog models."""

    def __init__(self):
        """Initialize the repository with the WorkLog model."""
        super().__init__(WorkLog)

    def get_by_date_range(
        self, session: Session, start_date: date, end_date: date
    ) -> List[WorkLog]:
        """
        Get all work logs within a date range.

        Args:
            session: SQLAlchemy session
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of work logs in the date range
        """
        return (
            session.query(WorkLog)
            .filter(
                WorkLog.work_date >= start_date,
                WorkLog.work_date <= end_date,
            )
            .order_by(WorkLog.work_date.desc())
            .all()
        )

    def get_by_project_id(self, session: Session, project_id: int) -> List[WorkLog]:
        """
        Get all work logs for a project.

        Args:
            session: SQLAlchemy session
            project_id: Project ID

        Returns:
            List of work logs
        """
        return (
            session.query(WorkLog)
            .filter(WorkLog.project_id == project_id)
            .order_by(WorkLog.work_date.desc())
            .all()
        )

    def get_by_client_id(self, session: Session, client_id: int) -> List[WorkLog]:
        """
        Get all work logs for a client.

        Args:
            session: SQLAlchemy session
            client_id: Client ID

        Returns:
            List of work logs
        """
        return (
            session.query(WorkLog)
            .join(Project)
            .filter(Project.client_id == client_id)
            .order_by(WorkLog.work_date.desc())
            .all()
        )
        
    def get_by_invoice_id(self, session: Session, invoice_id: int) -> List[WorkLog]:
        """
        Get all work logs for an invoice.

        Args:
            session: SQLAlchemy session
            invoice_id: Invoice ID

        Returns:
            List of work logs
        """
        return (
            session.query(WorkLog)
            .filter(WorkLog.invoice_id == invoice_id)
            .order_by(WorkLog.work_date.desc())
            .all()
        )

    def get_unbilled(self, session: Session) -> List[WorkLog]:
        """
        Get all unbilled work logs.

        Args:
            session: SQLAlchemy session

        Returns:
            List of unbilled work logs
        """
        return (
            session.query(WorkLog)
            .filter(WorkLog.invoice_id.is_(None), WorkLog.billable.is_(True))
            .order_by(WorkLog.work_date.desc())
            .all()
        )

    def get_total_hours_by_project(
        self, session: Session, start_date: date, end_date: date
    ) -> List[tuple]:
        """
        Get total hours by project within a date range.

        Args:
            session: SQLAlchemy session
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of tuples (project_id, project_name, total_hours)
        """
        return (
            session.query(
                Project.id,
                Project.name,
                func.sum(WorkLog.hours).label("total_hours"),
            )
            .join(Project)
            .filter(
                WorkLog.work_date >= start_date,
                WorkLog.work_date <= end_date,
            )
            .group_by(Project.id, Project.name)
            .all()
        )

    def get_with_project_and_client(self, session: Session, work_log_id: int) -> Optional[WorkLog]:
        """
        Get a work log with its project and client.

        Args:
            session: SQLAlchemy session
            work_log_id: Work log ID

        Returns:
            The work log with project and client loaded, or None if not found
        """
        return (
            session.query(WorkLog)
            .options(joinedload(WorkLog.project).joinedload(Project.client))
            .filter(WorkLog.id == work_log_id)
            .first()
        )
