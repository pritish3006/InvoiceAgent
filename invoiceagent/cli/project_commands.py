"""Project management CLI commands for InvoiceAgent."""

import sys
from datetime import date, datetime

import click
from sqlalchemy.exc import IntegrityError

from invoiceagent.db.engine import get_session
from invoiceagent.db.models import Project
from invoiceagent.db.repositories.client import ClientRepository
from invoiceagent.db.repositories.project import ProjectRepository


@click.group(name="project")
def project_commands():
    """Project management commands."""
    pass


@project_commands.command(name="add")
@click.option("--name", prompt="Project name", help="Name of the project")
@click.option("--client-id", prompt="Client ID", type=int, help="ID of the client")
@click.option("--description", prompt=True, help="Description of the project")
@click.option("--hourly-rate", prompt="Hourly rate", type=float, help="Hourly rate for the project")
@click.option("--start-date", type=click.DateTime(formats=["%Y-%m-%d"]), help="Start date (YYYY-MM-DD)")
@click.option("--end-date", type=click.DateTime(formats=["%Y-%m-%d"]), help="End date (YYYY-MM-DD)")
def add_project(name, client_id, description, hourly_rate, start_date, end_date):
    """Add a new project to the database."""
    project_repo = ProjectRepository()
    client_repo = ClientRepository()
    
    # Create project data
    project_data = {
        "name": name,
        "client_id": client_id,
        "description": description,
        "hourly_rate": hourly_rate,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    # Add optional dates if provided
    if start_date:
        project_data["start_date"] = start_date.date()
    if end_date:
        project_data["end_date"] = end_date.date()
    
    # Add project to database
    try:
        with get_session() as session:
            # Check if client exists
            client = client_repo.get_by_id(session, client_id)
            if not client:
                click.echo(f"Error: No client found with ID: {client_id}")
                sys.exit(1)
            
            # Check if project with same name already exists for this client
            existing_project = project_repo.get_by_name(session, name)
            if existing_project and existing_project.client_id == client_id:
                click.echo(f"Error: Project with name '{name}' already exists for client '{client.name}'.")
                sys.exit(1)
            
            # Create new project
            project = project_repo.create(session, **project_data)
            click.echo(f"Project '{name}' added successfully with ID: {project.id}")
    except IntegrityError:
        click.echo("Error: Failed to add project due to database constraint violation.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@project_commands.command(name="list")
@click.option("--client-id", type=int, help="Filter projects by client ID")
@click.option("--active-only", is_flag=True, help="Show only active projects")
def list_projects(client_id, active_only):
    """List projects in the database."""
    project_repo = ProjectRepository()
    client_repo = ClientRepository()
    
    try:
        with get_session() as session:
            # Get projects based on filters
            if client_id:
                # Check if client exists
                client = client_repo.get_by_id(session, client_id)
                if not client:
                    click.echo(f"Error: No client found with ID: {client_id}")
                    sys.exit(1)
                
                projects = project_repo.get_by_client_id(session, client_id)
                if active_only:
                    projects = [p for p in projects if p.is_active]
                
                click.echo(f"\nProjects for client '{client.name}':")
            else:
                projects = project_repo.get_all(session)
                if active_only:
                    projects = [p for p in projects if p.is_active]
                
                click.echo("\nAll Projects:")
            
            if not projects:
                click.echo("No projects found.")
                return
            
            click.echo("=" * 80)
            
            for project in projects:
                client = client_repo.get_by_id(session, project.client_id)
                click.echo(f"ID: {project.id}")
                click.echo(f"Name: {project.name}")
                click.echo(f"Client: {client.name} (ID: {client.id})")
                click.echo(f"Hourly Rate: ${project.hourly_rate:.2f}")
                click.echo(f"Status: {'Active' if project.is_active else 'Inactive'}")
                
                if project.start_date:
                    click.echo(f"Start Date: {project.start_date}")
                if project.end_date:
                    click.echo(f"End Date: {project.end_date}")
                
                click.echo("-" * 80)
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@project_commands.command(name="get")
@click.argument("project_id", type=int)
def get_project(project_id):
    """Get details for a specific project."""
    project_repo = ProjectRepository()
    client_repo = ClientRepository()
    
    try:
        with get_session() as session:
            project = project_repo.get_by_id(session, project_id)
            
            if not project:
                click.echo(f"No project found with ID: {project_id}")
                sys.exit(1)
            
            client = client_repo.get_by_id(session, project.client_id)
            
            click.echo("\nProject Details:")
            click.echo("=" * 80)
            click.echo(f"ID: {project.id}")
            click.echo(f"Name: {project.name}")
            click.echo(f"Client: {client.name} (ID: {client.id})")
            click.echo(f"Description: {project.description}")
            click.echo(f"Hourly Rate: ${project.hourly_rate:.2f}")
            click.echo(f"Status: {'Active' if project.is_active else 'Inactive'}")
            
            if project.start_date:
                click.echo(f"Start Date: {project.start_date}")
            if project.end_date:
                click.echo(f"End Date: {project.end_date}")
            
            click.echo(f"Created: {project.created_at}")
            click.echo(f"Updated: {project.updated_at}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@project_commands.command(name="update")
@click.argument("project_id", type=int)
@click.option("--name", help="New name for the project")
@click.option("--description", help="New description")
@click.option("--hourly-rate", type=float, help="New hourly rate")
@click.option("--start-date", type=click.DateTime(formats=["%Y-%m-%d"]), help="New start date (YYYY-MM-DD)")
@click.option("--end-date", type=click.DateTime(formats=["%Y-%m-%d"]), help="New end date (YYYY-MM-DD)")
@click.option("--active/--inactive", help="Set project active or inactive")
def update_project(project_id, name, description, hourly_rate, start_date, end_date, active):
    """Update an existing project."""
    project_repo = ProjectRepository()
    
    # Collect update data (only non-None values)
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if hourly_rate is not None:
        update_data["hourly_rate"] = hourly_rate
    if start_date is not None:
        update_data["start_date"] = start_date.date()
    if end_date is not None:
        update_data["end_date"] = end_date.date()
    if active is not None:
        update_data["is_active"] = active
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
    else:
        click.echo("No update parameters provided.")
        sys.exit(1)
    
    try:
        with get_session() as session:
            # Check if project exists
            project = project_repo.get_by_id(session, project_id)
            if not project:
                click.echo(f"No project found with ID: {project_id}")
                sys.exit(1)
            
            # Update project
            updated_project = project_repo.update(session, project_id, update_data)
            click.echo(f"Project with ID {project_id} updated successfully.")
    except IntegrityError:
        click.echo("Error: Failed to update project due to database constraint violation.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@project_commands.command(name="delete")
@click.argument("project_id", type=int)
@click.option("--force", is_flag=True, help="Force deletion without confirmation")
def delete_project(project_id, force):
    """Delete a project from the database."""
    project_repo = ProjectRepository()
    
    try:
        with get_session() as session:
            # Check if project exists
            project = project_repo.get_by_id(session, project_id)
            if not project:
                click.echo(f"No project found with ID: {project_id}")
                sys.exit(1)
            
            # Confirm deletion
            if not force:
                if not click.confirm(f"Are you sure you want to delete project '{project.name}'?"):
                    click.echo("Deletion cancelled.")
                    return
            
            # Check if project has work logs
            if project.work_logs and not force:
                click.echo(f"Project has {len(project.work_logs)} work logs. Use --force to delete anyway.")
                sys.exit(1)
            
            # Delete project
            project_repo.delete(session, project_id)
            click.echo(f"Project '{project.name}' deleted successfully.")
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@project_commands.command(name="search")
@click.argument("name_pattern")
def search_projects(name_pattern):
    """Search for projects by name pattern."""
    project_repo = ProjectRepository()
    client_repo = ClientRepository()
    
    try:
        with get_session() as session:
            # This is a simple implementation - in a real app, we'd add a search_by_name method to ProjectRepository
            projects = session.query(Project).filter(Project.name.like(f"%{name_pattern}%")).all()
            
            if not projects:
                click.echo(f"No projects found matching pattern: {name_pattern}")
                return
            
            click.echo(f"\nFound {len(projects)} projects matching '{name_pattern}':")
            click.echo("=" * 80)
            
            for project in projects:
                client = client_repo.get_by_id(session, project.client_id)
                click.echo(f"ID: {project.id}")
                click.echo(f"Name: {project.name}")
                click.echo(f"Client: {client.name} (ID: {client.id})")
                click.echo(f"Hourly Rate: ${project.hourly_rate:.2f}")
                click.echo(f"Status: {'Active' if project.is_active else 'Inactive'}")
                click.echo("-" * 80)
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1) 