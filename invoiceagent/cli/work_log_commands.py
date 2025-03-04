"""Work log management CLI commands for InvoiceAgent."""

import asyncio
import sys
from datetime import date, datetime, timedelta

import click
from sqlalchemy.exc import IntegrityError

from invoiceagent.ai import WorkLogProcessor
from invoiceagent.db.engine import get_session
from invoiceagent.db.models import WorkLog
from invoiceagent.db.repositories.client import ClientRepository
from invoiceagent.db.repositories.project import ProjectRepository
from invoiceagent.db.repositories.work_log import WorkLogRepository
from invoiceagent.cli.utils import print_success, print_error, print_warning


@click.group(name="log")
def work_log_commands():
    """Work log management commands."""
    pass


@work_log_commands.command(name="add")
@click.option("--project-id", type=int, help="ID of the project")
@click.option("--date", type=click.DateTime(formats=["%Y-%m-%d"]), help="Work date (YYYY-MM-DD)")
@click.option("--hours", type=float, help="Hours spent")
@click.option("--description", help="Description of work performed")
@click.option("--category", help="Category of work")
@click.option("--billable/--non-billable", default=True, help="Whether the work is billable")
@click.option("--free-form", help="Free-form text description to be processed by AI")
def add_work_log(project_id, date, hours, description, category, billable, free_form):
    """Add a new work log entry."""
    async def _add_work_log():
        try:
            if free_form:
                # Process free-form text using AI
                processor = WorkLogProcessor()
                async with processor.client:  # Use async context manager
                    result = await processor.process_free_form_log(free_form)
                    
                    # Display the processed result
                    print("Processed free-form entry:")
                    print(f"Project: {result.project}")
                    print(f"Client: {result.client}")
                    print(f"Date: {result.work_date}")
                    print(f"Hours: {result.hours}")
                    print(f"Description: {result.description}")
                    print(f"Category: {result.category}")
                    print(f"Billable: {result.billable}")
                    
                    # Confirm with user
                    if not click.confirm("Is this correct?", default=False):
                        print_warning("Cancelled.")
                        return
                    
                    # Get project ID from client and project name
                    with get_session() as session:
                        # First find the client
                        client_repo = ClientRepository()
                        client = client_repo.get_by_name(session, result.client)
                        if not client:
                            print_error(f"Client not found: {result.client}")
                            return
                            
                        # Then find the project
                        project_repo = ProjectRepository()
                        project = project_repo.get_by_name(session, result.project)
                        if not project:
                            print_error(f"Project not found: {result.project}")
                            return
                            
                        # Create the work log
                        work_log_repo = WorkLogRepository()
                        work_log = work_log_repo.create(
                            session,
                            project_id=project.id,
                            work_date=result.work_date,
                            hours=result.hours,
                            description=result.description,
                            category=result.category,
                            billable=result.billable
                        )
                        
                        session.commit()
                        print_success(f"Work log added successfully with ID: {work_log.id}")
                        
            else:
                # Handle structured input
                if not all([project_id, date, hours, description]):
                    print_error("All fields are required when not using free-form input.")
                    return
                    
                with get_session() as session:
                    work_log_repo = WorkLogRepository()
                    work_log = work_log_repo.create(
                        session,
                        project_id=project_id,
                        work_date=date.date(),
                        hours=hours,
                        description=description,
                        category=category,
                        billable=billable
                    )
                    
                    session.commit()
                    print_success(f"Work log added successfully with ID: {work_log.id}")
                    
        except Exception as e:
            print_error(f"Error adding work log: {str(e)}")
            raise
    
    # Run the async function
    asyncio.run(_add_work_log())


