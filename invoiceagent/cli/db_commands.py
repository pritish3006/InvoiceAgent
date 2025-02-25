"""Database management CLI commands for InvoiceAgent."""
import os
import sys
import subprocess
from pathlib import Path

import click
from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, MetaData

from invoiceagent.db.engine import DEFAULT_DB_PATH, get_engine, init_db
from invoiceagent.db.models import Base


@click.group(name="db")
def db_commands():
    """Database management commands."""
    pass


@db_commands.command(name="init")
@click.option(
    "--db-path",
    default=None,
    help="Path to the SQLite database file (default: $HOME/.invoiceagent/invoiceagent.db)",
)
def init_database(db_path):
    """Initialize the database schema."""
    db_path = db_path or DEFAULT_DB_PATH
    
    # Ensure the directory exists
    db_dir = os.path.dirname(db_path)
    os.makedirs(db_dir, exist_ok=True)
    
    click.echo(f"Initializing database at: {db_path}")
    
    # Check if the database file exists
    if os.path.exists(db_path):
        if not click.confirm("Database already exists. Do you want to recreate it?"):
            click.echo("Aborted.")
            sys.exit(1)
        os.remove(db_path)
    
    # Initialize the database
    engine = get_engine(db_path)
    init_db(engine)
    
    click.echo("Database initialized successfully.")


@db_commands.command(name="upgrade")
@click.option(
    "--db-path",
    default=None,
    help="Path to the SQLite database file (default: $HOME/.invoiceagent/invoiceagent.db)",
)
@click.option(
    "--revision",
    default="head",
    help="Revision to upgrade to (default: head)",
)
def upgrade_database(db_path, revision):
    """Upgrade the database schema to the specified revision."""
    db_path = db_path or DEFAULT_DB_PATH
    
    if not os.path.exists(db_path):
        click.echo(f"Database file not found at: {db_path}")
        if click.confirm("Do you want to create a new database?"):
            init_database(db_path)
        else:
            click.echo("Aborted.")
            sys.exit(1)
    
    click.echo(f"Upgrading database at: {db_path} to revision: {revision}")
    
    # Set the database path in the environment
    os.environ["INVOICEAGENT_DB_PATH"] = str(db_path)
    
    # Get the alembic.ini path
    project_root = Path(__file__).parent.parent.parent
    alembic_ini = project_root / "alembic.ini"
    
    # Create the Alembic configuration
    alembic_cfg = Config(str(alembic_ini))
    
    # Run the upgrade
    command.upgrade(alembic_cfg, revision)
    
    click.echo("Database upgrade completed successfully.")


@db_commands.command(name="create-migration")
@click.argument("message")
def create_migration(message):
    """Create a new database migration."""
    click.echo(f"Creating migration: {message}")
    
    # Get the alembic.ini path
    project_root = Path(__file__).parent.parent.parent
    alembic_ini = project_root / "alembic.ini"
    
    # Create the Alembic configuration
    alembic_cfg = Config(str(alembic_ini))
    
    # Run the revision command
    command.revision(alembic_cfg, message=message, autogenerate=True)
    
    click.echo("Migration created successfully.")


@db_commands.command(name="show-migrations")
def show_migrations():
    """Show all available migrations."""
    click.echo("Available migrations:")
    
    # Get the alembic.ini path
    project_root = Path(__file__).parent.parent.parent
    alembic_ini = project_root / "alembic.ini"
    
    # Run the history command
    result = subprocess.run(
        ["alembic", "-c", str(alembic_ini), "history"],
        capture_output=True,
        text=True,
    )
    
    click.echo(result.stdout)


@db_commands.command(name="verify-schema")
@click.option(
    "--db-path",
    default=None,
    help="Path to the SQLite database file (default: $HOME/.invoiceagent/invoiceagent.db)",
)
def verify_schema(db_path):
    """Verify that the database schema matches the expected schema from the models."""
    db_path = db_path or DEFAULT_DB_PATH
    
    if not os.path.exists(db_path):
        click.echo(f"Database file not found at: {db_path}")
        sys.exit(1)
    
    click.echo(f"Verifying database schema at: {db_path}")
    
    # Get the engine and inspector
    engine = get_engine(db_path)
    inspector = inspect(engine)
    
    # Get the actual tables in the database
    actual_tables = set(inspector.get_table_names())
    
    # Get the expected tables from the models
    metadata = Base.metadata
    expected_tables = set(metadata.tables.keys())
    
    # Compare the tables
    missing_tables = expected_tables - actual_tables
    extra_tables = actual_tables - expected_tables - {'alembic_version'}  # Exclude alembic_version
    
    if missing_tables:
        click.echo(f"Missing tables: {', '.join(missing_tables)}")
    
    if extra_tables:
        click.echo(f"Extra tables: {', '.join(extra_tables)}")
    
    if not missing_tables and not extra_tables:
        click.echo("All expected tables are present in the database.")
    
    # For each table, verify the columns
    for table_name in expected_tables & actual_tables:
        click.echo(f"\nVerifying columns for table: {table_name}")
        
        # Get the actual columns
        actual_columns = {col['name']: col for col in inspector.get_columns(table_name)}
        
        # Get the expected columns
        expected_columns = {col.name: col for col in metadata.tables[table_name].columns}
        
        # Compare the columns
        missing_columns = set(expected_columns.keys()) - set(actual_columns.keys())
        extra_columns = set(actual_columns.keys()) - set(expected_columns.keys())
        
        if missing_columns:
            click.echo(f"  Missing columns: {', '.join(missing_columns)}")
        
        if extra_columns:
            click.echo(f"  Extra columns: {', '.join(extra_columns)}")
        
        if not missing_columns and not extra_columns:
            click.echo("  All expected columns are present.")
    
    # Check for foreign keys
    for table_name in expected_tables & actual_tables:
        click.echo(f"\nVerifying foreign keys for table: {table_name}")
        
        # Get the actual foreign keys
        actual_fks = inspector.get_foreign_keys(table_name)
        actual_fk_set = {(fk['referred_table'], tuple(fk['constrained_columns'])) for fk in actual_fks}
        
        # Get the expected foreign keys
        expected_fks = []
        for fk in metadata.tables[table_name].foreign_keys:
            referred_table = fk.column.table.name
            constrained_column = fk.parent.name
            expected_fks.append((referred_table, (constrained_column,)))
        expected_fk_set = set(expected_fks)
        
        # Compare the foreign keys
        missing_fks = expected_fk_set - actual_fk_set
        extra_fks = actual_fk_set - expected_fk_set
        
        if missing_fks:
            click.echo(f"  Missing foreign keys: {missing_fks}")
        
        if extra_fks:
            click.echo(f"  Extra foreign keys: {extra_fks}")
        
        if not missing_fks and not extra_fks:
            click.echo("  All expected foreign keys are present.")
    
    click.echo("\nSchema verification completed.") 