# InvoiceAgent User Guide

This guide provides detailed instructions for using the InvoiceAgent application to manage clients, projects, work logs, and invoices.

## Table of Contents

- [Introduction](#introduction)
- [Installation and Setup](#installation-and-setup)
- [Client Management](#client-management)
- [Project Management](#project-management)
- [Work Logging](#work-logging)
- [Invoice Generation](#invoice-generation)
- [Invoice Management](#invoice-management)
- [Configuration](#configuration)
- [AI Features](#ai-features)
- [Troubleshooting](#troubleshooting)

## Introduction

InvoiceAgent is a command-line application designed to help freelancers and contractors track their work, manage clients and projects, and generate professional invoices. It combines traditional structured input with AI-powered natural language processing to make work logging and invoice generation as effortless as possible.

### Key Concepts

- **Clients**: Individuals or organizations you work for
- **Projects**: Specific engagements with clients, including rate information
- **Work Logs**: Records of time spent on projects
- **Invoices**: Generated documents that bill clients for completed work

## Installation and Setup

### Prerequisites

- Python 3.8 or newer
- Ollama installed locally for AI features
- Llama 3.2 model pulled in Ollama

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/pritish3006/InvoiceAgent.git
   cd InvoiceAgent
   ```

2. Create a virtual environment:
   ```bash
   python -m venv invoice_agent_env
   # For bash or zsh shells:
   source invoice_agent_env/bin/activate
   # On Windows:
   # invoice_agent_env\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install the package in development mode:
   ```bash
   pip install -e .
   ```

5. Initialize the database:
   ```bash
   invoiceagent db init
   ```

6. Pull the Llama 3.2 model in Ollama (if not already done):
   ```bash
   ollama pull llama3.2:latest
   ```

### Initial Configuration

Before using InvoiceAgent, you should configure your company information:

```bash
invoiceagent config company --name "Your Company" --address "123 Main St\nCity, State 12345" --phone "(123) 456-7890" --email "billing@yourcompany.com"
```

You can also add a company logo:

```bash
invoiceagent config logo /path/to/your/logo.png
```

And configure payment details:

```bash
invoiceagent config payment --details "Payment Details:\nBank Name: Example Bank\nAccount Number: XXXX-XXXX-XXXX-1234\nRouting Number: XXXXXXXXX"
```

### Troubleshooting Installation

If you encounter issues during installation:

1. Ensure Python 3.8+ is installed:
   ```bash
   python --version
   ```

2. Check that pip is up-to-date:
   ```bash
   pip install --upgrade pip
   ```

3. For virtual environment issues, try deactivating and reactivating:
   ```bash
   deactivate
   # For bash or zsh shells:
   source invoice_agent_env/bin/activate
   ```

## Client Management

Clients are the individuals or organizations you work for. InvoiceAgent stores client information for use in invoices and project management.

### Adding a Client

To add a new client:

```bash
invoiceagent client add
```

Follow the interactive prompts to enter:
- Client name (required)
- Contact name (optional)
- Email (optional)
- Phone (optional)
- Address (optional)
- Notes (optional)

Alternatively, you can specify all details directly:

```bash
invoiceagent client add --name "Acme Corp" --contact "John Doe" --email "john@acme.com" --phone "555-123-4567" --address "123 Business St, City, State" --notes "Enterprise client"
```

### Listing Clients

To view all clients:

```bash
invoiceagent client list
```

### Viewing Client Details

To view details for a specific client:

```bash
invoiceagent client get CLIENT_ID
```

### Updating Client Information

To update client information:

```bash
invoiceagent client update CLIENT_ID --name "New Name" --email "new-email@example.com"
```

You can update any combination of fields.

### Deleting a Client

To delete a client:

```bash
invoiceagent client delete CLIENT_ID
```

Note: This will also delete all associated projects, work logs, and invoices.

## Project Management

Projects represent specific engagements with clients, including rate information and other details.

### Creating a Project

To create a new project:

```bash
invoiceagent project create
```

Follow the interactive prompts to enter:
- Project name (required)
- Client ID (required)
- Description (optional)
- Hourly rate (required)
- Start date (optional, format: YYYY-MM-DD)
- End date (optional, format: YYYY-MM-DD)
- Equity information (optional)

Alternatively, you can specify all details directly:

```bash
invoiceagent project create --name "Website Redesign" --client-id 1 --description "Complete redesign of corporate website" --hourly-rate 150 --start-date "2023-05-01" --end-date "2023-07-31"
```

### Creating a Project with Equity Compensation

For projects that include equity compensation:

```bash
invoiceagent project create --name "Startup Project" --client-id 1 --hourly-rate 100 --has-equity --equity-type "Stock Options" --equity-amount 0.5 --equity-details "ISO options vesting monthly"
```

This sets up a project with a cash rate of $100/hour plus 0.5 stock options per hour worked.

### Listing Projects

To view all projects:

```bash
invoiceagent project list
```

To filter by client:

```bash
invoiceagent project list --client-id 1
```

To show only active projects:

```bash
invoiceagent project list --active-only
```

### Viewing Project Details

To view details for a specific project:

```bash
invoiceagent project get PROJECT_ID
```

### Updating Project Information

To update project information:

```bash
invoiceagent project update PROJECT_ID --name "New Name" --hourly-rate 175
```

You can update any combination of fields.

### Deactivating/Reactivating a Project

To mark a project as inactive:

```bash
invoiceagent project update PROJECT_ID --inactive
```

To reactivate:

```bash
invoiceagent project update PROJECT_ID --active
```

### Deleting a Project

To delete a project:

```bash
invoiceagent project delete PROJECT_ID
```

Note: This will also delete all associated work logs.

## Work Logging

Work logs record the time you spend on projects. These logs form the basis for invoice generation.

### Adding a Work Log with Structured Input

To add a work log with manual entry:

```bash
invoiceagent log add
```

Follow the interactive prompts to enter:
- Project ID or name (required)
- Work date (required, format: YYYY-MM-DD)
- Hours spent (required)
- Description of work (required)
- Category (optional)
- Billable status (default: billable)

Alternatively, you can specify all details directly:

```bash
invoiceagent log add --project-id 1 --date 2023-05-15 --hours 3.5 --description "Implemented user authentication system" --category "Development" --billable
```

### Adding a Work Log with Natural Language

InvoiceAgent can parse natural language descriptions using AI:

```bash
invoiceagent log add --free-form "Spent 2.5 hours yesterday working on database schema design for Acme Corp's ProjectX"
```

The AI will analyze this text and extract:
- Client (if mentioned)
- Project (if mentioned)
- Date (if mentioned, otherwise uses current date)
- Hours
- Description
- Category (automatically determined)
- Tags (automatically determined)

If the client/project can't be determined from the text, you may need to specify:

```bash
invoiceagent log add --free-form "Spent 3 hours on API integration" --project-id 1
```

### Listing Work Logs

To view all work logs:

```bash
invoiceagent log list
```

To filter by project:

```bash
invoiceagent log list --project-id 1
```

To filter by client:

```bash
invoiceagent log list --client-id 1
```

To filter by date range:

```bash
invoiceagent log list --start-date 2023-05-01 --end-date 2023-05-31
```

To show only unbilled work logs:

```bash
invoiceagent log list --unbilled-only
```

### Viewing Work Log Details

To view details for a specific work log:

```bash
invoiceagent log get WORK_LOG_ID
```

### Updating Work Log Information

To update work log information:

```bash
invoiceagent log update WORK_LOG_ID --hours 4.0 --description "Updated description"
```

You can update any combination of fields.

### Deleting a Work Log

To delete a work log:

```bash
invoiceagent log delete WORK_LOG_ID
```

### Work Log Summary

To view a summary of your work:

```bash
invoiceagent log summary --start-date 2023-05-01 --end-date 2023-05-31
```

Group by project:

```bash
invoiceagent log summary --by-project
```

Group by client:

```bash
invoiceagent log summary --by-client
```

Group by category:

```bash
invoiceagent log summary --by-category
```

## Invoice Generation

Invoices are generated from work logs based on date ranges and other criteria.

### Generating an Invoice

To generate an invoice for a client:

```bash
invoiceagent invoice generate --client-id 1 --start-date 2023-05-01 --end-date 2023-05-31
```

Required parameters:
- `--client-id`: Client ID
- `--start-date`: Start date for work logs (YYYY-MM-DD)
- `--end-date`: End date for work logs (YYYY-MM-DD)

Optional parameters:
- `--issue-date`: Invoice issue date (defaults to today)
- `--due-date`: Invoice due date
- `--tax-rate`: Tax rate percentage (e.g., 8.5)
- `--notes`: Invoice notes
- `--combine-items`: Combine work logs with the same category
- `--include-equity`: Include equity compensation (default)
- `--dry-run`: Preview invoice without saving

### Generating an Invoice with Equity Components

Equity components are included by default:

```bash
invoiceagent invoice generate --client-id 1 --start-date 2023-05-01 --end-date 2023-05-31 --include-equity
```

To exclude equity components:

```bash
invoiceagent invoice generate --client-id 1 --start-date 2023-05-01 --end-date 2023-05-31 --exclude-equity
```

### Previewing an Invoice

To preview an invoice without saving it:

```bash
invoiceagent invoice generate --client-id 1 --start-date 2023-05-01 --end-date 2023-05-31 --dry-run
```

## Invoice Management

After generating invoices, you can manage them using the following commands.

### Listing Invoices

To view all invoices:

```bash
invoiceagent invoice list
```

Filter by client:

```bash
invoiceagent invoice list --client-id 1
```

Filter by status:

```bash
invoiceagent invoice list --status sent
```

Filter by date range:

```bash
invoiceagent invoice list --start-date 2023-05-01 --end-date 2023-05-31
```

### Viewing Invoice Details

To view details for a specific invoice:

```bash
invoiceagent invoice get INVOICE_ID
```

### Updating Invoice Status

To update the status of an invoice:

```bash
invoiceagent invoice update-status INVOICE_ID STATUS
```

Available statuses:
- `draft`: Invoice is a draft
- `sent`: Invoice has been sent to the client
- `paid`: Invoice has been paid
- `overdue`: Invoice is past due
- `canceled`: Invoice has been canceled

Example:

```bash
invoiceagent invoice update-status 1 sent
```

### Deleting an Invoice

To delete an invoice:

```bash
invoiceagent invoice delete INVOICE_ID
```

### Exporting an Invoice to PDF

To export an invoice to PDF:

```bash
invoiceagent invoice export INVOICE_ID
```

This will create a PDF file in the current directory with the name `invoice_{number}.pdf`.

Specify a custom output path:

```bash
invoiceagent invoice export INVOICE_ID --output /path/to/invoice.pdf
```

Use a specific template:

```bash
invoiceagent invoice export INVOICE_ID --template professional
```

List available templates:

```bash
invoiceagent invoice export --list-templates
```

## Configuration

InvoiceAgent offers various configuration options to customize your experience.

### Company Information

To set or update your company information:

```bash
invoiceagent config company --name "Your Company" --address "123 Main St\nCity, State 12345" --phone "(123) 456-7890" --email "billing@yourcompany.com"
```

To view current company information:

```bash
invoiceagent config company --show
```

### Logo

To add or update your company logo:

```bash
invoiceagent config logo /path/to/your/logo.png
```

To remove your logo:

```bash
invoiceagent config logo --remove
```

### Payment Information

To set or update payment details:

```bash
invoiceagent config payment --details "Payment Details:\nBank Name: Example Bank\nAccount Number: XXXX-XXXX-XXXX-1234\nRouting Number: XXXXXXXXX"
```

To view current payment information:

```bash
invoiceagent config payment --show
```

### Invoice Templates

To list available invoice templates:

```bash
invoiceagent config templates
```

## AI Features

InvoiceAgent uses AI to enhance several features of the application.

### Natural Language Work Logging

The most prominent AI feature is the ability to process natural language work descriptions:

```bash
invoiceagent log add --free-form "Spent 3 hours yesterday on the database design for ACME project"
```

The AI will extract:
- Work date (from "yesterday")
- Hours (3)
- Description ("database design for ACME project")
- Client (ACME, if recognized)
- Project (if recognized)
- Category (automatically determined as "Development")

### Smart Invoice Item Generation

When generating invoices, the AI can help summarize and categorize similar work items when using the `--combine-items` option.

## Troubleshooting

### Common Issues

#### Database Issues

If you encounter database errors, try resetting the database:

```bash
invoiceagent db reset
```

Warning: This will delete all data!

#### AI Processing Issues

If AI-powered features aren't working:

1. Ensure Ollama is running:
   ```bash
   invoiceagent status
   ```

2. Check that the Llama 3.2 model is installed:
   ```bash
   ollama list
   ```

3. If not installed, pull the model:
   ```bash
   ollama pull llama3.2:latest
   ```

#### Command Not Found

If the `invoiceagent` command is not found:

1. Ensure you've activated the virtual environment:
   ```bash
   source invoice_agent_env/bin/activate
   ```

2. Reinstall the package in development mode:
   ```bash
   pip install -e .
   ```

### Getting Help

For any command, you can add `--help` to see available options:

```bash
invoiceagent --help
invoiceagent client --help
invoiceagent invoice generate --help
```

## Additional Resources

- [Command Reference](command_reference.md): Detailed information on all commands
- [Configuration Guide](configuration.md): Detailed information on configuration options
- [GitHub Repository](https://github.com/pritish3006/InvoiceAgent): Source code and issue reporting