@work_log_commands.command(name="list")
@click.option("--project-id", type=int, help="Filter by project ID")
@click.option("--client-id", type=int, help="Filter by client ID")
@click.option("--start-date", type=click.DateTime(formats=["%Y-%m-%d"]), help="Start date (YYYY-MM-DD)")
@click.option("--end-date", type=click.DateTime(formats=["%Y-%m-%d"]), help="End date (YYYY-MM-DD)")
@click.option("--unbilled-only", is_flag=True, help="Show only unbilled work logs")
@click.option("--billable-only", is_flag=True, help="Show only billable work logs")
def list_work_logs(project_id, client_id, start_date, end_date, unbilled_only, billable_only):
    """List work logs in the database."""
    work_log_repo = WorkLogRepository()
    project_repo = ProjectRepository()
    client_repo = ClientRepository()
    
    # Default to current month if no dates provided
    if not start_date and not end_date:
        today = date.today()
        start_date = date(today.year, today.month, 1)
        end_date = (date(today.year, today.month + 1, 1) if today.month < 12 
                   else date(today.year + 1, 1, 1)) - timedelta(days=1)
    elif start_date and not end_date:
        end_date = date.today()
    elif end_date and not start_date:
        start_date = end_date.replace(day=1)
    
    # Convert datetime to date if needed
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    
    try:
        with get_session() as session:
            # Apply filters
            if unbilled_only:
                work_logs = work_log_repo.get_unbilled(session)
                if start_date and end_date:
                    work_logs = [wl for wl in work_logs 
                                if start_date <= wl.work_date <= end_date]
            elif project_id:
                # Check if project exists
                project = project_repo.get_by_id(session, project_id)
                if not project:
                    click.echo(f"Error: No project found with ID: {project_id}")
                    sys.exit(1)
                
                if start_date and end_date:
                    # Filter by project and date range
                    work_logs = session.query(WorkLog).filter(
                        WorkLog.project_id == project_id,
                        WorkLog.work_date >= start_date,
                        WorkLog.work_date <= end_date
                    ).order_by(WorkLog.work_date).all()
                else:
                    # Filter by project only
                    work_logs = work_log_repo.get_by_project_id(session, project_id)
            elif client_id:
                # Check if client exists
                client = client_repo.get_by_id(session, client_id)
                if not client:
                    click.echo(f"Error: No client found with ID: {client_id}")
                    sys.exit(1)
                
                # Get work logs for client
                work_logs = work_log_repo.get_by_client_id(session, client_id)
                if start_date and end_date:
                    work_logs = [wl for wl in work_logs 
                                if start_date <= wl.work_date <= end_date]
            else:
                # Get work logs by date range
                work_logs = work_log_repo.get_by_date_range(session, start_date, end_date)
            
            # Apply billable filter if needed
            if billable_only:
                work_logs = [wl for wl in work_logs if wl.billable]
            
            if not work_logs:
                click.echo("No work logs found matching the criteria.")
                return
            
            # Display work logs
            total_hours = 0
            billable_hours = 0
            
            click.echo("\nWork Logs:")
            if start_date and end_date:
                click.echo(f"Period: {start_date} to {end_date}")
            click.echo("=" * 80)
            
            for work_log in work_logs:
                project = project_repo.get_by_id(session, work_log.project_id)
                client = client_repo.get_by_id(session, project.client_id)
                
                click.echo(f"ID: {work_log.id}")
                click.echo(f"Date: {work_log.work_date}")
                click.echo(f"Client: {client.name}")
                click.echo(f"Project: {project.name}")
                click.echo(f"Hours: {work_log.hours}")
                click.echo(f"Description: {work_log.description}")
                if work_log.category:
                    click.echo(f"Category: {work_log.category}")
                click.echo(f"Billable: {'Yes' if work_log.billable else 'No'}")
                click.echo(f"Invoiced: {'Yes' if work_log.invoice_id else 'No'}")
                click.echo("-" * 80)
                
                total_hours += float(work_log.hours)
                if work_log.billable:
                    billable_hours += float(work_log.hours)
            
            # Display summary
            click.echo(f"Total Hours: {total_hours:.2f}")
            click.echo(f"Billable Hours: {billable_hours:.2f}")
            
            # Calculate potential earnings if project rates are available
            if project_id:
                project = project_repo.get_by_id(session, project_id)
                potential_earnings = billable_hours * float(project.hourly_rate)
                click.echo(f"Potential Earnings: ${potential_earnings:.2f}")
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@work_log_commands.command(name="get")
@click.argument("work_log_id", type=int)
def get_work_log(work_log_id):
    """Get details for a specific work log."""
    work_log_repo = WorkLogRepository()
    project_repo = ProjectRepository()
    client_repo = ClientRepository()
    
    try:
        with get_session() as session:
            work_log = work_log_repo.get_by_id(session, work_log_id)
            
            if not work_log:
                click.echo(f"No work log found with ID: {work_log_id}")
                sys.exit(1)
            
            project = project_repo.get_by_id(session, work_log.project_id)
            client = client_repo.get_by_id(session, project.client_id)
            
            click.echo("\nWork Log Details:")
            click.echo("=" * 80)
            click.echo(f"ID: {work_log.id}")
            click.echo(f"Date: {work_log.work_date}")
            click.echo(f"Client: {client.name} (ID: {client.id})")
            click.echo(f"Project: {project.name} (ID: {project.id})")
            click.echo(f"Hours: {work_log.hours}")
            click.echo(f"Description: {work_log.description}")
            if work_log.category:
                click.echo(f"Category: {work_log.category}")
            click.echo(f"Billable: {'Yes' if work_log.billable else 'No'}")
            click.echo(f"Invoiced: {'Yes' if work_log.invoice_id else 'No'}")
            if work_log.invoice_id:
                click.echo(f"Invoice ID: {work_log.invoice_id}")
            click.echo(f"Created: {work_log.created_at}")
            click.echo(f"Updated: {work_log.updated_at}")
            
            # Calculate value
            if work_log.billable:
                value = float(work_log.hours) * float(project.hourly_rate)
                click.echo(f"Value: ${value:.2f} (at ${float(project.hourly_rate):.2f}/hour)")
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@work_log_commands.command(name="update")
@click.argument("work_log_id", type=int)
@click.option("--date", type=click.DateTime(formats=["%Y-%m-%d"]), help="New work date (YYYY-MM-DD)")
@click.option("--hours", type=float, help="New hours spent")
@click.option("--description", help="New description")
@click.option("--category", help="New category")
@click.option("--billable/--non-billable", help="Set billable status")
def update_work_log(work_log_id, date, hours, description, category, billable):
    """Update an existing work log."""
    work_log_repo = WorkLogRepository()
    
    # Collect update data (only non-None values)
    update_data = {}
    if date is not None:
        update_data["work_date"] = date.date() if hasattr(date, 'date') else date
    if hours is not None:
        update_data["hours"] = hours
    if description is not None:
        update_data["description"] = description
    if category is not None:
        update_data["category"] = category
    if billable is not None:
        update_data["billable"] = billable
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
    else:
        click.echo("No update parameters provided.")
        sys.exit(1)
    
    try:
        with get_session() as session:
            # Check if work log exists
            work_log = work_log_repo.get_by_id(session, work_log_id)
            if not work_log:
                click.echo(f"No work log found with ID: {work_log_id}")
                sys.exit(1)
            
            # Check if work log is already invoiced
            if work_log.invoice_id and (
                "work_date" in update_data or 
                "hours" in update_data or 
                "billable" in update_data
            ):
                if not click.confirm("This work log is already invoiced. Updating may affect invoice accuracy. Continue?"):
                    click.echo("Update cancelled.")
                    return
            
            # Update work log
            updated_work_log = work_log_repo.update(session, work_log_id, update_data)
            click.echo(f"Work log with ID {work_log_id} updated successfully.")
    except IntegrityError:
        click.echo("Error: Failed to update work log due to database constraint violation.")
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@work_log_commands.command(name="delete")
@click.argument("work_log_id", type=int)
@click.option("--force", is_flag=True, help="Force deletion without confirmation")
def delete_work_log(work_log_id, force):
    """Delete a work log from the database."""
    work_log_repo = WorkLogRepository()
    
    try:
        with get_session() as session:
            # Check if work log exists
            work_log = work_log_repo.get_by_id(session, work_log_id)
            if not work_log:
                click.echo(f"No work log found with ID: {work_log_id}")
                sys.exit(1)
            
            # Check if work log is already invoiced
            if work_log.invoice_id and not force:
                click.echo(f"Work log is already invoiced (Invoice ID: {work_log.invoice_id}). Use --force to delete anyway.")
                sys.exit(1)
            
            # Confirm deletion
            if not force:
                if not click.confirm(f"Are you sure you want to delete work log {work_log_id}?"):
                    click.echo("Deletion cancelled.")
                    return
            
            # Delete work log
            work_log_repo.delete(session, work_log_id)
            click.echo(f"Work log with ID {work_log_id} deleted successfully.")
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1)


