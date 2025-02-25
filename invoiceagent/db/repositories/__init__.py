"""
Database repositories package for InvoiceAgent.

This package contains repository classes for database operations.
Each repository provides CRUD operations for specific model types.
"""

from invoiceagent.db.repositories.base import BaseRepository
from invoiceagent.db.repositories.client import ClientRepository
from invoiceagent.db.repositories.project import ProjectRepository
from invoiceagent.db.repositories.work_log import WorkLogRepository
from invoiceagent.db.repositories.invoice import InvoiceRepository

__all__ = [
    'BaseRepository',
    'ClientRepository',
    'ProjectRepository',
    'WorkLogRepository',
    'InvoiceRepository',
] 