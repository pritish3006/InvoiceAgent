"""
PDF generator for invoices.

This module provides functionality for generating PDF invoices using ReportLab.
"""

import datetime
import logging
from decimal import Decimal
from pathlib import Path
from typing import List, Optional, Tuple, Union

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4, LETTER, landscape, portrait
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from invoiceagent.db.models import Client, Invoice
from invoiceagent.export.models import InvoiceTemplateConfig, TextAlignment
from invoiceagent.export.template_manager import get_logo_path, load_template

logger = logging.getLogger(__name__)

# Define page sizes
PAGE_SIZES = {
    "A4": A4,
    "LETTER": LETTER,
}

# Register default fonts - Helvetica is a built-in font in ReportLab
# There's no need to register it explicitly. We'll use the built-in font names.
# For reference, built-in font families:
# - Helvetica (Normal, Bold, Italic, BoldItalic)
# - Times-Roman (Normal, Bold, Italic, BoldItalic)
# - Courier (Normal, Bold, Italic, BoldItalic)


def _get_alignment(alignment: TextAlignment) -> int:
    """
    Convert TextAlignment enum to ReportLab alignment constant.

    Args:
        alignment: TextAlignment enum value

    Returns:
        ReportLab alignment constant
    """
    if alignment == TextAlignment.LEFT:
        return TA_LEFT
    elif alignment == TextAlignment.CENTER:
        return TA_CENTER
    elif alignment == TextAlignment.RIGHT:
        return TA_RIGHT
    return TA_LEFT


def _create_paragraph_style(
    name: str,
    font_name: str = "Helvetica",
    font_size: int = 10,
    text_color: Tuple[int, int, int] = (0, 0, 0),
    alignment: str = "LEFT",
    bold: bool = False,
    italic: bool = False,
    line_height: float = 1.2,
) -> ParagraphStyle:
    """
    Create a paragraph style for ReportLab.

    Args:
        name: Style name
        font_name: Font family name
        font_size: Font size in points
        text_color: RGB color tuple
        alignment: Text alignment (LEFT, CENTER, RIGHT)
        bold: Whether to use bold font
        italic: Whether to use italic font
        line_height: Line height multiplier

    Returns:
        ReportLab ParagraphStyle
    """
    # Use standard ReportLab font names - they use different naming conventions
    font_suffix = ""
    if bold and italic:
        font_suffix = (
            "-BoldOblique"  # ReportLab uses "Oblique" instead of "Italic" for Helvetica
        )
    elif bold:
        font_suffix = "-Bold"
    elif italic:
        font_suffix = (
            "-Oblique"  # ReportLab uses "Oblique" instead of "Italic" for Helvetica
        )

    # Full font name - handle the case where font_name already includes style suffix
    if font_suffix and not font_name.endswith(font_suffix):
        font_name = f"{font_name}{font_suffix}"

    # Convert string alignment to ReportLab alignment constants
    align_const = TA_LEFT
    if alignment == "CENTER":
        align_const = TA_CENTER
    elif alignment == "RIGHT":
        align_const = TA_RIGHT

    return ParagraphStyle(
        name=name,
        fontName=font_name,
        fontSize=font_size,
        textColor=colors.Color(*[c / 255 for c in text_color]),
        alignment=align_const,
        leading=font_size * line_height,
    )


def _format_currency(amount: Union[float, Decimal]) -> str:
    """
    Format a currency amount.

    Args:
        amount: Amount to format

    Returns:
        Formatted currency string
    """
    return f"${float(amount):.2f}"


def _format_date(date_obj: date) -> str:
    """
    Format a date.

    Args:
        date_obj: Date to format

    Returns:
        Formatted date string
    """
    return date_obj.strftime("%B %d, %Y")


def _format_equity(amount: Union[float, Decimal], equity_type: str) -> str:
    """
    Format an equity amount.

    Args:
        amount: Amount to format
        equity_type: Type of equity

    Returns:
        Formatted equity string
    """
    return f"{float(amount):.4f} {equity_type}"


