"""
Main CLI entry point for InvoiceAgent.

This module provides the main command-line interface for the application.
"""

import asyncio
import os
import sys

import click
from rich.console import Console

from invoiceagent.ai.ollama_client import OllamaClient, OllamaConnectionError
from invoiceagent.cli.ai_commands import ai_commands
from invoiceagent.cli.client_commands import client_commands
from invoiceagent.cli.db_commands import db_commands
from invoiceagent.cli.invoice_commands import invoice_commands
from invoiceagent.cli.project_commands import project_commands
from invoiceagent.cli.utils import (
    print_error,
    print_info,
    print_section_header,
    print_success,
)
from invoiceagent.cli.work_log_commands import work_log_commands
from invoiceagent.config import get_config

# Create console for rich output
console = Console()


@click.group()
@click.version_option()
def cli():
    """InvoiceAgent - AI-powered invoice generation tool."""
    pass


# Register command groups
cli.add_command(db_commands)
cli.add_command(client_commands)
cli.add_command(project_commands)
cli.add_command(work_log_commands)
cli.add_command(ai_commands)
cli.add_command(invoice_commands)


async def check_ollama():
    """Check if Ollama is running and responding."""
    client = OllamaClient()
    try:
        status = await client._check_ollama_status()
        if status:
            print_success("Ollama is running and responding")
        else:
            print_error("Ollama is not responding")
            print_info("Make sure Ollama is running")
    except OllamaConnectionError:
        print_error("Failed to connect to Ollama")
        print_info("Make sure Ollama is running on http://localhost:11434")
    finally:
        await client.close()


@cli.command(name="status")
def status():
    """Check the status of the application and connections."""
    print_section_header("InvoiceAgent Status")

    # Check if database exists
    db_path = os.path.expanduser("~/.invoiceagent/invoiceagent.db")

    if os.path.exists(db_path):
        print_success(f"Database found at {db_path}")
    else:
        print_error(f"Database not found at {db_path}")
        print_info("Run 'invoiceagent db init' to create the database")

    # Check Ollama connection
    print_info("Checking Ollama connection...")
    asyncio.run(check_ollama())


def main():
    """Entry point for the CLI."""
    try:
        cli()
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
