# Invoice Agent

A lightweight, AI-powered invoicing system for independent contractors powered by Ollama.

## Overview

Invoice Agent is a personal tool designed to simplify the process of tracking work and generating professional invoices. It uses Ollama with the Llama 3.2 model to process daily work logs and create well-formatted invoice content.

Key features:
- Log daily work with minimal friction
- Store client and project information
- Track contract terms and rates
- Generate professional invoices
- Process natural language descriptions into structured data
- Run entirely locally for privacy and cost efficiency

## Getting Started

### Prerequisites

- Python 3.8+
- [Ollama](https://ollama.ai/) installed locally
- Llama 3.2 model pulled in Ollama

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/invoiceagent.git
cd invoiceagent
```

2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Initialize the database
```bash
python -m invoiceagent.db.init
```

5. Pull the Llama 3.2 model in Ollama (if not already done)
```bash
ollama pull llama3.2:8b
```

### Basic Usage

#### Setting Up

1. Add a client
```bash
invoiceagent client add
```

2. Add a project
```bash
invoiceagent project add
```

#### Daily Work Logging

Log work using structured entry:
```bash
invoiceagent log add
```

Or with free-form entry:
```bash
invoiceagent log add --free-form "Spent 2 hours working on database schema design for Acme Corp's ProjectX"
```

#### Generating Invoices

```bash
invoiceagent invoice generate --client "ClientName" --start-date "2023-07-01" --end-date "2023-07-31"
```

## Project Structure

```
/invoiceagent
  /db              # Database models and migrations
  /cli             # Command-line interface
  /ai              # Ollama integration
  /templates       # Invoice templates
  /export          # PDF generation
  /utils           # Helper utilities
  /config          # Configuration management
```

## Development

Check the `.notes` directory for detailed documentation:
- Project planning: `.notes/project_plan.md`
- PRD: `.notes/invoice_agent_prd.md`
- Design decisions: `.notes/design_decisions.md`
- Implementation roadmap: `.notes/implementation_roadmap.md`

### Development Guidelines

This project follows the guidelines defined in `.cursorrules`. Please review this file before contributing.

### Running Tests

```bash
pytest
```

## License

MIT

## Acknowledgments

- [Ollama](https://ollama.ai/) for the local LLM platform
- [SQLAlchemy](https://www.sqlalchemy.org/) for ORM functionality
- [ReportLab](https://www.reportlab.com/) for PDF generation 