# InvoiceAgent Developer Guide

This guide is intended for developers who want to understand the codebase, fix bugs, add features, or contribute to the InvoiceAgent project.

## Table of Contents

- [Project Structure](#project-structure)
- [Development Environment](#development-environment)
- [Architecture Overview](#architecture-overview)
- [Database Schema](#database-schema)
- [Core Components](#core-components)
- [Testing](#testing)
- [Adding New Features](#adding-new-features)
- [Contribution Guidelines](#contribution-guidelines)

## Project Structure

The InvoiceAgent codebase is organized into several modules:

```
/invoiceagent
  /ai              # AI integration with Ollama
  /cli             # Command-line interface implementation
  /config          # Configuration management
  /db              # Database models, migrations, and repositories
  /export          # PDF generation and export functionality
  /templates       # Invoice templates and configurations
  /utils           # Helper utilities
```

Important files:
- `setup.py`: Package installation configuration
- `requirements.txt`: Production dependencies
- `requirements-dev.txt`: Development dependencies
- `alembic.ini`: Database migration configuration

## Development Environment

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) installed locally
- Llama 3.2 model pulled in Ollama

### Setting Up a Development Environment

1. **Clone the repository**
```bash
git clone https://github.com/pritish3006/InvoiceAgent.git
cd InvoiceAgent
```

2. **Create and activate a virtual environment**
```bash
python -m venv invoice_agent_env
# For bash or zsh shells:
source invoice_agent_env/bin/activate
# On Windows:
# invoice_agent_env\Scripts\activate
```

3. **Install development dependencies**
```bash
pip install -r requirements.txt
```

4. **Install the package in development mode**
```bash
pip install -e .
```

5. **Initialize the database**
```bash
invoiceagent db init
```

6. **Set up pre-commit hooks**
```bash
pre-commit install
```

### Running the Application in Development Mode

After setting up the development environment, you can run the application with:

```bash
invoiceagent [command] [options]
```

## Architecture Overview

InvoiceAgent follows a modular, layered architecture:

1. **CLI Layer (`invoiceagent/cli/`)**: Command-line interface for all functionality
2. **Service Layer (`invoiceagent/db/repositories/`)**: Business logic and operations
3. **Data Layer (`invoiceagent/db/models.py`)**: Database models and data structure
4. **AI Integration (`invoiceagent/ai/`)**: Ollama LLM integration
5. **Export Layer (`invoiceagent/export/`)**: PDF generation and export

### Key Design Patterns

- **Repository Pattern**: Used in the database layer to abstract data access
- **Command Pattern**: CLI commands encapsulate operations
- **Dependency Injection**: Services are injected into higher-level components

## Database Schema

InvoiceAgent uses SQLAlchemy for ORM and Alembic for migrations. The core models are:

### Client

Represents clients for whom you work:
- `id`: Primary key
- `name`: Client name
- `contact_name`: Contact person's name
- `email`: Contact email
- `phone`: Contact phone
- `address`: Physical address
- `notes`: Additional notes

### Project

Represents a specific project or engagement with a client:
- `id`: Primary key
- `name`: Project name
- `client_id`: Foreign key to client
- `description`: Project description
- `hourly_rate`: Billing rate for the project
- `is_active`: Project status
- `start_date`: Project start date
- `end_date`: Project end date
- `has_equity_component`: Whether the project includes equity compensation
- `equity_type`: Type of equity
- `equity_amount_per_hour`: Equity amount per hour worked
- `equity_details`: Additional details about equity

### WorkLog

Represents time spent on a project:
- `id`: Primary key
- `project_id`: Foreign key to project
- `invoice_id`: Foreign key to invoice (if billed)
- `work_date`: Date of work
- `hours`: Hours spent
- `description`: Description of work performed
- `category`: Work category
- `billable`: Whether the work is billable

### Invoice

Represents an invoice to a client:
- `id`: Primary key
- `client_id`: Foreign key to client
- `invoice_number`: Unique invoice number
- `issue_date`: Date invoice was issued
- `due_date`: Date payment is due
- `paid_date`: Date payment was received
- `sent_date`: Date invoice was sent
- `status`: Invoice status (draft, sent, paid, overdue, canceled)
- `notes`: Additional notes
- `subtotal`: Invoice subtotal
- `tax_rate`: Tax rate applied
- `tax_amount`: Tax amount
- `total_amount`: Total invoice amount

### InvoiceItem

Represents an individual line item on an invoice:
- `id`: Primary key
- `invoice_id`: Foreign key to invoice
- `work_log_id`: Foreign key to work log (if applicable)
- `description`: Description of the item
- `quantity`: Quantity (usually hours)
- `unit`: Unit of measurement
- `rate`: Rate per unit
- `amount`: Total amount for the item
- `category`: Category of work
- `has_equity_component`: Whether this item includes equity
- `equity_type`: Type of equity
- `equity_quantity`: Quantity of equity
- `equity_description`: Description of equity component

## Core Components

### Command-Line Interface (`invoiceagent/cli/`)

The CLI is built using the [Click](https://click.palletsprojects.com/) framework and is organized into command groups:

- `client_commands.py`: Client management
- `project_commands.py`: Project management
- `work_log_commands.py`: Work log management
- `invoice_commands.py`: Invoice generation and management
- `config_commands.py`: Configuration management
- `db_commands.py`: Database commands
- `ai_commands.py`: AI interaction commands

### Repositories (`invoiceagent/db/repositories/`)

Repositories encapsulate database operations for each model:

- `BaseRepository`: Common repository functionality
- `ClientRepository`: Client operations
- `ProjectRepository`: Project operations
- `WorkLogRepository`: Work log operations
- `InvoiceRepository`: Invoice operations

### Database Management (`invoiceagent/db/`)

- `engine.py`: Database connection management
- `migrations/`: Alembic migrations
- `models.py`: SQLAlchemy models

### AI Integration (`invoiceagent/ai/`)

- `ollama_client.py`: Client for interacting with Ollama API
- `work_processor.py`: Process natural language work descriptions
- `models.py`: Pydantic models for AI interactions
- `templates/`: Prompt templates for the LLM

### PDF Generation (`invoiceagent/export/`)

- `pdf_generator.py`: Generate PDF invoices
- `models.py`: Models for invoice templates
- `template_manager.py`: Manage invoice templates

## Testing

InvoiceAgent uses [pytest](https://docs.pytest.org/) for testing.

### Running Tests

```bash
pytest
```

For specific test files:

```bash
pytest tests/test_client_repository.py
```

With verbosity:

```bash
pytest -v
```

### Writing Tests

Tests are organized by component:

- `tests/db/`: Database tests
- `tests/cli/`: CLI tests
- `tests/export/`: Export functionality tests
- `tests/ai/`: AI integration tests

Example test case pattern:

```python
def test_client_repository_create():
    # Setup
    with get_test_session() as session:
        repo = ClientRepository()

        # Execute
        client = repo.create(session, "Test Client", "Test Contact", "test@example.com")
        session.commit()

        # Assert
        assert client.id is not None
        assert client.name == "Test Client"

        # Cleanup
        session.delete(client)
        session.commit()
```

## Adding New Features

### Adding a New Command

1. Identify the appropriate command group (client, project, invoice, etc.)
2. Add a new command function to the corresponding file in `invoiceagent/cli/`
3. Decorate it with the appropriate Click decorators
4. Implement the command logic

Example:

```python
@client_commands.command(name="search")
@click.argument("query", type=str)
def search_clients(query: str):
    """Search for clients by name or contact information."""
    with get_session() as session:
        client_repo = ClientRepository()
        clients = client_repo.search(session, query)

        if not clients:
            print_warning(f"No clients found matching '{query}'.")
            return

        # Display results
        rows = [[client.id, client.name, client.contact_name, client.email] for client in clients]
        print_table(["ID", "Name", "Contact", "Email"], rows, title=f"Search Results for '{query}'")
```

### Adding a New Model

1. Define the model in `invoiceagent/db/models.py`
2. Create a new repository in `invoiceagent/db/repositories/`
3. Create a database migration:
```bash
alembic revision --autogenerate -m "Add new model"
```
4. Update the CLI to interact with the new model

### Adding a New Template

1. Create a new JSON file in `invoiceagent/templates/invoice_configs/`
2. Follow the structure of existing templates
3. Ensure it has a unique name
4. Test it with invoice export

## Contribution Guidelines

### Code Style

InvoiceAgent follows PEP 8 style guidelines and uses:
- [Black](https://black.readthedocs.io/) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [flake8](https://flake8.pycqa.org/) for linting

The pre-commit hooks will ensure these standards are followed.

### Pull Request Process

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature-name`)
3. Make your changes
4. Run tests to ensure all tests pass
5. Commit your changes (`git commit -am 'Add some feature'`)
6. Push to the branch (`git push origin feature/your-feature-name`)
7. Create a Pull Request

### Commit Message Format

Use conventional commit messages:

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools

Example: `fix: Resolve issue with invoice number generation`

## Troubleshooting Common Issues

### Database Migrations

If you encounter database migration issues:

1. Ensure you're using the correct version of alembic
2. Check if your model changes are properly reflected in the migration script
3. If all else fails, reset the database:
```bash
invoiceagent db reset --force
```

### Ollama Connection Issues

If Ollama integration isn't working:

1. Verify Ollama is running:
```bash
curl http://localhost:11434/api/version
```
2. Check if you have the Llama 3.2 model:
```bash
ollama list
```
3. Pull the model if needed:
```bash
ollama pull llama3.2:latest
```

### PDF Generation Issues

If PDF generation doesn't work:

1. Ensure ReportLab is properly installed
2. Verify template files exist in the correct location
3. Check if the logo file is accessible
4. Look for issues in the invoice data itself
