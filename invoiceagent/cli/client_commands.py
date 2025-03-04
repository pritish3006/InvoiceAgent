"""Client management CLI commands for InvoiceAgent."""

import sys
from datetime import datetime

import click
from sqlalchemy.exc import IntegrityError

from invoiceagent.db.engine import get_session
from invoiceagent.db.models import Client
from invoiceagent.db.repositories.client import ClientRepository
from invoiceagent.cli.utils import (
    print_success,
    print_error,
    print_info,
    print_table,
    print_entity,
    confirm_action,
)


@click.group(name="client")
def client_commands():
    """Client management commands."""
    pass


@client_commands.command(name="add")
@click.option("--name", prompt="Client name", help="Name of the client")
@click.option("--contact-name", prompt=True, help="Name of the primary contact")
@click.option("--email", prompt=True, help="Email address of the client")
@click.option("--phone", prompt=True, help="Phone number of the client")
@click.option("--address", prompt=True, help="Address of the client")
@click.option("--notes", prompt=True, help="Additional notes about the client")
def add_client(name, contact_name, email, phone, address, notes):
    """Add a new client to the database."""
    client_repo = ClientRepository()
    
    # Create client data
    client_data = {
        "name": name,
        "contact_name": contact_name,
        "email": email,
        "phone": phone,
        "address": address,
        "notes": notes,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    
    # Add client to database
    try:
        with get_session() as session:
            # Check if client with same name already exists
            existing_client = client_repo.get_by_name(session, name)
            if existing_client:
                print_error(f"Client with name '{name}' already exists.")
                sys.exit(1)
            
            # Create new client
            client = client_repo.create(session, **client_data)
            print_success(f"Client added successfully with ID: {client.id}")
    except IntegrityError:
        print_error("Failed to add client due to database constraint violation.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@client_commands.command(name="list")
@click.option("--with-projects", is_flag=True, help="Include projects in the output")
def list_clients(with_projects):
    """List all clients in the database."""
    client_repo = ClientRepository()
    
    try:
        with get_session() as session:
            if with_projects:
                clients = client_repo.get_all_with_projects(session)
            else:
                clients = client_repo.get_all(session)
            
            if not clients:
                print_info("No clients found.")
                return
            
            print_info("\nClients:")
            
            # Prepare table data
            columns = ["ID", "Name", "Contact", "Email", "Phone"]
            data = []
            
            for client in clients:
                row = [
                    str(client.id),
                    client.name,
                    client.contact_name or "",
                    client.email or "",
                    client.phone or "",
                ]
                data.append(row)
                
                if with_projects and client.projects:
                    for project in client.projects:
                        data.append([
                            "↳",
                            f"Project: {project.name}",
                            f"Rate: ${project.hourly_rate}/hr",
                            "Active" if project.is_active else "Inactive",
                            "",
                        ])
            
            print_table(columns=columns, data=data)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@client_commands.command(name="get")
@click.argument("client_id", type=int)
def get_client(client_id):
    """Get details for a specific client."""
    client_repo = ClientRepository()
    
    try:
        with get_session() as session:
            client = client_repo.get_by_id(session, client_id)
            
            if not client:
                print_error(f"No client found with ID: {client_id}")
                sys.exit(1)
            
            # Convert client to dictionary for display
            client_data = {
                "ID": client.id,
                "Name": client.name,
                "Contact": client.contact_name,
                "Email": client.email,
                "Phone": client.phone,
                "Address": client.address,
                "Notes": client.notes,
                "Created": client.created_at,
                "Updated": client.updated_at,
            }
            
            print_entity(client_data, title="Client Details")
            
            if client.projects:
                print_info("\nProjects:")
                columns = ["ID", "Name", "Rate", "Status", "Start Date", "End Date"]
                data = [
                    [
                        str(p.id),
                        p.name,
                        f"${p.hourly_rate}/hr",
                        "Active" if p.is_active else "Inactive",
                        str(p.start_date) if p.start_date else "",
                        str(p.end_date) if p.end_date else "",
                    ]
                    for p in client.projects
                ]
                print_table(columns=columns, data=data)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@client_commands.command(name="update")
@click.argument("client_id", type=int)
@click.option("--name", help="New name for the client")
@click.option("--contact-name", help="New contact name")
@click.option("--email", help="New email address")
@click.option("--phone", help="New phone number")
@click.option("--address", help="New address")
@click.option("--notes", help="New notes")
def update_client(client_id, name, contact_name, email, phone, address, notes):
    """Update an existing client."""
    client_repo = ClientRepository()
    
    # Collect update data (only non-None values)
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if contact_name is not None:
        update_data["contact_name"] = contact_name
    if email is not None:
        update_data["email"] = email
    if phone is not None:
        update_data["phone"] = phone
    if address is not None:
        update_data["address"] = address
    if notes is not None:
        update_data["notes"] = notes
    
    if update_data:
        update_data["updated_at"] = datetime.utcnow()
    else:
        print_error("No update parameters provided.")
        sys.exit(1)
    
    try:
        with get_session() as session:
            # Check if client exists
            client = client_repo.get_by_id(session, client_id)
            if not client:
                print_error(f"No client found with ID: {client_id}")
                sys.exit(1)
            
            # Update client
            updated_client = client_repo.update(session, client_id, update_data)
            print_success(f"Client with ID {client_id} updated successfully.")
    except IntegrityError:
        print_error("Failed to update client due to database constraint violation.")
        sys.exit(1)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@client_commands.command(name="delete")
@click.argument("client_id", type=int)
@click.option("--force", is_flag=True, help="Force deletion without confirmation")
def delete_client(client_id, force):
    """Delete a client from the database."""
    client_repo = ClientRepository()
    
    try:
        with get_session() as session:
            # Check if client exists
            client = client_repo.get_by_id(session, client_id)
            if not client:
                print_error(f"No client found with ID: {client_id}")
                sys.exit(1)
            
            # Confirm deletion
            if not force:
                if not confirm_action(f"Are you sure you want to delete client '{client.name}'?"):
                    print_info("Deletion cancelled.")
                    return
            
            # Check if client has projects
            if client.projects and not force:
                print_error(f"Client has {len(client.projects)} projects. Use --force to delete anyway.")
                sys.exit(1)
            
            # Delete client
            client_repo.delete(session, client_id)
            print_success(f"Client '{client.name}' deleted successfully.")
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1)


@client_commands.command(name="search")
@click.argument("name_pattern")
def search_clients(name_pattern):
    """Search for clients by name pattern."""
    client_repo = ClientRepository()
    
    try:
        with get_session() as session:
            clients = client_repo.search_by_name(session, name_pattern)
            
            if not clients:
                print_info(f"No clients found matching pattern: {name_pattern}")
                return
            
            print_info(f"\nFound {len(clients)} clients matching '{name_pattern}':")
            
            # Prepare table data
            columns = ["ID", "Name", "Contact", "Email", "Phone"]
            data = [
                [
                    str(client.id),
                    client.name,
                    client.contact_name or "",
                    client.email or "",
                    client.phone or "",
                ]
                for client in clients
            ]
            
            print_table(columns=columns, data=data)
    except Exception as e:
        print_error(f"Error: {str(e)}")
        sys.exit(1) 