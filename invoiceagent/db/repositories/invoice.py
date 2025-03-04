"""Invoice repository for database operations."""

from datetime import date
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from invoiceagent.db.models import Invoice, InvoiceStatus
from invoiceagent.db.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    """Repository for Invoice model operations."""

    def __init__(self):
        """Initialize the repository with the Invoice model."""
        super().__init__(Invoice)

    def get_by_number(self, session: Session, invoice_number: str) -> Optional[Invoice]:
        """Find an invoice by its number.

        Args:
            session: The database session
            invoice_number: The invoice number to search for

        Returns:
            The matching invoice or None if not found
        """
        return session.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()

    def get_by_status(self, session: Session, status: InvoiceStatus) -> List[Invoice]:
        """Get all invoices with a specific status.

        Args:
            session: The database session
            status: The status to filter by

        Returns:
            List of invoices with the given status
        """
        return session.query(Invoice).filter(Invoice.status == status).all()

    def get_by_client_id(self, session: Session, client_id: int) -> List[Invoice]:
        """Get all invoices for a specific client.

        Args:
            session: The database session
            client_id: The client ID to filter by

        Returns:
            List of invoices for the client
        """
        return session.query(Invoice).filter(Invoice.client_id == client_id).all()

    def get_by_date_range(
        self, session: Session, start_date: date, end_date: date
    ) -> List[Invoice]:
        """Get invoices within a specific issue date range.

        Args:
            session: The database session
            start_date: The start date (inclusive)
            end_date: The end date (inclusive)

        Returns:
            List of invoices in the date range
        """
        return (
            session.query(Invoice)
            .filter(Invoice.issue_date >= start_date, Invoice.issue_date <= end_date)
            .order_by(Invoice.issue_date)
            .all()
        )

    def get_with_items(self, session: Session, invoice_id: int) -> Optional[Invoice]:
        """Get an invoice by ID and eagerly load its items.

        Args:
            session: The database session
            invoice_id: The invoice ID to retrieve

        Returns:
            The invoice with items loaded, or None if not found
        """
        return (
            session.query(Invoice)
            .options(joinedload(Invoice.items))
            .filter(Invoice.id == invoice_id)
            .first()
        )

    def get_with_client_and_items(self, session: Session, invoice_id: int) -> Optional[Invoice]:
        """Get an invoice by ID and eagerly load its client and items.

        Args:
            session: The database session
            invoice_id: The invoice ID to retrieve

        Returns:
            The invoice with client and items loaded, or None if not found
        """
        return (
            session.query(Invoice)
            .options(joinedload(Invoice.client), joinedload(Invoice.items))
            .filter(Invoice.id == invoice_id)
            .first()
        )

    def get_total_by_client(self, session: Session, year: int) -> List[tuple]:
        """Get total invoice amounts by client for a specific year.

        Args:
            session: The database session
            year: The year to filter by

        Returns:
            List of tuples with (client_id, client_name, total_amount)
        """
        from sqlalchemy import extract, func

        return (
            session.query(
                Invoice.client_id,
                Invoice.client.name,
                func.sum(Invoice.total_amount).label("total_amount"),
            )
            .join(Invoice.client)
            .filter(extract("year", Invoice.issue_date) == year)
            .group_by(Invoice.client_id)
            .all()
        )

    def create(
        self,
        session: Session,
        client_id: int,
        invoice_number: str,
        issue_date: date,
        due_date: date,
        status: InvoiceStatus = InvoiceStatus.DRAFT,
        notes: Optional[str] = None,
        subtotal: Optional[Decimal] = None,
        tax_rate: Optional[Decimal] = None,
        tax_amount: Optional[Decimal] = None,
        total_amount: Optional[Decimal] = None,
    ) -> Invoice:
        """Create a new invoice.

        Args:
            session: The database session
            client_id: The client ID
            invoice_number: The invoice number
            issue_date: The issue date
            due_date: The due date
            status: The initial status (default: DRAFT)
            notes: Optional notes
            subtotal: The subtotal amount
            tax_rate: The tax rate percentage
            tax_amount: The tax amount
            total_amount: The total invoice amount

        Returns:
            The created invoice
        """
        invoice = Invoice(
            client_id=client_id,
            invoice_number=invoice_number,
            issue_date=issue_date,
            due_date=due_date,
            status=status,
            notes=notes,
            subtotal=subtotal,
            tax_rate=tax_rate,
            tax_amount=tax_amount,
            total_amount=total_amount,
        )
        session.add(invoice)
        session.flush()  # Flush to get the ID
        return invoice

    def update_status(
        self, session: Session, invoice_id: int, status: InvoiceStatus
    ) -> Optional[Invoice]:
        """Update the status of an invoice.

        Args:
            session: The database session
            invoice_id: The invoice ID
            status: The new status

        Returns:
            The updated invoice or None if not found
        """
        invoice = self.get_by_id(session, invoice_id)
        if invoice:
            invoice.status = status
            session.flush()
        return invoice

    def mark_as_paid(
        self, session: Session, invoice_id: int, payment_date: Optional[date] = None
    ) -> Optional[Invoice]:
        """Mark an invoice as paid.

        Args:
            session: The database session
            invoice_id: The invoice ID
            payment_date: The payment date (default: today)

        Returns:
            The updated invoice or None if not found
        """
        invoice = self.get_by_id(session, invoice_id)
        if invoice:
            invoice.status = InvoiceStatus.PAID
            invoice.payment_date = payment_date or date.today()
            session.flush()
        return invoice

    def get_unpaid(self, session: Session) -> List[Invoice]:
        """Get all unpaid invoices (draft or sent).

        Args:
            session: The database session

        Returns:
            List of unpaid invoices
        """
        return (
            session.query(Invoice)
            .filter(
                or_(
                    Invoice.status == InvoiceStatus.DRAFT,
                    Invoice.status == InvoiceStatus.SENT,
                )
            )
            .order_by(Invoice.due_date)
            .all()
        )