def generate_invoice_pdf(
    invoice: Invoice,
    output_path: str,
    template_name: str = "default",
    work_logs: Optional[List] = None,
) -> str:
    """
    Generate a PDF invoice.

    Args:
        invoice: Invoice object
        output_path: Path to save the PDF
        template_name: Name of the template to use
        work_logs: Optional list of work logs (if not provided, will be loaded from database)

    Returns:
        Path to the generated PDF
    """
    # Load template configuration
    template = load_template(template_name)
    if not template:
        logger.error(f"Failed to load template '{template_name}'")
        raise ValueError(f"Template '{template_name}' not found")

    # Get page size and orientation
    page_size = PAGE_SIZES.get(template.page_size.upper(), A4)
    if template.page_orientation.lower() == "landscape":
        page_size = landscape(page_size)
    else:
        page_size = portrait(page_size)

    # Create PDF document
    doc = SimpleDocTemplate(
        output_path,
        pagesize=page_size,
        leftMargin=template.margin_left,
        rightMargin=template.margin_right,
        topMargin=template.margin_top,
        bottomMargin=template.margin_bottom,
    )

    # Get client
    client = invoice.client

    # Get work logs if not provided
    if work_logs is None:
        work_log_repo = WorkLogRepository()
        with get_session() as session:
            work_logs = work_log_repo.get_by_invoice_id(session, invoice.id)

    # Create document elements
    elements = []

    # Add header (which now includes the INVOICE title and invoice info)
    elements.extend(_create_header_section(template, client, invoice, doc.width))
    elements.append(Spacer(1, 20))

    # Add client section
    client_section = _create_client_section(template, client)
    elements.extend(client_section)
    elements.append(Spacer(1, 15))

    # Add items table (with no invoice combining)
    if template.items_table.show_items:
        items_table = _create_items_table(template, invoice, doc.width)
        elements.extend(items_table)
        elements.append(Spacer(1, 15))

    # Add equity items table if applicable
    has_equity_items = any(item.has_equity_component for item in invoice.items)
    if has_equity_items and template.items_table.show_equity:
        equity_table = _create_equity_items_table(template, invoice, doc.width)
        if equity_table:
            elements.extend(equity_table)
            elements.append(Spacer(1, 15))

    # Add totals section
    totals_section = _create_totals_section(template, invoice)
    elements.extend(totals_section)

    # Add notes if present and meaningful
    if invoice.notes and template.items_table.show_notes:
        # Check if notes are not empty or just trivial strings
        notes_text = invoice.notes.strip()

        # Define what's considered a trivial note (client name + invoice)
        client_name_with_invoice = f"{client.name.lower()} invoice"
        is_trivial_note = (
            notes_text.lower() == client_name_with_invoice
            or notes_text.lower() == "invoice"
            or notes_text.lower() == client.name.lower()
        )

        if notes_text and not is_trivial_note:
            notes_style = _create_paragraph_style(
                "notes",
                font_name=template.items_table.row_style.text_style.font.family,
                font_size=template.items_table.row_style.text_style.font.size - 1,
                text_color=template.items_table.row_style.text_style.font.color.to_rgb(),
                alignment=_get_alignment(
                    template.items_table.row_style.text_style.alignment
                ),
            )

            notes_title = Paragraph(
                f"<b>{template.items_table.notes_title}</b>", notes_style
            )
            notes_text_paragraph = Paragraph(notes_text, notes_style)

            elements.append(Spacer(1, 10))
            elements.append(notes_title)
            elements.append(notes_text_paragraph)

    # Add footer
    elements.append(Spacer(1, 30))
    elements.extend(_create_footer_section(template))

    # Build PDF
    doc.build(elements)

    return output_path


