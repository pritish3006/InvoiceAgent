"""
Main CLI entry point for InvoiceAgent.

This module provides the main command-line interface for the application.
"""

import click

from invoiceagent.cli.ai_commands import ai_commands
from invoiceagent.cli.client_commands import client_commands
from invoiceagent.cli.db_commands import db_commands
from invoiceagent.cli.project_commands import project_commands
from invoiceagent.cli.utils import print_error, print_info, print_success
from invoiceagent.cli.work_log_commands import work_log_commands
from invoiceagent.config import get_config


@click.group()
@click.version_option()
def cli():
    """InvoiceAgent - AI-powered invoice generation tool."""
    pass


# Add command groups
cli.add_command(db_commands)
cli.add_command(client_commands)
cli.add_command(project_commands)
cli.add_command(work_log_commands)
cli.add_command(ai_commands)


@cli.command(name="status")
def status():
    """Show the current status of InvoiceAgent."""
    config = get_config()
    
    print_info("InvoiceAgent Status")
    print_info("-------------------")
    print_info(f"Database path: {config.database_path}")
    
    # Check if Ollama is running
    import asyncio
    from invoiceagent.ai.ollama_client import OllamaClient
    
    async def check_ollama():
        client = OllamaClient()
        if await client._check_ollama_status():
            print_success("Ollama: Running")
        else:
            print_error("Ollama: Not running")
    
    asyncio.run(check_ollama())


if __name__ == "__main__":
    cli() 