@work_log_commands.command(name="summary")
@click.option("--start-date", type=click.DateTime(formats=["%Y-%m-%d"]), help="Start date (YYYY-MM-DD)")
@click.option("--end-date", type=click.DateTime(formats=["%Y-%m-%d"]), help="End date (YYYY-MM-DD)")
@click.option("--by-project", is_flag=True, help="Group by project")
@click.option("--by-client", is_flag=True, help="Group by client")
@click.option("--by-category", is_flag=True, help="Group by category")
def work_log_summary(start_date, end_date, by_project, by_client, by_category):
    """Generate a summary of work logs."""
    work_log_repo = WorkLogRepository()
    project_repo = ProjectRepository()
    client_repo = ClientRepository()
    
    # Default to current month if no dates provided
    if not start_date and not end_date:
        today = date.today()
        start_date = date(today.year, today.month, 1)
        end_date = (date(today.year, today.month + 1, 1) if today.month < 12 
                   else date(today.year + 1, 1, 1)) - timedelta(days=1)
    elif start_date and not end_date:
        end_date = date.today()
    elif end_date and not start_date:
        start_date = end_date.replace(day=1)
    
    # Convert datetime to date if needed
    if hasattr(start_date, 'date'):
        start_date = start_date.date()
    if hasattr(end_date, 'date'):
        end_date = end_date.date()
    
    try:
        with get_session() as session:
            # Get work logs for the date range
            work_logs = work_log_repo.get_by_date_range(session, start_date, end_date)
            
            if not work_logs:
                click.echo(f"No work logs found for period {start_date} to {end_date}.")
                return
            
            click.echo(f"\nWork Log Summary ({start_date} to {end_date}):")
            click.echo("=" * 80)
            
            # Calculate totals
            total_hours = sum(float(wl.hours) for wl in work_logs)
            billable_hours = sum(float(wl.hours) for wl in work_logs if wl.billable)
            
            click.echo(f"Total Hours: {total_hours:.2f}")
            click.echo(f"Billable Hours: {billable_hours:.2f}")
            click.echo(f"Non-Billable Hours: {(total_hours - billable_hours):.2f}")
            click.echo(f"Billable Percentage: {(billable_hours / total_hours * 100) if total_hours else 0:.1f}%")
            
            # Group by project
            if by_project:
                click.echo("\nHours by Project:")
                click.echo("-" * 80)
                
                project_hours = {}
                for wl in work_logs:
                    project_id = wl.project_id
                    if project_id not in project_hours:
                        project_hours[project_id] = {
                            "total": 0.0,
                            "billable": 0.0
                        }
                    project_hours[project_id]["total"] += float(wl.hours)
                    if wl.billable:
                        project_hours[project_id]["billable"] += float(wl.hours)
                
                for project_id, hours in project_hours.items():
                    project = project_repo.get_by_id(session, project_id)
                    client = client_repo.get_by_id(session, project.client_id)
                    
                    click.echo(f"Project: {project.name} (Client: {client.name})")
                    click.echo(f"  Total Hours: {hours['total']:.2f}")
                    click.echo(f"  Billable Hours: {hours['billable']:.2f}")
                    if hours['billable'] > 0:
                        value = hours['billable'] * float(project.hourly_rate)
                        click.echo(f"  Value: ${value:.2f}")
                    click.echo("")
            
            # Group by client
            if by_client:
                click.echo("\nHours by Client:")
                click.echo("-" * 80)
                
                client_hours = {}
                for wl in work_logs:
                    project = project_repo.get_by_id(session, wl.project_id)
                    client_id = project.client_id
                    
                    if client_id not in client_hours:
                        client_hours[client_id] = {
                            "total": 0.0,
                            "billable": 0.0,
                            "value": 0.0
                        }
                    client_hours[client_id]["total"] += float(wl.hours)
                    if wl.billable:
                        client_hours[client_id]["billable"] += float(wl.hours)
                        client_hours[client_id]["value"] += float(wl.hours) * float(project.hourly_rate)
                
                for client_id, hours in client_hours.items():
                    client = client_repo.get_by_id(session, client_id)
                    
                    click.echo(f"Client: {client.name}")
                    click.echo(f"  Total Hours: {hours['total']:.2f}")
                    click.echo(f"  Billable Hours: {hours['billable']:.2f}")
                    click.echo(f"  Value: ${hours['value']:.2f}")
                    click.echo("")
            
            # Group by category
            if by_category:
                click.echo("\nHours by Category:")
                click.echo("-" * 80)
                
                category_hours = {}
                for wl in work_logs:
                    category = wl.category or "Uncategorized"
                    
                    if category not in category_hours:
                        category_hours[category] = {
                            "total": 0.0,
                            "billable": 0.0
                        }
                    category_hours[category]["total"] += float(wl.hours)
                    if wl.billable:
                        category_hours[category]["billable"] += float(wl.hours)
                
                for category, hours in category_hours.items():
                    click.echo(f"Category: {category}")
                    click.echo(f"  Total Hours: {hours['total']:.2f}")
                    click.echo(f"  Billable Hours: {hours['billable']:.2f}")
                    click.echo(f"  Percentage of Total: {(hours['total'] / total_hours * 100):.1f}%")
                    click.echo("")
    except Exception as e:
        click.echo(f"Error: {str(e)}")
        sys.exit(1) 