def _create_header_section(
    template: InvoiceTemplateConfig,
    client: Client,
    invoice: Invoice,
    available_width: float,
) -> List:
    """
    Create the header section of the invoice.

    Args:
        template: Template configuration
        client: Client object
        invoice: Invoice object
        available_width: Available width for the header

    Returns:
        List of flowable elements
    """
    elements = []

    # Create title with "INVOICE" centered at the top
    title_style = _create_paragraph_style(
        "invoice_title",
        font_name=template.header.style.text_style.font.family,
        font_size=template.header.style.text_style.font.size + 6,
        text_color=template.header.style.text_style.font.color.to_rgb(),
        alignment=TA_CENTER,  # Always center the invoice title
        bold=True,
    )

    # Create a 1-column table for the centered title
    title_table = Table(
        [[Paragraph(template.invoice_info.title, title_style)]],
        colWidths=[available_width],
    )
    title_table.setStyle(
        TableStyle(
            [
                ("ALIGN", (0, 0), (0, 0), "CENTER"),
                ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
            ]
        )
    )
    elements.append(title_table)
    elements.append(Spacer(1, 10))  # Small space after title

    # Company info styles
    company_style = _create_paragraph_style(
        "company_name",
        font_name=template.header.style.text_style.font.family,
        font_size=template.header.style.text_style.font.size,
        text_color=template.header.style.text_style.font.color.to_rgb(),
        alignment=TA_RIGHT,  # Always right-align company info
        bold=template.header.style.text_style.font.bold,
        italic=template.header.style.text_style.font.italic,
    )

    company_details_style = _create_paragraph_style(
        "company_details",
        font_name=template.header.style.text_style.font.family,
        font_size=template.header.style.text_style.font.size - 2,
        text_color=template.header.style.text_style.font.color.to_rgb(),
        alignment=TA_RIGHT,  # Always right-align company info
    )

    # Invoice info style (left-aligned)
    invoice_info_style = _create_paragraph_style(
        "invoice_info",
        font_name=template.invoice_info.style.text_style.font.family,
        font_size=template.invoice_info.style.text_style.font.size,
        text_color=template.invoice_info.style.text_style.font.color.to_rgb(),
        alignment=TA_LEFT,  # Always left-align invoice info
    )

    # Prepare company information
    company_name = Paragraph(template.header.company_name, company_style)
    company_details = Paragraph(
        template.header.company_details.replace("\n", "<br/>"), company_details_style
    )

    # Logo (if available)
    logo_cell = ""
    if template.header.show_logo:
        # Check for logo file
        logo_path = get_logo_path()
        if logo_path.exists() and logo_path.stat().st_size > 0:
            try:
                logo = Image(str(logo_path))
                logo.drawHeight = template.header.logo_position.height
                logo.drawWidth = template.header.logo_position.width
                logo_cell = logo
            except Exception as e:
                logger.warning(f"Failed to load logo image: {e}")

    # Prepare invoice information paragraphs
    invoice_number = (
        Paragraph(f"<b>Invoice #:</b> {invoice.invoice_number}", invoice_info_style)
        if template.invoice_info.show_invoice_number
        else ""
    )
    issue_date = (
        Paragraph(
            f"<b>Issue Date:</b> {_format_date(invoice.issue_date)}", invoice_info_style
        )
        if template.invoice_info.show_issue_date
        else ""
    )
    due_date = (
        Paragraph(
            f"<b>Due Date:</b> {_format_date(invoice.due_date)}", invoice_info_style
        )
        if template.invoice_info.show_due_date
        else ""
    )

    # Create a table with company info on right, invoice info on left
    # Use a single row for invoice #, a single row for combined dates to reduce spacing
    header_data = [
        [invoice_number, company_name],
        [
            Table(
                [[issue_date], [due_date]],
                colWidths=["100%"],
                rowHeights=[14, 14],  # Fixed row heights to reduce spacing
                style=[
                    ("TOPPADDING", (0, 0), (0, -1), 0),
                    ("BOTTOMPADDING", (0, 0), (0, -1), 0),
                    ("LEFTPADDING", (0, 0), (0, -1), 0),
                    ("RIGHTPADDING", (0, 0), (0, -1), 0),
                ],
            ),
            company_details,
        ],
    ]

    # If logo is present, include it in the table
    if logo_cell:
        header_data.append(["", logo_cell])

    # Create the table
    header_table = Table(header_data, colWidths=["50%", "50%"])
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), template.header.style.padding.right),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),  # No bottom padding
                ("LEFTPADDING", (0, 0), (-1, -1), template.header.style.padding.left),
                (
                    "ALIGN",
                    (0, 0),
                    (0, -1),
                    "LEFT",
                ),  # Left column left-aligned (invoice info)
                (
                    "ALIGN",
                    (1, 0),
                    (1, -1),
                    "RIGHT",
                ),  # Right column right-aligned (company info)
            ]
        )
    )

    elements.append(header_table)

    return elements


