"""Invoice management CLI commands for InvoiceAgent."""

import asyncio
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Optional

import click
from rich.console import Console
from sqlalchemy.exc import IntegrityError

from invoiceagent.cli.utils import (
    confirm_action, format_currency, format_date, print_entity, print_error,
    print_info, print_section_header, print_subsection_header, print_success,
    print_table, print_warning
)
from invoiceagent.db.engine import get_session
from invoiceagent.db.models import InvoiceItem, InvoiceStatus
from invoiceagent.db.repositories.client import ClientRepository
from invoiceagent.db.repositories.invoice import InvoiceRepository
from invoiceagent.db.repositories.project import ProjectRepository
from invoiceagent.db.repositories.work_log import WorkLogRepository

# Create console for rich output
console = Console()


@click.group(name="invoice")
def invoice_commands():
    """Invoice management commands."""
    pass


@invoice_commands.command(name="generate")
@click.option("--client-id", type=int, required=True, help="Client ID to generate invoice for")
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    required=True,
    help="Start date for work logs (YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    required=True,
    help="End date for work logs (YYYY-MM-DD)",
)
@click.option(
    "--due-date", type=click.DateTime(formats=["%Y-%m-%d"]), help="Invoice due date (YYYY-MM-DD)"
)
@click.option(
    "--tax-rate", type=float, default=0.0, help="Tax rate (percentage, e.g. 8.25 for 8.25%)"
)
@click.option("--notes", help="Additional notes to include on the invoice")
@click.option("--invoice-number", help="Custom invoice number (auto-generated if not provided)")
@click.option("--dry-run", is_flag=True, help="Preview the invoice without saving it")
def generate_invoice(
    client_id: int,
    start_date: datetime,
    end_date: datetime,
    due_date: Optional[datetime] = None,
    tax_rate: float = 0.0,
    notes: Optional[str] = None,
    invoice_number: Optional[str] = None,
    dry_run: bool = False,
):
    """Generate a new invoice for a client based on work logs."""

    async def _generate_invoice():
        try:
            # Convert dates
            start_date_obj = start_date.date()
            end_date_obj = end_date.date()

            # Set due date to 15 days from now if not provided
            if due_date is None:
                due_date_obj = date.today() + timedelta(days=15)
            else:
                due_date_obj = due_date.date()

            # Repositories
            client_repo = ClientRepository()
            work_log_repo = WorkLogRepository()
            project_repo = ProjectRepository()
            invoice_repo = InvoiceRepository()

            with get_session() as session:
                # Check if client exists
                client = client_repo.get_by_id(session, client_id)
                if not client:
                    print_error(f"Client with ID {client_id} not found.")
                    return

                # Get all unbilled work logs for this client in the date range
                work_logs = work_log_repo.get_by_client_id(session, client_id)
                work_logs = [
                    wl
                    for wl in work_logs
                    if wl.invoice_id is None
                    and wl.work_date >= start_date_obj
                    and wl.work_date <= end_date_obj
                    and wl.billable
                ]

                if not work_logs:
                    print_warning(
                        f"No unbilled work logs found for client {client.name} "
                        f"between {format_date(start_date_obj)} and {format_date(end_date_obj)}."
                    )
                    return

                # Group work logs by project for preview
                project_work_logs = {}
                for wl in work_logs:
                    project = project_repo.get_by_id(session, wl.project_id)
                    if project.name not in project_work_logs:
                        project_work_logs[project.name] = []
                    project_work_logs[project.name].append(wl)

                # Display preview
                print_section_header(f"Invoice Preview for {client.name}")
                print_info(f"Period: {format_date(start_date_obj)} to {format_date(end_date_obj)}")
                print_info(f"Due Date: {format_date(due_date_obj)}")

                # Create invoice items preview
                invoice_items = []
                subtotal = Decimal("0")

                for project_name, logs in project_work_logs.items():
                    print_subsection_header(f"Project: {project_name}")

                    # Get the project's hourly rate
                    project = next(p for p in client.projects if p.name == project_name)

                    # Group work logs by category
                    category_logs = {}
                    for log in logs:
                        category = log.category or "General"
                        if category not in category_logs:
                            category_logs[category] = []
                        category_logs[category].append(log)

                    # Create line items
                    for category, cat_logs in category_logs.items():
                        hours = sum(float(log.hours) for log in cat_logs)
                        rate = float(project.hourly_rate)
                        amount = hours * rate

                        # Generate a consolidated description
                        if len(cat_logs) == 1:
                            description = cat_logs[0].description
                        else:
                            # For simplicity in preview, concatenate descriptions
                            description = f"{category} work: " + ", ".join(
                                [log.description.split(".")[0] for log in cat_logs[:3]]
                            )
                            if len(cat_logs) > 3:
                                description += f" and {len(cat_logs) - 3} more tasks"

                        # Create invoice item
                        item = {
                            "description": description,
                            "hours": hours,
                            "rate": rate,
                            "amount": amount,
                            "category": category,
                            "project": project_name,
                        }
                        invoice_items.append(item)
                        subtotal += Decimal(str(amount))

                        # Display item
                        console.print(f"[bold]{description}[/bold]")
                        console.print(
                            f"  Hours: {hours}, Rate: {format_currency(rate)}, Amount: {format_currency(amount)}"
                        )

                # Calculate totals
                tax_amount = subtotal * (Decimal(str(tax_rate)) / Decimal("100"))
                total_amount = subtotal + tax_amount

                # Display summary
                print_section_header("Invoice Summary")
                console.print(f"Subtotal: {format_currency(subtotal)}")
                if tax_rate > 0:
                    console.print(f"Tax ({tax_rate}%): {format_currency(tax_amount)}")
                console.print(f"[bold]Total: {format_currency(total_amount)}[/bold]")

                if dry_run:
                    print_info("This is a dry run - invoice was not saved.")
                    return

                # Confirm before proceeding
                if not confirm_action("Generate this invoice?"):
                    print_info("Invoice generation canceled.")
                    return

                # Generate invoice number if not provided
                inv_number = invoice_number  # Use a local variable to avoid scope issues
                if not inv_number:
                    # Format: INV-YYYYMMDD-XX where XX is a sequential number
                    today_str = date.today().strftime("%Y%m%d")
                    existing_invoices = invoice_repo.get_all(session)
                    existing_numbers = [
                        inv.invoice_number
                        for inv in existing_invoices
                        if inv.invoice_number.startswith(f"INV-{today_str}")
                    ]

                    if existing_numbers:
                        # Find the highest number and increment
                        highest = max([int(num.split("-")[-1]) for num in existing_numbers])
                        seq_num = highest + 1
                    else:
                        seq_num = 1

                    inv_number = f"INV-{today_str}-{seq_num:02d}"

                # Create invoice
                invoice = invoice_repo.create(
                    session,
                    client_id=client_id,
                    invoice_number=inv_number,
                    issue_date=date.today(),
                    due_date=due_date_obj,
                    status=InvoiceStatus.DRAFT,
                    notes=notes,
                    subtotal=subtotal,
                    tax_rate=Decimal(str(tax_rate)) if tax_rate > 0 else None,
                    tax_amount=tax_amount if tax_rate > 0 else None,
                    total_amount=total_amount,
                )

                # Create invoice items
                for item in invoice_items:
                    invoice_item = InvoiceItem(
                        invoice_id=invoice.id,
                        description=item["description"],
                        quantity=item["hours"],
                        unit="hour",
                        rate=item["rate"],
                        amount=item["amount"],
                        category=item["category"],
                    )
                    session.add(invoice_item)

                # Update work logs to associate with this invoice
                for wl in work_logs:
                    wl.invoice_id = invoice.id

                # Commit the transaction
                session.commit()

                print_success(f"Invoice {inv_number} generated successfully!")

        except IntegrityError as e:
            print_error(f"Database error: {str(e)}")
        except Exception as e:
            print_error(f"Error generating invoice: {str(e)}")
            raise

    # Run the async function
    asyncio.run(_generate_invoice())


