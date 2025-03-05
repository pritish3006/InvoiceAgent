"""Invoice management CLI commands for InvoiceAgent."""

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional

import click
from rich.console import Console
from rich.table import Table as RichTable
from sqlalchemy import desc
from sqlalchemy.exc import IntegrityError

from invoiceagent.cli.utils import (
    confirm_action,
    format_currency,
    format_date,
    print_entity,
    print_error,
    print_info,
    print_section_header,
    print_subsection_header,
    print_success,
    print_table,
    print_warning,
)
from invoiceagent.db.engine import get_session
from invoiceagent.db.models import Invoice, InvoiceItem, InvoiceStatus
from invoiceagent.db.repositories.client import ClientRepository
from invoiceagent.db.repositories.invoice import InvoiceRepository
from invoiceagent.db.repositories.project import ProjectRepository
from invoiceagent.db.repositories.work_log import WorkLogRepository
from invoiceagent.export.pdf_generator import generate_invoice_pdf
from invoiceagent.export.template_manager import (
    get_template_details,
    list_available_templates,
)

# Create console for rich output
console = Console()


@click.group(name="invoice")
def invoice_commands():
    """Invoice management commands."""
    pass


@invoice_commands.command(name="generate")
@click.option("--client-id", required=True, type=int, help="Client ID for the invoice")
@click.option("--start-date", required=True, type=str, help="Start date (YYYY-MM-DD)")
@click.option("--end-date", required=True, type=str, help="End date (YYYY-MM-DD)")
@click.option(
    "--issue-date",
    required=False,
    type=str,
    default=lambda: datetime.now().strftime("%Y-%m-%d"),
    help="Issue date (YYYY-MM-DD)",
)
@click.option("--due-date", required=False, type=str, help="Due date (YYYY-MM-DD)")
@click.option("--tax-rate", required=False, type=float, default=0.0, help="Tax rate percentage")
@click.option("--notes", required=False, type=str, help="Invoice notes")
@click.option("--combine-items", is_flag=True, help="Combine work logs with the same category")
@click.option("--include-equity", is_flag=True, help="Include equity components")
@click.option("--dry-run", is_flag=True, help="Preview invoice without saving")
def generate_invoice(
    client_id,
    start_date,
    end_date,
    issue_date,
    due_date,
    tax_rate,
    notes,
    combine_items,
    include_equity,
    dry_run,
):
    """Generate an invoice from work logs."""
    import logging

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger("invoiceagent.cli.invoice_commands")

    try:
        logger.debug("Starting invoice generation process")
        # Convert string dates to date objects
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
            issue_date_obj = datetime.strptime(issue_date, "%Y-%m-%d").date()
            due_date_obj = (
                datetime.strptime(due_date, "%Y-%m-%d").date()
                if due_date
                else (issue_date_obj + timedelta(days=30))
            )
            logger.debug(
                f"Parsed dates: start={start_date_obj}, end={end_date_obj}, issue={issue_date_obj}, due={due_date_obj}"
            )
        except ValueError as e:
            print_error(f"Invalid date format: {e}. Use YYYY-MM-DD format.")
            return

        if start_date_obj > end_date_obj:
            print_error("Start date must be before end date.")
            return

        if issue_date_obj > due_date_obj:
            print_warning("Issue date is after due date.")

        # Convert tax rate from percentage to decimal
        try:
            tax_rate_decimal = Decimal(str(tax_rate / 100))
            logger.debug(f"Converted tax rate {tax_rate}% to decimal {tax_rate_decimal}")
        except (ValueError, ArithmeticError, TypeError) as e:
            print_error(f"Invalid tax rate: {tax_rate}. Error: {e}")
            return

        with get_session() as session:
            # Verify client exists
            client_repo = ClientRepository()
            client = client_repo.get_by_id(session, client_id)
            logger.debug(f"Client lookup result: {client}")

            if not client:
                print_error(f"Client with ID {client_id} not found.")
                return

            print_info(
                f"Generating invoice for '{client.name}' from {start_date_obj} to {end_date_obj}"
            )

            # Generate invoice
            invoice_repo = InvoiceRepository()

            try:
                # Create a default category mapping
                category_map = {}
                logger.debug("Calling create_invoice_from_work_logs")

                invoice = invoice_repo.create_invoice_from_work_logs(
                    session=session,
                    client_id=client_id,
                    start_date=start_date_obj,
                    end_date=end_date_obj,
                    issue_date=issue_date_obj,
                    due_date=due_date_obj,
                    tax_rate=tax_rate_decimal,
                    notes=notes,
                    category_map=category_map,
                    combine_same_category=combine_items,
                    include_equity=include_equity,
                )

                logger.debug(f"Invoice created: {invoice}")
                logger.debug(
                    f"Invoice items type: {type(invoice.items) if hasattr(invoice, 'items') else 'No items attribute'}"
                )
                logger.debug(
                    f"Invoice items count: {len(invoice.items) if hasattr(invoice, 'items') and invoice.items is not None else 0}"
                )

                if not invoice:
                    print_error("No billable work logs found in the specified date range.")
                    return

                if dry_run:
                    # Don't commit, just preview the invoice
                    logger.debug("Dry run mode - calling _display_invoice_details")
                    _display_invoice_details(invoice, show_items=True)
                    logger.debug("_display_invoice_details completed successfully")
                    print_info("This was a dry run. Invoice not saved.")
                else:
                    # Commit the transaction
                    logger.debug("Committing transaction")
                    session.commit()
                    logger.debug("Transaction committed successfully")
                    # Display invoice details
                    logger.debug("Calling _display_invoice_details for saved invoice")
                    _display_invoice_details(invoice, show_items=True)
                    print_success(f"Invoice #{invoice.invoice_number} generated successfully")
            except Exception as e:
                logger.exception("Error in invoice generation:")
                print_error(f"Error generating invoice: {str(e)}")
                import traceback

                logger.debug(f"Traceback: {traceback.format_exc()}")
    except Exception as e:
        logger.exception("Unhandled exception in generate_invoice:")
        print_error(f"An unexpected error occurred: {str(e)}")
        import traceback

        logger.debug(f"Traceback: {traceback.format_exc()}")


