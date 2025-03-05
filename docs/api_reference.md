# InvoiceAgent API Reference

While InvoiceAgent is primarily a command-line application, its components can be used programmatically in Python code. This document provides information on how to use InvoiceAgent as a library.

## Table of Contents

- [Database Models](#database-models)
- [Repository API](#repository-api)
- [AI Integration](#ai-integration)
- [PDF Generation](#pdf-generation)
- [Configuration Management](#configuration-management)

## Database Models

### Importing Models

```python
from invoiceagent.db.models import Client, Project, WorkLog, Invoice, InvoiceItem, InvoiceStatus
```

### Client Model

```python
client = Client(
    name="Acme Corp",
    contact_name="John Doe",
    email="john@acme.com",
    phone="555-123-4567",
    address="123 Business St, City, State",
    notes="Enterprise client"
)
```

### Project Model

```python
project = Project(
    name="Website Redesign",
    client_id=1,  # Reference to a client
    description="Complete redesign of corporate website",
    hourly_rate=150.00,
    is_active=True,
    start_date=datetime.date(2023, 5, 1),
    end_date=datetime.date(2023, 7, 31),
    # Equity fields
    has_equity_component=False,
    equity_type=None,
    equity_amount_per_hour=None,
    equity_details=None
)
```

### WorkLog Model

```python
work_log = WorkLog(
    project_id=1,  # Reference to a project
    invoice_id=None,  # Will be set when invoiced
    work_date=datetime.date(2023, 5, 15),
    hours=3.5,
    description="Implemented user authentication system",
    category="Development",
    billable=True
)
```

### Invoice Model

```python
invoice = Invoice(
    client_id=1,  # Reference to a client
    invoice_number="INV-2023-001",
    issue_date=datetime.date(2023, 6, 1),
    due_date=datetime.date(2023, 6, 15),
    paid_date=None,
    sent_date=None,
    status=InvoiceStatus.DRAFT,
    notes="Invoice for May 2023",
    subtotal=1050.00,
    tax_rate=8.5,
    tax_amount=89.25,
    total_amount=1139.25
)
```

### InvoiceItem Model

```python
invoice_item = InvoiceItem(
    invoice_id=1,  # Reference to an invoice
    work_log_id=1,  # Reference to a work log
    description="Implemented user authentication system",
    quantity=3.5,  # Hours
    unit="hour",
    rate=150.00,
    amount=525.00,
    category="Development",
    # Equity fields
    has_equity_component=False,
    equity_type=None,
    equity_quantity=None,
    equity_description=None
)
```

## Repository API

InvoiceAgent uses the repository pattern to abstract database operations. Each repository provides methods for CRUD operations and other specific operations for its entity.

### Database Session

```python
from invoiceagent.db.engine import get_session

# Using a session
with get_session() as session:
    # Perform database operations
    pass
```

### Client Repository

```python
from invoiceagent.db.repositories.client import ClientRepository

client_repo = ClientRepository()

# Create a client
with get_session() as session:
    client = client_repo.create(
        session, 
        name="Acme Corp",
        contact_name="John Doe",
        email="john@acme.com"
    )
    session.commit()
    
    # Get a client by ID
    client = client_repo.get_by_id(session, client_id=1)
    
    # Get all clients
    clients = client_repo.get_all(session)
    
    # Update a client
    client = client_repo.update(
        session,
        client_id=1,
        name="Acme Corporation",
        email="contact@acme.com"
    )
    session.commit()
    
    # Delete a client
    result = client_repo.delete(session, client_id=1)
    session.commit()
```

### Project Repository

```python
from invoiceagent.db.repositories.project import ProjectRepository

project_repo = ProjectRepository()

# Create a project
with get_session() as session:
    project = project_repo.create(
        session,
        name="Website Redesign",
        client_id=1,
        hourly_rate=150.0,
        description="Redesign corporate website"
    )
    session.commit()
    
    # Get projects by client
    projects = project_repo.get_by_client_id(session, client_id=1)
    
    # Get active projects
    active_projects = project_repo.get_active_projects(session)
```

### WorkLog Repository

```python
from invoiceagent.db.repositories.work_log import WorkLogRepository
from datetime import date

work_log_repo = WorkLogRepository()

# Create a work log
with get_session() as session:
    work_log = work_log_repo.create(
        session,
        project_id=1,
        work_date=date(2023, 5, 15),
        hours=3.5,
        description="Implemented authentication system",
        category="Development",
        billable=True
    )
    session.commit()
    
    # Get work logs by project
    work_logs = work_log_repo.get_by_project_id(session, project_id=1)
    
    # Get work logs by date range
    logs = work_log_repo.get_by_date_range(
        session,
        start_date=date(2023, 5, 1),
        end_date=date(2023, 5, 31)
    )
    
    # Get unbilled work logs
    unbilled = work_log_repo.get_unbilled(session, client_id=1)
```

### Invoice Repository

```python
from invoiceagent.db.repositories.invoice import InvoiceRepository
from invoiceagent.db.models import InvoiceStatus
from datetime import date, timedelta
from decimal import Decimal

invoice_repo = InvoiceRepository()

# Create an invoice from work logs
with get_session() as session:
    invoice = invoice_repo.create_invoice_from_work_logs(
        session,
        client_id=1,
        start_date=date(2023, 5, 1),
        end_date=date(2023, 5, 31),
        issue_date=date(2023, 6, 1),
        due_date=date(2023, 6, 1) + timedelta(days=14),
        tax_rate=Decimal("8.5"),
        notes="Invoice for May 2023",
        combine_same_category=True
    )
    session.commit()
    
    # Get invoice with items
    invoice = invoice_repo.get_with_client_and_items(session, invoice_id=1)
    
    # Update invoice status
    invoice = invoice_repo.update_invoice_status(
        session,
        invoice_id=1,
        status=InvoiceStatus.SENT
    )
    session.commit()
```

## AI Integration

InvoiceAgent provides AI integration for processing natural language work descriptions.

### OllamaClient

```python
from invoiceagent.ai.ollama_client import OllamaClient
import asyncio

async def generate_content():
    client = OllamaClient(
        base_url="http://localhost:11434",
        model="llama3.2:latest",
        timeout=60
    )
    
    # Generate content
    response = await client.generate(
        prompt="Summarize this work: Spent 3 hours on database design and implementation.",
        system_prompt="You are a helpful assistant for organizing work logs.",
        temperature=0.7,
        max_tokens=2000
    )
    
    # Close the client
    await client.close()
    
    return response

# Run the async function
result = asyncio.run(generate_content())
print(result)
```

### WorkLogProcessor

```python
from invoiceagent.ai.work_processor import WorkLogProcessor
import asyncio

async def process_work_log():
    processor = WorkLogProcessor()
    
    # Process a free-form work log
    work_log = await processor.process_free_form_log(
        "Spent 3 hours yesterday designing the database schema for the client portal project",
        project_id=1
    )
    
    return work_log

# Run the async function
work_log = asyncio.run(process_work_log())
print(f"Hours: {work_log.hours}, Description: {work_log.description}, Category: {work_log.category}")
```

## PDF Generation

InvoiceAgent provides functionality for generating PDF invoices.

### Generating an Invoice PDF

```python
from invoiceagent.export.pdf_generator import generate_invoice_pdf
from invoiceagent.db.engine import get_session
from invoiceagent.db.repositories.invoice import InvoiceRepository

# Generate a PDF invoice
with get_session() as session:
    invoice_repo = InvoiceRepository()
    invoice = invoice_repo.get_with_client_and_items(session, invoice_id=1)
    
    if invoice:
        pdf_path = generate_invoice_pdf(
            invoice=invoice,
            output_path="invoice.pdf",
            template_name="default"
        )
        print(f"Invoice PDF generated at: {pdf_path}")
```

### Working with Invoice Templates

```python
from invoiceagent.export.template_manager import load_template, list_available_templates

# List available templates
templates = list_available_templates()
print(f"Available templates: {templates}")

# Load a template
template = load_template("default")
if template:
    print(f"Template name: {template.name}")
    print(f"Template description: {template.description}")
```

## Configuration Management

### Working with Configuration

```python
from invoiceagent.config import get_config, update_config

# Get configuration
config = get_config()
database_path = config.get("database", "path")
print(f"Database path: {database_path}")

# Update configuration
update_config({
    "database": {
        "path": "~/invoiceagent.db"
    }
})
```

### Working with Template Configurations

```python
from invoiceagent.export.template_manager import load_template, save_template
from invoiceagent.export.models import InvoiceTemplateConfig

# Load a template
template = load_template("default")

if template:
    # Modify the template
    template.header.company_name = "My Company"
    template.footer.text = "Thank you for your business!"
    
    # Save the modified template
    save_template(template, "custom")
``` 