@invoice_commands.command(name="list")
@click.option("--client-id", type=int, help="Filter by client ID")
@click.option(
    "--status",
    type=click.Choice([s.value for s in InvoiceStatus], case_sensitive=False),
    help="Filter by invoice status",
)
@click.option(
    "--start-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Filter by issue date - start (YYYY-MM-DD)",
)
@click.option(
    "--end-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Filter by issue date - end (YYYY-MM-DD)",
)
def list_invoices(
    client_id: Optional[int] = None,
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
):
    """List invoices with optional filtering."""
    with get_session() as session:
        invoice_repo = InvoiceRepository()
        client_repo = ClientRepository()

        # Apply filters
        if client_id is not None:
            invoices = invoice_repo.get_by_client_id(session, client_id)
        elif start_date is not None and end_date is not None:
            invoices = invoice_repo.get_by_date_range(session, start_date.date(), end_date.date())
        elif status is not None:
            invoice_status = InvoiceStatus(status)
            invoices = invoice_repo.get_by_status(session, invoice_status)
        else:
            invoices = invoice_repo.get_all(session)

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
        invoice = invoice_repo.get_with_items(session, invoice_id)

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
@click.option("--template", help="Invoice template to use")
def export_invoice(invoice_id: int, output: Optional[str] = None, template: Optional[str] = None):
    """Export an invoice to PDF."""
    print_info("PDF export functionality will be implemented in a future version.")
    print_info("This is a placeholder for the export command.")