@invoice_commands.command(name="list")
@click.option("--client-id", type=int, help="Filter by client ID")
@click.option(
    "--status",
    type=click.Choice([s.value for s in InvoiceStatus], case_sensitive=False),
    help="Filter by invoice status",
)
@click.option(
    "--start-date",
    type=str,
    help="Filter by issue date - start (YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=str,
    help="Filter by issue date - end (YYYY-MM-DD)",
)
def list_invoices(
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
):
    """List invoices with optional filtering."""
    # Convert date strings to date objects if provided
    start_date_obj = None
    end_date_obj = None

    if start_date:
        try:
            start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
        except ValueError:
            print_error(f"Invalid start date format: {start_date}. Use YYYY-MM-DD.")
            return

    if end_date:
        try:
            end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
        except ValueError:
            print_error(f"Invalid end date format: {end_date}. Use YYYY-MM-DD.")
            return

    with get_session() as session:
        invoice_repo = InvoiceRepository()
        client_repo = ClientRepository()
        invoices = []

        # Determine search method based on provided filters
        if client_id and status and start_date_obj and end_date_obj:
            # Filter by client, status, and date range
            invoices = (
                session.query(Invoice)
                .filter(
                    Invoice.client_id == client_id,
                    Invoice.status == status,
                    Invoice.issue_date >= start_date_obj,
                    Invoice.issue_date <= end_date_obj,
                )
                .order_by(desc(Invoice.issue_date))
                .all()
            )
        elif client_id and status:
            # Filter by client and status
            invoices = (
                session.query(Invoice)
                .filter(Invoice.client_id == client_id, Invoice.status == status)
                .order_by(desc(Invoice.issue_date))
                .all()
            )
        elif client_id and start_date_obj and end_date_obj:
            # Filter by client and date range
            invoices = (
                session.query(Invoice)
                .filter(
                    Invoice.client_id == client_id,
                    Invoice.issue_date >= start_date_obj,
                    Invoice.issue_date <= end_date_obj,
                )
                .order_by(desc(Invoice.issue_date))
                .all()
            )
        elif status and start_date_obj and end_date_obj:
            # Filter by status and date range
            invoices = (
                session.query(Invoice)
                .filter(
                    Invoice.status == status,
                    Invoice.issue_date >= start_date_obj,
                    Invoice.issue_date <= end_date_obj,
                )
                .order_by(desc(Invoice.issue_date))
                .all()
            )
        elif client_id:
            # Filter by client only
            invoices = invoice_repo.get_by_client_id(session, client_id)
        elif status:
            # Filter by status only
            invoices = invoice_repo.get_by_status(session, InvoiceStatus(status))
        elif start_date_obj and end_date_obj:
            # Filter by date range only
            invoices = invoice_repo.get_by_date_range(session, start_date_obj, end_date_obj)
        else:
            # No filters, get all invoices
            invoices = session.query(Invoice).order_by(desc(Invoice.issue_date)).limit(100).all()

        if not invoices:
            print_warning("No invoices found.")
            return

        # Prepare data for table
        columns = [
            "ID",
            "Invoice #",
            "Client",
            "Issue Date",
            "Due Date",
            "Status",
            "Amount",
            "Paid",
        ]

        rows = []
        for invoice in invoices:
            client = client_repo.get_by_id(session, invoice.client_id)
            paid = invoice.status == InvoiceStatus.PAID

            rows.append(
                [
                    invoice.id,
                    invoice.invoice_number,
                    client.name if client else f"Client {invoice.client_id}",
                    format_date(invoice.issue_date),
                    format_date(invoice.due_date),
                    invoice.status.value,
                    format_currency(invoice.total_amount),
                    "✓" if paid else "",
                ]
            )

        # Print table
        title = "Invoices"
        if client_id:
            client = client_repo.get_by_id(session, client_id)
            if client:
                title += f" for {client.name}"
        if status:
            title += f" ({status})"

        print_table(columns, rows, title=title)