def _create_client_section(template: InvoiceTemplateConfig, client: Client) -> List:
    """
    Create the client section of the invoice.

    Args:
        template: Template configuration
        client: Client object

    Returns:
        List of flowable elements
    """
    elements = []

    # Create styles
    title_style = _create_paragraph_style(
        "client_title",
        font_name=template.client.style.text_style.font.family,
        font_size=template.client.style.text_style.font.size,
        text_color=template.client.style.text_style.font.color.to_rgb(),
        alignment=_get_alignment(template.client.style.text_style.alignment),
        bold=True,
    )

    text_style = _create_paragraph_style(
        "client_text",
        font_name=template.client.style.text_style.font.family,
        font_size=template.client.style.text_style.font.size,
        text_color=template.client.style.text_style.font.color.to_rgb(),
        alignment=_get_alignment(template.client.style.text_style.alignment),
    )

    # Create client info
    title = Paragraph(template.client.title, title_style)

    client_info = []
    client_info.append(client.name)
    if client.contact_name:
        client_info.append(f"Attn: {client.contact_name}")
    if client.address:
        client_info.append(client.address.replace("\n", "<br/>"))
    if client.email:
        client_info.append(f"Email: {client.email}")
    if client.phone:
        client_info.append(f"Phone: {client.phone}")

    client_text = Paragraph("<br/>".join(client_info), text_style)

    # Create client table
    client_data = [[title], [client_text]]
    client_table = Table(client_data, colWidths=["100%"])
    client_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), template.client.style.padding.top),
                ("RIGHTPADDING", (0, 0), (-1, -1), template.client.style.padding.right),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    template.client.style.padding.bottom,
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), template.client.style.padding.left),
            ]
        )
    )

    elements.append(client_table)
    return elements


