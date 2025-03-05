# InvoiceAgent Command Reference

This document provides a comprehensive reference for all commands available in the InvoiceAgent application.

## Table of Contents

- [Global Options](#global-options)
- [Main Commands](#main-commands)
- [Client Commands](#client-commands)
- [Project Commands](#project-commands)
- [Work Log Commands](#work-log-commands)
- [Invoice Commands](#invoice-commands)
- [Configuration Commands](#configuration-commands)
- [Database Commands](#database-commands)
- [AI Commands](#ai-commands)

## Global Options

These options apply to all InvoiceAgent commands:

```
--version  Show the version and exit.
--help     Show help message and exit.
```

## Main Commands

### invoiceagent

The root command for all InvoiceAgent functionality.

```bash
invoiceagent [OPTIONS] COMMAND [ARGS]...
```

Options:
- `--version`: Show the version and exit.
- `--help`: Show help message and exit.

### invoiceagent status

Check the status of the InvoiceAgent application, including database and AI connections.

```bash
invoiceagent status
```

## Client Commands

Commands for managing clients.

### invoiceagent client

Parent command for client management operations.

```bash
invoiceagent client [OPTIONS] COMMAND [ARGS]...
```

### invoiceagent client add

Add a new client to the database.

```bash
invoiceagent client add [OPTIONS]
```

Options:
- `--name TEXT`: Client name
- `--contact TEXT`: Contact name
- `--email TEXT`: Email address
- `--phone TEXT`: Phone number
- `--address TEXT`: Physical address (use \n for line breaks)
- `--notes TEXT`: Additional notes

### invoiceagent client list

List all clients.

```bash
invoiceagent client list
```

### invoiceagent client get

Get detailed information about a specific client.

```bash
invoiceagent client get [OPTIONS] CLIENT_ID
```

Arguments:
- `CLIENT_ID`: ID of the client (required)

### invoiceagent client update

Update an existing client.

```bash
invoiceagent client update [OPTIONS] CLIENT_ID
```

Arguments:
- `CLIENT_ID`: ID of the client to update (required)

Options:
- `--name TEXT`: New client name
- `--contact TEXT`: New contact name
- `--email TEXT`: New email address
- `--phone TEXT`: New phone number
- `--address TEXT`: New physical address (use \n for line breaks)
- `--notes TEXT`: New additional notes

### invoiceagent client delete

Delete a client.

```bash
invoiceagent client delete [OPTIONS] CLIENT_ID
```

Arguments:
- `CLIENT_ID`: ID of the client to delete (required)

Options:
- `--force`: Force deletion without confirmation

## Project Commands

Commands for managing projects.

### invoiceagent project

Parent command for project management operations.

```bash
invoiceagent project [OPTIONS] COMMAND [ARGS]...
```

### invoiceagent project create

Create a new project.

```bash
invoiceagent project create [OPTIONS]
```

Options:
- `--name TEXT`: Project name
- `--client-id INTEGER`: ID of the client
- `--description TEXT`: Description of the project
- `--hourly-rate FLOAT`: Hourly rate for the project
- `--start-date TEXT`: Project start date (YYYY-MM-DD)
- `--end-date TEXT`: Project end date (YYYY-MM-DD)
- `--has-equity`: Project includes equity compensation
- `--equity-type TEXT`: Type of equity (e.g., Stock Options, RSUs, Shares)
- `--equity-amount FLOAT`: Amount of equity per hour
- `--equity-details TEXT`: Additional details about the equity component

### invoiceagent project list

List all projects.

```bash
invoiceagent project list [OPTIONS]
```

Options:
- `--client-id INTEGER`: Filter by client ID
- `--active-only`: Show only active projects

### invoiceagent project get

Get detailed information about a specific project.

```bash
invoiceagent project get [OPTIONS] PROJECT_ID
```

Arguments:
- `PROJECT_ID`: ID of the project (required)

### invoiceagent project update

Update an existing project.

```bash
invoiceagent project update [OPTIONS] PROJECT_ID
```

Arguments:
- `PROJECT_ID`: ID of the project to update (required)

Options:
- `--name TEXT`: New project name
- `--description TEXT`: New project description
- `--hourly-rate FLOAT`: New hourly rate
- `--active/--inactive`: Set project active status
- `--start-date TEXT`: New start date (YYYY-MM-DD)
- `--end-date TEXT`: New end date (YYYY-MM-DD)
- `--has-equity/--no-equity`: Project includes equity compensation
- `--equity-type TEXT`: Type of equity (e.g., Stock Options, RSUs, Shares)
- `--equity-amount FLOAT`: Amount of equity per hour
- `--equity-details TEXT`: Additional details about the equity component

### invoiceagent project delete

Delete a project.

```bash
invoiceagent project delete [OPTIONS] PROJECT_ID
```

Arguments:
- `PROJECT_ID`: ID of the project to delete (required)

Options:
- `--force`: Force deletion without confirmation

## Work Log Commands

Commands for managing work logs.

### invoiceagent log

Parent command for work log management operations.

```bash
invoiceagent log [OPTIONS] COMMAND [ARGS]...
```

### invoiceagent log add

Add a new work log entry.

```bash
invoiceagent log add [OPTIONS]
```

Options:
- `--project-id INTEGER`: ID of the project
- `--project-name TEXT`: Name of the project (if project ID is not provided)
- `--date TEXT`: Work date (YYYY-MM-DD)
- `--hours FLOAT`: Hours spent
- `--description TEXT`: Description of work performed
- `--category TEXT`: Category of work
- `--billable/--non-billable`: Whether the work is billable
- `--free-form TEXT`: Free-form text description to be processed by AI

### invoiceagent log list

List work log entries.

```bash
invoiceagent log list [OPTIONS]
```

Options:
- `--project-id INTEGER`: Filter by project ID
- `--client-id INTEGER`: Filter by client ID
- `--start-date TEXT`: Start date (YYYY-MM-DD)
- `--end-date TEXT`: End date (YYYY-MM-DD)
- `--unbilled-only`: Show only unbilled work logs
- `--billable-only`: Show only billable work logs

### invoiceagent log get

Get detailed information about a specific work log.

```bash
invoiceagent log get [OPTIONS] WORK_LOG_ID
```

Arguments:
- `WORK_LOG_ID`: ID of the work log (required)

### invoiceagent log update

Update an existing work log.

```bash
invoiceagent log update [OPTIONS] WORK_LOG_ID
```

Arguments:
- `WORK_LOG_ID`: ID of the work log to update (required)

Options:
- `--date TEXT`: New work date (YYYY-MM-DD)
- `--hours FLOAT`: New hours spent
- `--description TEXT`: New description
- `--category TEXT`: New category
- `--billable/--non-billable`: Set billable status

### invoiceagent log delete

Delete a work log.

```bash
invoiceagent log delete [OPTIONS] WORK_LOG_ID
```

Arguments:
- `WORK_LOG_ID`: ID of the work log to delete (required)

Options:
- `--force`: Force deletion without confirmation

### invoiceagent log summary

Generate a summary of work logs.

```bash
invoiceagent log summary [OPTIONS]
```

Options:
- `--start-date TEXT`: Start date (YYYY-MM-DD)
- `--end-date TEXT`: End date (YYYY-MM-DD)
- `--by-project`: Group by project
- `--by-client`: Group by client
- `--by-category`: Group by category

## Invoice Commands

Commands for generating and managing invoices.

### invoiceagent invoice

Parent command for invoice operations.

```bash
invoiceagent invoice [OPTIONS] COMMAND [ARGS]...
```

### invoiceagent invoice generate

Generate a new invoice.

```bash
invoiceagent invoice generate [OPTIONS]
```

Options:
- `--client-id INTEGER`: Client ID for the invoice (required)
- `--start-date TEXT`: Start date (YYYY-MM-DD) (required)
- `--end-date TEXT`: End date (YYYY-MM-DD) (required)
- `--issue-date TEXT`: Issue date (YYYY-MM-DD) (defaults to today)
- `--due-date TEXT`: Due date (YYYY-MM-DD)
- `--tax-rate FLOAT`: Tax rate percentage
- `--notes TEXT`: Invoice notes
- `--combine-items`: Combine work logs with the same category
- `--include-equity`: Include equity components
- `--dry-run`: Preview invoice without saving

### invoiceagent invoice list

List invoices.

```bash
invoiceagent invoice list [OPTIONS]
```

Options:
- `--client-id INTEGER`: Filter by client ID
- `--status [draft|sent|paid|overdue|canceled]`: Filter by invoice status
- `--start-date TEXT`: Filter by issue date - start (YYYY-MM-DD)
- `--end-date TEXT`: Filter by issue date - end (YYYY-MM-DD)

### invoiceagent invoice get

Get detailed information about a specific invoice.

```bash
invoiceagent invoice get [OPTIONS] INVOICE_ID
```

Arguments:
- `INVOICE_ID`: ID of the invoice (required)

### invoiceagent invoice update-status

Update the status of an invoice.

```bash
invoiceagent invoice update-status [OPTIONS] INVOICE_ID STATUS
```

Arguments:
- `INVOICE_ID`: ID of the invoice (required)
- `STATUS`: New status (draft, sent, paid, overdue, canceled) (required)

### invoiceagent invoice delete

Delete an invoice.

```bash
invoiceagent invoice delete [OPTIONS] INVOICE_ID
```

Arguments:
- `INVOICE_ID`: ID of the invoice to delete (required)

Options:
- `--force`: Force deletion without confirmation

### invoiceagent invoice export

Export an invoice to PDF.

```bash
invoiceagent invoice export [OPTIONS] INVOICE_ID
```

Arguments:
- `INVOICE_ID`: ID of the invoice to export (required)

Options:
- `--output PATH`: Output file path
- `--template TEXT`: Invoice template to use (default: default)
- `--list-templates`: List available templates and exit

### invoiceagent invoice templates

List available invoice templates.

```bash
invoiceagent invoice templates
```

## Configuration Commands

Commands for configuring the application.

### invoiceagent config

Parent command for configuration operations.

```bash
invoiceagent config [OPTIONS] COMMAND [ARGS]...
```

### invoiceagent config company

Configure company information.

```bash
invoiceagent config company [OPTIONS]
```

Options:
- `--name TEXT`: Company name
- `--address TEXT`: Company address (use \n for line breaks)
- `--phone TEXT`: Company phone number
- `--email TEXT`: Company email
- `--template TEXT`: Template name to update (default: default)
- `--show`: Show current company information

### invoiceagent config payment

Configure payment information.

```bash
invoiceagent config payment [OPTIONS]
```

Options:
- `--details TEXT`: Payment details to show on invoices (use \n for line breaks)
- `--template TEXT`: Template name to update (default: default)
- `--show`: Show current payment information

### invoiceagent config templates

List available invoice templates.

```bash
invoiceagent config templates
```

### invoiceagent config logo

Update or remove the company logo.

```bash
invoiceagent config logo [OPTIONS] [LOGO_PATH]
```

Arguments:
- `LOGO_PATH`: Path to the logo file (optional)

Options:
- `--remove`: Remove the current logo

### invoiceagent config payment-template

Set up payment details using predefined templates.

```bash
invoiceagent config payment-template
```

## Database Commands

Commands for managing the database.

### invoiceagent db

Parent command for database operations.

```bash
invoiceagent db [OPTIONS] COMMAND [ARGS]...
```

### invoiceagent db init

Initialize the database.

```bash
invoiceagent db init [OPTIONS]
```

### invoiceagent db migrate

Run database migrations.

```bash
invoiceagent db migrate [OPTIONS]
```

### invoiceagent db reset

Reset the database (WARNING: This will delete all data).

```bash
invoiceagent db reset [OPTIONS]
```

Options:
- `--force`: Force reset without confirmation

## AI Commands

Commands for interacting with AI features.

### invoiceagent ai

Parent command for AI operations.

```bash
invoiceagent ai [OPTIONS] COMMAND [ARGS]...
```

### invoiceagent ai process

Process text with AI.

```bash
invoiceagent ai process [OPTIONS] TEXT
```

Arguments:
- `TEXT`: Text to process (required)

Options:
- `--project-id INTEGER`: Project ID for context
- `--template TEXT`: AI template to use

## Environment Variables

InvoiceAgent supports the following environment variables:

- `INVOICEAGENT_CONFIG_DIR`: Directory for configuration files
- `INVOICEAGENT_DATABASE_PATH`: Path to the SQLite database file
- `INVOICEAGENT_TEMPLATES_DIR`: Directory for invoice templates
- `INVOICEAGENT_OLLAMA_URL`: URL for Ollama API (default: http://localhost:11434)
- `INVOICEAGENT_OLLAMA_MODEL`: Ollama model to use (default: llama3.2:latest) 