@invoice_commands.command(name="get")
@click.argument("invoice_id", type=int)
def get_invoice(invoice_id: int):
    """Get detailed information about an invoice."""
    with get_session() as session:
        invoice_repo = InvoiceRepository()
        client_repo = ClientRepository()

        # Get invoice with items
        invoice = invoice_repo.get_with_client_and_items(session, invoice_id)

        if not invoice:
            print_error(f"Invoice with ID {invoice_id} not found.")
            return

        client = client_repo.get_by_id(session, invoice.client_id)

        # Display invoice header
        print_section_header(f"Invoice {invoice.invoice_number}")

        # Basic info
        invoice_data = {
            "Invoice Number": invoice.invoice_number,
            "Client": client.name if client else f"Client {invoice.client_id}",
            "Status": invoice.status.value,
            "Issue Date": format_date(invoice.issue_date),
            "Due Date": format_date(invoice.due_date),
            "Subtotal": format_currency(invoice.subtotal),
        }

        if invoice.tax_rate:
            invoice_data["Tax Rate"] = f"{float(invoice.tax_rate)}%"
            invoice_data["Tax Amount"] = format_currency(invoice.tax_amount)

        invoice_data["Total Amount"] = format_currency(invoice.total_amount)

        if invoice.notes:
            invoice_data["Notes"] = invoice.notes

        print_entity(invoice_data)

        # Display line items
        print_subsection_header("Line Items")

        if not invoice.items:
            print_warning("No line items found for this invoice.")
            return

        columns = ["Description", "Quantity", "Unit", "Rate", "Amount", "Category"]
        rows = []

        for item in invoice.items:
            rows.append(
                [
                    item.description,
                    float(item.quantity),
                    item.unit or "hour",
                    format_currency(item.rate),
                    format_currency(item.amount),
                    item.category or "",
                ]
            )

        print_table(columns, rows)


@invoice_commands.command(name="update-status")
@click.argument("invoice_id", type=int)
@click.argument("status", type=click.Choice([s.value for s in InvoiceStatus], case_sensitive=False))
def update_invoice_status(invoice_id: int, status: str):
    """Update the status of an invoice."""
    with get_session() as session:
        invoice_repo = InvoiceRepository()

        invoice = invoice_repo.get_by_id(session, invoice_id)
        if not invoice:
            print_error(f"Invoice with ID {invoice_id} not found.")
            return

        old_status = invoice.status.value
        new_status = InvoiceStatus(status)

        # Update the status
        invoice.status = new_status
        session.commit()

        print_success(
            f"Invoice {invoice.invoice_number} status updated from {old_status} to {status}."
        )


@invoice_commands.command(name="delete")
@click.argument("invoice_id", type=int)
@click.option("--force", is_flag=True, help="Force deletion without confirmation")
def delete_invoice(invoice_id: int, force: bool = False):
    """Delete an invoice."""
    with get_session() as session:
        invoice_repo = InvoiceRepository()
        work_log_repo = WorkLogRepository()

        invoice = invoice_repo.get_by_id(session, invoice_id)
        if not invoice:
            print_error(f"Invoice with ID {invoice_id} not found.")
            return

        # Confirm deletion
        if not force and not confirm_action(
            f"Are you sure you want to delete invoice {invoice.invoice_number}? "
            "This action cannot be undone."
        ):
            print_info("Deletion canceled.")
            return

        # Get associated work logs and remove invoice_id
        work_logs = work_log_repo.get_by_invoice_id(session, invoice_id)
        for wl in work_logs:
            wl.invoice_id = None

        # Delete the invoice
        invoice_repo.delete(session, invoice_id)
        session.commit()

        print_success(f"Invoice {invoice.invoice_number} deleted successfully.")