def _create_items_table(
    template: InvoiceTemplateConfig, invoice: Invoice, available_width: float
) -> List:
    """
    Create the items table section for cash components.

    Args:
        template: Template configuration
        invoice: Invoice object
        available_width: Available width for the table

    Returns:
        List of flowable elements
    """
    elements = []

    # Filter out equity items
    cash_items = [item for item in invoice.items if not item.has_equity_component]
    if not cash_items:
        return elements

    # Create section title
    section_title_style = _create_paragraph_style(
        "cash_section_title",
        font_name=template.items_table.header_style.text_style.font.family,
        font_size=template.items_table.header_style.text_style.font.size + 2,
        text_color=template.items_table.header_style.text_style.font.color.to_rgb(),
        alignment="LEFT",
        bold=True,
    )

    elements.append(Paragraph("Services & Expenses", section_title_style))
    elements.append(Spacer(1, 10))

    # Create styles
    header_style = _create_paragraph_style(
        "items_header",
        font_name=template.items_table.header_style.text_style.font.family,
        font_size=template.items_table.header_style.text_style.font.size,
        text_color=template.items_table.header_style.text_style.font.color.to_rgb(),
        alignment="LEFT",  # Will be overridden by column alignment
        bold=template.items_table.header_style.text_style.font.bold,
    )

    row_style = _create_paragraph_style(
        "items_row",
        font_name=template.items_table.row_style.text_style.font.family,
        font_size=template.items_table.row_style.text_style.font.size,
        text_color=template.items_table.row_style.text_style.font.color.to_rgb(),
        alignment="LEFT",  # Will be overridden by column alignment
    )

    # Create table data
    table_data = []

    # Add header row
    header_row = []
    for column in template.items_table.columns:
        header_cell = Paragraph(column["title"], header_style)
        header_row.append(header_cell)
    table_data.append(header_row)

    # Add item rows
    for item in cash_items:
        row = []
        for column in template.items_table.columns:
            column_name = column["name"]
            if column_name == "description":
                cell_text = item.description
                if template.items_table.show_category and item.category:
                    cell_text = f"<b>{item.category}</b><br/>{cell_text}"
                cell = Paragraph(cell_text, row_style)
            elif column_name == "quantity":
                cell = Paragraph(f"{float(item.quantity):.2f}", row_style)
            elif column_name == "rate":
                cell = Paragraph(_format_currency(item.rate), row_style)
            elif column_name == "amount":
                cell = Paragraph(_format_currency(item.amount), row_style)
            else:
                cell = Paragraph("", row_style)
            row.append(cell)
        table_data.append(row)

    # Calculate column widths
    col_widths = []
    total_width_units = sum(col["width"] for col in template.items_table.columns)

    for column in template.items_table.columns:
        width_percent = column["width"] / total_width_units
        col_widths.append(available_width * width_percent)

    # Create table
    items_table = Table(table_data, colWidths=col_widths)

    # Apply table styles
    table_style = [
        # Header style
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            (
                colors.Color(
                    *[
                        c / 255
                        for c in template.items_table.header_style.background_color.to_rgb()
                    ]
                )
                if template.items_table.header_style.background_color
                else colors.white
            ),
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            template.items_table.header_style.border.width,
            colors.Color(
                *[
                    c / 255
                    for c in template.items_table.header_style.border.color.to_rgb()
                ]
            ),
        ),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), template.items_table.header_style.padding.top),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, 0),
            template.items_table.header_style.padding.right,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, 0),
            template.items_table.header_style.padding.bottom,
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, 0),
            template.items_table.header_style.padding.left,
        ),
    ]

    # Row styles
    for i in range(1, len(table_data)):
        # Alternate row background if specified
        if template.items_table.alternate_row_style and i % 2 == 0:
            table_style.append(
                (
                    "BACKGROUND",
                    (0, i),
                    (-1, i),
                    (
                        colors.Color(
                            *[
                                c / 255
                                for c in template.items_table.alternate_row_style.background_color.to_rgb()
                            ]
                        )
                        if template.items_table.alternate_row_style.background_color
                        else colors.white
                    ),
                )
            )

        # Add padding
        table_style.extend(
            [
                (
                    "TOPPADDING",
                    (0, i),
                    (-1, i),
                    template.items_table.row_style.padding.top,
                ),
                (
                    "RIGHTPADDING",
                    (0, i),
                    (-1, i),
                    template.items_table.row_style.padding.right,
                ),
                (
                    "BOTTOMPADDING",
                    (0, i),
                    (-1, i),
                    template.items_table.row_style.padding.bottom,
                ),
                (
                    "LEFTPADDING",
                    (0, i),
                    (-1, i),
                    template.items_table.row_style.padding.left,
                ),
            ]
        )

    # Apply column alignments
    for i, column in enumerate(template.items_table.columns):
        alignment = column.get("align", "left").upper()
        table_style.append(("ALIGN", (i, 0), (i, -1), alignment))

    items_table.setStyle(TableStyle(table_style))
    elements.append(items_table)

    return elements


