"""
CLI utility functions for InvoiceAgent.

This module provides helper functions for formatting CLI output,
displaying tables, and other UI enhancements.
"""

import sys
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

# Create console for rich output
console = Console()


def print_success(message: str) -> None:
    """
    Print a success message with green color.
    
    Args:
        message: The message to print
    """
    console.print(f"[bold green]✓[/bold green] {message}")


def print_error(message: str) -> None:
    """
    Print an error message with red color.
    
    Args:
        message: The message to print
    """
    console.print(f"[bold red]✗[/bold red] {message}")


def print_warning(message: str) -> None:
    """
    Print a warning message with yellow color.
    
    Args:
        message: The message to print
    """
    console.print(f"[bold yellow]![/bold yellow] {message}")


def print_info(message: str) -> None:
    """
    Print an info message with blue color.
    
    Args:
        message: The message to print
    """
    console.print(f"[bold blue]i[/bold blue] {message}")


def format_currency(amount: Union[float, int]) -> str:
    """
    Format a number as currency.
    
    Args:
        amount: The amount to format
        
    Returns:
        Formatted currency string
    """
    return f"${amount:.2f}"


def format_date(date_obj: Union[date, datetime, str]) -> str:
    """
    Format a date consistently.
    
    Args:
        date_obj: The date to format
        
    Returns:
        Formatted date string
    """
    if isinstance(date_obj, str):
        try:
            date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()
        except ValueError:
            return date_obj
    
    if isinstance(date_obj, datetime):
        date_obj = date_obj.date()
        
    return date_obj.strftime("%Y-%m-%d")


def print_table(
    columns: List[str], 
    data: List[List[Any]], 
    title: Optional[str] = None,
    caption: Optional[str] = None
) -> None:
    """
    Print a formatted table.
    
    Args:
        columns: List of column names
        data: List of rows, where each row is a list of values
        title: Optional title for the table
        caption: Optional caption for the table
    """
    table = Table(title=title, caption=caption)
    
    # Add columns
    for column in columns:
        table.add_column(column)
    
    # Add rows
    for row in data:
        # Convert all values to strings
        str_row = [str(cell) if cell is not None else "" for cell in row]
        table.add_row(*str_row)
    
    console.print(table)


def print_entity(entity: Dict[str, Any], title: Optional[str] = None) -> None:
    """
    Print an entity (client, project, etc.) in a formatted panel.
    
    Args:
        entity: Dictionary of entity attributes
        title: Optional title for the panel
    """
    # Format the entity as a string
    lines = []
    for key, value in entity.items():
        # Skip internal attributes
        if key.startswith("_"):
            continue
            
        # Format dates
        if isinstance(value, (date, datetime)):
            value = format_date(value)
            
        # Format currency
        if key in ["hourly_rate", "amount", "rate", "total_amount", "subtotal", "tax_amount"]:
            if value is not None:
                value = format_currency(float(value))
        
        # Format the line
        lines.append(f"{key.replace('_', ' ').title()}: {value}")
    
    # Create a panel with the formatted text
    panel = Panel("\n".join(lines), title=title)
    console.print(panel)


def confirm_action(message: str, default: bool = False) -> bool:
    """
    Ask for confirmation with colored output.
    
    Args:
        message: The confirmation message
        default: Default value if user just presses Enter
        
    Returns:
        True if confirmed, False otherwise
    """
    return click.confirm(Text(message, style="bold yellow"), default=default)


def exit_with_error(message: str, code: int = 1) -> None:
    """
    Print an error message and exit with the given code.
    
    Args:
        message: The error message
        code: Exit code
    """
    print_error(message)
    sys.exit(code)


def print_section_header(title: str) -> None:
    """
    Print a section header with a horizontal rule.
    
    Args:
        title: The section title
    """
    console.print(f"\n[bold]{title}[/bold]")
    console.print("=" * 80)


def print_subsection_header(title: str) -> None:
    """
    Print a subsection header.
    
    Args:
        title: The subsection title
    """
    console.print(f"\n[bold]{title}[/bold]")
    console.print("-" * 80) 