@invoice_commands.command(name="export")
@click.argument("invoice_id", type=int)
@click.option(
    "--output",
    type=click.Path(file_okay=True, dir_okay=False),
    help="Output file path (default: invoice_{number}.pdf in current directory)",
)
@click.option("--template", default="default", help="Invoice template to use")
@click.option("--list-templates", is_flag=True, help="List available templates and exit")
def export_invoice(
    invoice_id: int,
    output: Optional[str] = None,
    template: str = "default",
    list_templates: bool = False,
):
    """Export an invoice to PDF."""

    # List templates if requested
    if list_templates:
        templates = get_template_details()
        print_section_header("Available Invoice Templates")

        for template_info in templates:
            console.print(f"[bold]{template_info['name']}[/bold]: {template_info['description']}")

        return

    # Get invoice
    with get_session() as session:
        invoice_repo = InvoiceRepository()
        work_log_repo = WorkLogRepository()

        # Get invoice with client and items
        invoice = invoice_repo.get_with_client_and_items(session, invoice_id)

        if not invoice:
            print_error(f"Invoice with ID {invoice_id} not found.")
            return

        # Get work logs for this invoice
        work_logs = work_log_repo.get_by_invoice_id(session, invoice_id)

        # Determine output path
        if not output:
            output = f"invoice_{invoice.invoice_number.replace(' ', '_')}.pdf"

        try:
            # Generate PDF
            print_info(f"Generating PDF for invoice {invoice.invoice_number}...")
            pdf_path = generate_invoice_pdf(
                invoice=invoice, output_path=output, template_name=template, work_logs=work_logs
            )

            print_success(f"Invoice exported to {pdf_path}")

        except Exception as e:
            print_error(f"Error exporting invoice: {str(e)}")


@invoice_commands.command(name="templates")
def list_invoice_templates():
    """List available invoice templates."""
    templates = get_template_details()
    print_section_header("Available Invoice Templates")

    for template_info in templates:
        console.print(f"[bold]{template_info['name']}[/bold]: {template_info['description']}")


def _display_invoice_details(invoice, show_items=True):
    """
    Display detailed information about an invoice.

    Args:
        invoice: Invoice object to display
        show_items: Whether to show invoice items
    """
    # Display invoice header information as a dictionary
    invoice_data = {
        "Invoice Number": invoice.invoice_number,
        "Client": invoice.client.name if invoice.client else f"ID: {invoice.client_id}",
        "Status": invoice.status.value,
        "Issue Date": format_date(invoice.issue_date),
        "Due Date": format_date(invoice.due_date),
        "Subtotal": format_currency(invoice.subtotal),
    }

    if invoice.tax_rate and float(invoice.tax_rate) > 0:
        invoice_data["Tax Rate"] = f"{float(invoice.tax_rate) * 100:.2f}%"
        invoice_data["Tax Amount"] = format_currency(invoice.tax_amount)

    invoice_data["Total Amount"] = format_currency(invoice.total_amount)

    if invoice.paid_date:
        invoice_data["Paid Date"] = format_date(invoice.paid_date)

    if invoice.sent_date:
        invoice_data["Sent Date"] = format_date(invoice.sent_date)

    if invoice.notes:
        invoice_data["Notes"] = invoice.notes

    print_entity(invoice_data)

    # Show items if requested
    has_items = hasattr(invoice, "items") and invoice.items is not None
    items_list = []

    # Safely get items from invoice
    if has_items:
        try:
            # Handle both cases: when items is already a list and when it's an attribute with items
            if hasattr(invoice.items, "items") and callable(getattr(invoice.items, "items")):
                # This handles the case where invoice.items has a method called items() (like a dict)
                items_list = list(invoice.items.items())
            else:
                # This handles the case where invoice.items is already iterable (like a list)
                items_list = list(invoice.items)
        except Exception as e:
            print_warning(f"Error processing invoice items: {str(e)}")

    if show_items and items_list:
        print_subsection_header("Invoice Items")

        # Prepare table data
        item_data = []
        for item in items_list:
            item_data.append(
                [
                    item.description,
                    f"{float(item.quantity):.2f}" if item.quantity else "",
                    item.unit or "-",
                    format_currency(item.rate) if item.rate else "-",
                    format_currency(item.amount),
                    item.category or "-",
                ]
            )

        # Print the table
        print_table(["Description", "Quantity", "Unit", "Rate", "Amount", "Category"], item_data)

        # Display equity information if any items have it
        has_equity = any(getattr(item, "has_equity_component", False) for item in items_list)
        if has_equity:
            print_subsection_header("Equity Components")
            equity_data = []
            for item in items_list:
                if getattr(item, "has_equity_component", False):
                    equity_data.append(
                        [
                            item.description,
                            item.equity_type or "-",
                            f"{float(item.equity_quantity):.4f}" if item.equity_quantity else "-",
                            item.equity_description or "-",
                        ]
                    )

            if equity_data:
                print_table(["Description", "Type", "Quantity", "Details"], equity_data)