def _create_equity_items_table(
    template: InvoiceTemplateConfig, invoice: Invoice, available_width: float
) -> List:
    """
    Create the equity items table section.

    Args:
        template: Template configuration
        invoice: Invoice object
        available_width: Available width for the table

    Returns:
        List of flowable elements
    """
    elements = []

    # Filter out equity items
    equity_items = [item for item in invoice.items if item.has_equity_component]
    if not equity_items:
        return elements

    # Create section title
    section_title_style = _create_paragraph_style(
        "equity_section_title",
        font_name=template.items_table.header_style.text_style.font.family,
        font_size=template.items_table.header_style.text_style.font.size + 2,
        text_color=template.items_table.header_style.text_style.font.color.to_rgb(),
        alignment="LEFT",
        bold=True,
    )

    elements.append(Paragraph("Equity Compensation", section_title_style))
    elements.append(Spacer(1, 10))

    # Create styles
    header_style = _create_paragraph_style(
        "equity_header",
        font_name=template.items_table.header_style.text_style.font.family,
        font_size=template.items_table.header_style.text_style.font.size,
        text_color=template.items_table.header_style.text_style.font.color.to_rgb(),
        alignment="LEFT",  # Will be overridden by column alignment
        bold=template.items_table.header_style.text_style.font.bold,
    )

    row_style = _create_paragraph_style(
        "equity_row",
        font_name=template.items_table.row_style.text_style.font.family,
        font_size=template.items_table.row_style.text_style.font.size,
        text_color=template.items_table.row_style.text_style.font.color.to_rgb(),
        alignment="LEFT",  # Will be overridden by column alignment
    )

    # Create table data
    table_data = []

    # Define equity table columns
    equity_columns = [
        {"name": "description", "title": "Description", "width": 50, "align": "left"},
        {"name": "quantity", "title": "Hours", "width": 15, "align": "right"},
        {
            "name": "equity_amount",
            "title": "Equity Amount",
            "width": 35,
            "align": "right",
        },
    ]

    # Add header row
    header_row = []
    for column in equity_columns:
        header_cell = Paragraph(column["title"], header_style)
        header_row.append(header_cell)
    table_data.append(header_row)

    # Add item rows
    for item in equity_items:
        row = []
        for column in equity_columns:
            column_name = column["name"]
            if column_name == "description":
                cell_text = item.description
                if template.items_table.show_category and item.category:
                    cell_text = f"<b>{item.category}</b><br/>{cell_text}"
                cell = Paragraph(cell_text, row_style)
            elif column_name == "quantity":
                cell = Paragraph(f"{float(item.quantity):.2f}", row_style)
            elif column_name == "equity_amount":
                equity_text = _format_equity(item.equity_quantity, item.equity_type)
                cell = Paragraph(equity_text, row_style)
            else:
                cell = Paragraph("", row_style)
            row.append(cell)
        table_data.append(row)

    # Calculate column widths
    col_widths = []
    total_width_units = sum(col["width"] for col in equity_columns)

    for column in equity_columns:
        width_percent = column["width"] / total_width_units
        col_widths.append(available_width * width_percent)

    # Create table
    equity_table = Table(table_data, colWidths=col_widths)

    # Apply table styles (similar to items table)
    table_style = [
        # Header style
        (
            "BACKGROUND",
            (0, 0),
            (-1, 0),
            (
                colors.Color(
                    *[
                        c / 255
                        for c in template.items_table.header_style.background_color.to_rgb()
                    ]
                )
                if template.items_table.header_style.background_color
                else colors.white
            ),
        ),
        (
            "GRID",
            (0, 0),
            (-1, -1),
            template.items_table.header_style.border.width,
            colors.Color(
                *[
                    c / 255
                    for c in template.items_table.header_style.border.color.to_rgb()
                ]
            ),
        ),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, 0), template.items_table.header_style.padding.top),
        (
            "RIGHTPADDING",
            (0, 0),
            (-1, 0),
            template.items_table.header_style.padding.right,
        ),
        (
            "BOTTOMPADDING",
            (0, 0),
            (-1, 0),
            template.items_table.header_style.padding.bottom,
        ),
        (
            "LEFTPADDING",
            (0, 0),
            (-1, 0),
            template.items_table.header_style.padding.left,
        ),
    ]

    # Row styles
    for i in range(1, len(table_data)):
        # Alternate row background if specified
        if template.items_table.alternate_row_style and i % 2 == 0:
            table_style.append(
                (
                    "BACKGROUND",
                    (0, i),
                    (-1, i),
                    (
                        colors.Color(
                            *[
                                c / 255
                                for c in template.items_table.alternate_row_style.background_color.to_rgb()
                            ]
                        )
                        if template.items_table.alternate_row_style.background_color
                        else colors.white
                    ),
                )
            )

        # Add padding
        table_style.extend(
            [
                (
                    "TOPPADDING",
                    (0, i),
                    (-1, i),
                    template.items_table.row_style.padding.top,
                ),
                (
                    "RIGHTPADDING",
                    (0, i),
                    (-1, i),
                    template.items_table.row_style.padding.right,
                ),
                (
                    "BOTTOMPADDING",
                    (0, i),
                    (-1, i),
                    template.items_table.row_style.padding.bottom,
                ),
                (
                    "LEFTPADDING",
                    (0, i),
                    (-1, i),
                    template.items_table.row_style.padding.left,
                ),
            ]
        )

    # Apply column alignments
    for i, column in enumerate(equity_columns):
        alignment = column.get("align", "left").upper()
        table_style.append(("ALIGN", (i, 0), (i, -1), alignment))

    equity_table.setStyle(TableStyle(table_style))
    elements.append(equity_table)

    # Add equity notes
    elements.append(Spacer(1, 10))
    equity_notes_style = _create_paragraph_style(
        "equity_notes",
        font_name="Helvetica",  # Use base font name, let the function handle the suffix
        font_size=template.totals.style.text_style.font.size - 1,
        text_color=template.totals.style.text_style.font.color.to_rgb(),
        alignment="LEFT",
        italic=True,
    )
    notes = "Note: Equity compensation is issued according to contract terms and is not included in the cash total."
    elements.append(Paragraph(notes, equity_notes_style))

    return elements


