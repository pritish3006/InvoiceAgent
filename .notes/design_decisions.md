# Design Decisions

This document tracks major design decisions for the InvoiceAgent project.

## Technology Decisions

| Decision | Options Considered | Choice | Rationale |
|----------|-------------------|--------|-----------|
| Local LLM | GPT API, Ollama, Hugging Face | **Ollama with Llama 3.2 8B** | Privacy, cost efficiency, local control |
| Database | SQLite, PostgreSQL, File-based | **SQLite** | Lightweight, file-based, sufficient for personal use |
| Backend Language | Python, Node.js, Go | **Python** | Strong data processing capabilities, integration with ML libraries |
| UI Approach | CLI, Web, Desktop | **CLI with potential Web UI** | Simplicity, automation friendly, with path to better UI if needed |
| Document Generation | ReportLab, WeasyPrint, Pandoc | **ReportLab** | Mature Python library with PDF capabilities |
| ORM | Raw SQL, SQLAlchemy, Peewee | **SQLAlchemy** | Mature, flexible, good migration tooling |

## Architecture Decisions

| Decision | Description | Rationale |
|----------|------------|-----------|
| Modular Design | Separate core data, AI processing, and UI components | Allows independent development and testing |
| Local Processing | All processing done on user's machine | Privacy, no API costs, no internet dependency |
| File-Based Storage | Database and backups stored as files | Simplicity, ease of backup, portability |
| Template System | Jinja2-based invoice templates | Flexibility, separation of content and presentation |
| Dual Input Methods | Structured and free-form logging | Balance between user convenience and data consistency |

## User Experience Decisions

| Decision | Description | Rationale |
|----------|------------|-----------|
| CLI-First Approach | Primary interface via command line | Speed, automation, low overhead |
| Guided Prompts | Interactive CLI with smart defaults | Reduce friction for daily use |
| Consistent Formatting | Standardized date and time formats | Improve AI processing reliability |
| Hierarchical Work Organization | Project → Task → Subtask model | Matches how work is naturally organized |
| Pre-Invoice Review | Explicit review step before generation | Quality control, avoid errors |

## AI Processing Decisions

| Decision | Description | Rationale |
|----------|------------|-----------|
| Llama 3.2 8B Model | Use smaller model initially | Balance between capability and resource usage |
| Structured Output Format | Define JSON schema for AI outputs | Ensure consistent, parseable responses |
| Template Prompts | Use consistent prompt templates | Improve reliability of AI outputs |
| Fallback Mechanisms | Basic functionality without AI | System remains usable if AI processing fails |
| Client-Side Inference | Run Ollama locally | Privacy, no API costs |

## Data Management Decisions

| Decision | Description | Rationale |
|----------|------------|-----------|
| SQLAlchemy ORM | Abstract database operations | Cleaner code, portability, migration support |
| JSON Storage for Templates | Store templates as JSON files | Easy editing, version control friendly |
| Daily Backups | Automate daily database backups | Data protection with minimal overhead |
| Google Drive Sync | Use Drive for offsite backup | Simple, widely available cloud solution |

## Outstanding Decisions

| Decision | Options | Considerations |
|----------|---------|----------------|
| Invoice PDF Styling | Custom CSS, Template-based | Balance between flexibility and development effort |
| Deployment Strategy | Single-file executable, pip package | How users will install and run the application |
| Prompt Optimization | Static prompts, Dynamic generation | How to create effective prompts for the LLM |
| Integration Testing | Approach for testing AI components | How to test AI processing reliably | 