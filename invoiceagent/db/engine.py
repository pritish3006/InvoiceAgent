"""
Database engine configuration for InvoiceAgent.

Handles SQLite engine setup, connection management, and session factories.
"""

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, Optional

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from invoiceagent.db.models import Base

# Default location for SQLite database in user's home directory
DEFAULT_DB_PATH = Path.home() / ".invoiceagent" / "invoiceagent.db"

# Global engine instance
_engine = None


def get_engine(db_path: Optional[str] = None) -> Engine:
    """
    Get or create the SQLAlchemy engine.

    Args:
        db_path: Path to the SQLite database file. If None, uses the default path.

    Returns:
        SQLAlchemy engine
    """
    global _engine
    if _engine is not None:
        return _engine

    # Use the provided path or default
    if db_path is None:
        db_path = os.environ.get("INVOICEAGENT_DB_PATH", str(DEFAULT_DB_PATH))

    # Ensure directory exists
    db_file = Path(db_path)
    db_file.parent.mkdir(parents=True, exist_ok=True)

    # Create engine with SQLite settings
    _engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=os.environ.get("INVOICEAGENT_DB_ECHO", "0") == "1",
    )

    return _engine


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initialize the database by creating all tables.

    Args:
        db_path: Path to the SQLite database file. If None, uses the default path.
    """
    engine = get_engine(db_path)
    Base.metadata.create_all(engine)


# Session factory
_SessionLocal = None


def get_session_factory() -> sessionmaker:
    """
    Get the session factory for creating database sessions.

    Returns:
        SQLAlchemy sessionmaker
    """
    global _SessionLocal
    if _SessionLocal is None:
        engine = get_engine()
        _SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return _SessionLocal


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.

    Yields:
        SQLAlchemy session

    Example:
        ```
        with get_session() as session:
            clients = session.query(Client).all()
        ```
    """
    session_factory = get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