def _create_totals_section(template: InvoiceTemplateConfig, invoice: Invoice) -> List:
    """
    Create the totals section.

    Args:
        template: Template configuration
        invoice: Invoice object

    Returns:
        List of flowable elements
    """
    elements = []

    # Create styles
    label_style = _create_paragraph_style(
        "totals_label",
        font_name=template.totals.style.text_style.font.family,
        font_size=template.totals.style.text_style.font.size,
        text_color=template.totals.style.text_style.font.color.to_rgb(),
        alignment="RIGHT",
        bold=True,
    )

    value_style = _create_paragraph_style(
        "totals_value",
        font_name=template.totals.style.text_style.font.family,
        font_size=template.totals.style.text_style.font.size,
        text_color=template.totals.style.text_style.font.color.to_rgb(),
        alignment="RIGHT",
        bold=True,
    )

    # Create tables for each total
    totals_data = []

    # Subtotal
    if template.totals.show_subtotal:
        totals_data.append(
            [
                Paragraph("Subtotal:", label_style),
                Paragraph(_format_currency(invoice.subtotal), value_style),
            ]
        )

    # Tax
    if (
        template.totals.show_tax
        and invoice.tax_amount is not None
        and invoice.tax_amount > 0
    ):
        tax_label = f"Tax ({float(invoice.tax_rate)}%):"
        totals_data.append(
            [
                Paragraph(tax_label, label_style),
                Paragraph(_format_currency(invoice.tax_amount), value_style),
            ]
        )

    # Add horizontal rule
    elements.append(
        HRFlowable(width="100%", thickness=1, color=colors.black, spaceAfter=10)
    )

    # Total
    if template.totals.show_total:
        totals_data.append(
            [
                Paragraph("Total Due:", label_style),
                Paragraph(_format_currency(invoice.total_amount), value_style),
            ]
        )

    # Create totals table
    if totals_data:
        totals_table = Table(
            totals_data, colWidths=[100, 100], hAlign="RIGHT", spaceAfter=10
        )
        totals_table.setStyle(
            TableStyle(
                [
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("TOPPADDING", (0, 0), (-1, -1), template.totals.style.padding.top),
                    (
                        "RIGHTPADDING",
                        (0, 0),
                        (-1, -1),
                        template.totals.style.padding.right,
                    ),
                    (
                        "BOTTOMPADDING",
                        (0, 0),
                        (-1, -1),
                        template.totals.style.padding.bottom,
                    ),
                    (
                        "LEFTPADDING",
                        (0, 0),
                        (-1, -1),
                        template.totals.style.padding.left,
                    ),
                ]
            )
        )
        elements.append(totals_table)

    return elements


def _create_footer_section(template: InvoiceTemplateConfig) -> List:
    """
    Create the footer section.

    Args:
        template: Template configuration

    Returns:
        List of flowable elements
    """
    elements = []

    # Create styles
    footer_style = _create_paragraph_style(
        "footer",
        font_name=template.footer.style.text_style.font.family,
        font_size=template.footer.style.text_style.font.size,
        text_color=template.footer.style.text_style.font.color.to_rgb(),
        alignment=_get_alignment(template.footer.style.text_style.alignment),
    )

    # Create footer text - replace \n with <br/> for proper line breaks
    formatted_footer_text = template.footer.text.replace("\\n", "<br/>")
    footer_text = Paragraph(formatted_footer_text, footer_style)

    # Create footer table
    footer_table = Table([[footer_text]], colWidths=["100%"])
    footer_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), template.footer.style.padding.top),
                ("RIGHTPADDING", (0, 0), (-1, -1), template.footer.style.padding.right),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    template.footer.style.padding.bottom,
                ),
                ("LEFTPADDING", (0, 0), (-1, -1), template.footer.style.padding.left),
            ]
        )
    )

    elements.append(footer_table)
    return elements
