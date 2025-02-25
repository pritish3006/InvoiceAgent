"""
SQLAlchemy models for the InvoiceAgent database.

Defines all entity models and relationships needed for storing invoice data.
"""

import enum
from datetime import date, datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    Date,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Table,
    Text,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# Base class for all models
Base = declarative_base()

# Association table for many-to-many relationships
work_log_tag = Table(
    "work_log_tag",
    Base.metadata,
    Column("work_log_id", Integer, ForeignKey("work_logs.id"), primary_key=True),
    Column("tag_name", String, ForeignKey("tags.name"), primary_key=True),
)


class InvoiceStatus(enum.Enum):
    """Status of an invoice."""

    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELED = "canceled"


class Tag(Base):
    """Tag model for categorizing work logs."""

    __tablename__ = "tags"

    name = Column(String, primary_key=True)
    description = Column(String, nullable=True)

    # Relationships
    work_logs = relationship("WorkLog", secondary=work_log_tag, back_populates="tags")

    def __repr__(self) -> str:
        return f"<Tag(name='{self.name}')>"


class Client(Base):
    """Client model representing a customer."""

    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    contact_name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    address = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    projects = relationship("Project", back_populates="client", cascade="all, delete-orphan")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Client(id={self.id}, name='{self.name}')>"


class Project(Base):
    """Project model representing a client project."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    description = Column(Text, nullable=True)
    hourly_rate = Column(Numeric(10, 2), nullable=False, default=0.0)
    is_active = Column(Boolean, default=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client = relationship("Client", back_populates="projects")
    work_logs = relationship("WorkLog", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Project(id={self.id}, name='{self.name}', client_id={self.client_id})>"


class WorkLog(Base):
    """Work log model representing time spent on a project."""

    __tablename__ = "work_logs"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    work_date = Column(Date, nullable=False, index=True)
    hours = Column(Numeric(8, 2), nullable=False)
    description = Column(Text, nullable=False)
    category = Column(String, nullable=True)
    billable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship("Project", back_populates="work_logs")
    tags = relationship("Tag", secondary=work_log_tag, back_populates="work_logs")
    invoice = relationship("Invoice", back_populates="work_logs")

    def __repr__(self) -> str:
        return f"<WorkLog(id={self.id}, project_id={self.project_id}, date='{self.work_date}', hours={self.hours})>"


class Invoice(Base):
    """Invoice entity model."""

    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    invoice_number = Column(String(50), nullable=False, unique=True)
    issue_date = Column(Date, nullable=False, default=date.today)
    due_date = Column(Date, nullable=False)
    status = Column(Enum(InvoiceStatus), nullable=False, default=InvoiceStatus.DRAFT)
    notes = Column(Text, nullable=True)
    subtotal = Column(Numeric(10, 2), nullable=False, default=0)
    tax_rate = Column(Numeric(5, 2), nullable=True)
    tax_amount = Column(Numeric(10, 2), nullable=True)
    total_amount = Column(Numeric(10, 2), nullable=False, default=0)
    invoice_metadata = Column(JSON, nullable=True)

    # Relationships
    client = relationship("Client", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    work_logs = relationship("WorkLog", back_populates="invoice")

    def __repr__(self):
        return f"<Invoice {self.invoice_number}: {self.total_amount}>"


class InvoiceItem(Base):
    """Invoice item model representing a single line item on an invoice."""

    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    work_log_id = Column(Integer, ForeignKey("work_logs.id"), nullable=True)
    description = Column(String(255), nullable=False)
    quantity = Column(Numeric(8, 2), nullable=False, default=1)
    unit = Column(String(50), nullable=True)
    rate = Column(Numeric(10, 2), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=True)

    # Relationships
    invoice = relationship("Invoice", back_populates="items")
    work_log = relationship("WorkLog", foreign_keys=[work_log_id])

    def __repr__(self):
        return f"<InvoiceItem: {self.description[:20]}... - {self.amount}>"
