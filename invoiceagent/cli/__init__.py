"""
Command-line interface for InvoiceAgent.
"""

import click

from invoiceagent.cli.db_commands import db_commands


@click.group()
def cli():
    """InvoiceAgent: AI-powered invoicing for independent contractor work."""
    pass


@cli.command()
def version():
    """Display the current version of InvoiceAgent."""
    from importlib.metadata import version as get_version
    try:
        version = get_version("invoiceagent")
        click.echo(f"InvoiceAgent v{version}")
    except:  # noqa: E722
        click.echo("InvoiceAgent development version")


# Add subcommands
cli.add_command(db_commands)


def main():
    """Main entry point for the application."""
    cli()
