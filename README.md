# InvoiceAgent

A lightweight, AI-powered invoicing system for independent contractors and freelancers powered by Ollama.

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## Overview

InvoiceAgent is a comprehensive tool designed to simplify the process of tracking work and generating professional invoices. It leverages Ollama with the Llama 3.2 model to process natural language work descriptions and create well-formatted invoice content.

### Key Features

- **Work Logging**: Log your work using natural language or structured input
- **Client Management**: Store and manage client information
- **Project Tracking**: Organize work by project with customizable rates
- **Invoice Generation**: Create professional invoices from your work logs
- **PDF Export**: Generate well-formatted PDF invoices
- **Customizable Templates**: Personalize your invoice appearance
- **Equity Compensation**: Support for contracts that include both cash and equity components
- **AI-Powered**: Process natural language descriptions into structured data
- **Local Privacy**: Runs entirely locally for data privacy and cost efficiency

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [User Guide](#user-guide)
- [Command Reference](#command-reference)
- [Configuration](#configuration)
- [Development](#development)
- [License](#license)

## Installation

### Prerequisites

- Python 3.10+
- [Ollama](https://ollama.ai/) installed locally
- Llama 3.2 model pulled in Ollama

### Production Installation (End Users)

If you just want to use InvoiceAgent without developing it:

```bash
# Install directly from PyPI
pip install invoiceagent

# Initialize the database
invoiceagent db init

# Pull the Llama 3.2 model in Ollama (if not already done)
ollama pull llama3.2:latest
```

### Development Installation

If you want to contribute to InvoiceAgent or modify the code:

1. **Clone the repository**
```bash
git clone https://github.com/pritish3006/InvoiceAgent.git
cd InvoiceAgent
```

2. **Create a virtual environment**
```bash
python -m venv invoice_agent_env
# For bash or zsh shells:
source invoice_agent_env/bin/activate
# On Windows:
# invoice_agent_env\Scripts\activate
```

3. **Install dependencies**
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

6. **Pull the Llama 3.2 model in Ollama** (if not already done)
```bash
ollama pull llama3.2:latest
```

## Quick Start

Here's how to quickly get started with InvoiceAgent:

### 1. Set Up Your Company Information

Configure your company information that will appear on invoices:

```bash
invoiceagent config company --name "Your Company" --address "123 Main St\nCity, State 12345" --phone "(123) 456-7890" --email "billing@yourcompany.com"
```

### 2. Add a Client

```bash
invoiceagent client add
# Follow the prompts to enter client details
```

### 3. Create a Project

```bash
invoiceagent project create --name "Sample Project" --client-id 1 --hourly-rate 150
```

### 4. Log Your Work

With structured input:
```bash
invoiceagent log add --project-id 1 --date 2023-04-01 --hours 4.5 --description "Initial project setup and requirements gathering"
```

Or with natural language (AI-processed):
```bash
invoiceagent log add --free-form "Spent 3 hours today working on database design for the Sample Project"
```

### 5. Generate an Invoice

```bash
invoiceagent invoice generate --client-id 1 --start-date 2023-04-01 --end-date 2023-04-30 --issue-date 2023-05-01 --due-date 2023-05-15
```

### 6. Export the Invoice to PDF

```bash
invoiceagent invoice export 1 --output invoice.pdf
```

## User Guide

For a complete user guide including detailed instructions on all features, please see the [User Guide](docs/user_guide.md).

## Command Reference

InvoiceAgent uses a command-line interface with several command groups:

- `invoiceagent client` - Manage clients
- `invoiceagent project` - Manage projects
- `invoiceagent log` - Log and manage work entries
- `invoiceagent invoice` - Generate and manage invoices
- `invoiceagent config` - Configure application settings
- `invoiceagent db` - Database management commands

For detailed descriptions of all commands, see the [Command Reference](docs/command_reference.md).

## Configuration

InvoiceAgent offers extensive configuration options for customizing your experience:

- **Company Info**: Set your company information for invoices
- **Invoice Templates**: Customize the appearance of your invoices
- **Payment Details**: Add your payment information to invoices
- **Logo**: Add your company logo to invoices

For detailed configuration instructions, see [Configuration Guide](docs/configuration.md).

## Development

### Project Structure

```
/invoiceagent
  /ai              # AI integration with Ollama
  /cli             # Command-line interface implementation
  /config          # Configuration management
  /db              # Database models, migrations, and repositories
  /export          # PDF generation and export
  /templates       # Invoice templates and configurations
  /utils           # Helper utilities
```

### Running Tests

```bash
pytest
```

### Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature-name`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature-name`
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Ollama](https://ollama.ai/) for the local LLM platform
- [SQLAlchemy](https://www.sqlalchemy.org/) for ORM functionality
- [ReportLab](https://www.reportlab.com/) for PDF generation
- [Click](https://click.palletsprojects.com/) for CLI framework
