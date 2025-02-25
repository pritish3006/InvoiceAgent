# Invoice Agent Project Plan

## Project Overview
An AI-powered agent for generating regular invoices based on logged work, using Ollama for local AI processing. The system will allow tracking of daily work, contract terms, tooling costs, and other relevant information needed for consistent invoicing.

## Goals
- Create a lightweight, locally deployed, low-compute solution for personal invoice generation
- Implement daily logging capabilities for work done
- Maintain reference information (contracts, rates, tools)
- Generate professional invoices using stored information
- Run locally using Ollama for AI processing

## System Architecture

### Core Components
1. **Data Storage Layer**
   - Store client/project information
   - Store contract terms and rates
   - Store work logs (daily entries)
   - Store invoice templates
   - Store generated invoices

2. **User Interface**
   - CLI for daily logging and invoice generation
   - Simple web interface (optional, for easier use)

3. **Processing Engine**
   - Integration with Ollama for AI processing
   - Logic for converting work logs to invoice items
   - Invoice generation and formatting

4. **Output Generation**
   - PDF/HTML invoice generation
   - Export capabilities

## Technology Stack
- **Backend**: Python (Flask for API if needed)
- **AI**: Ollama with Llama 3.2 8B model (locally deployed)
- **Database**: SQLite (lightweight, file-based)
- **UI**: 
  - Command-line interface with guided prompts
  - Simple web UI with HTML/CSS/JS (optional)
- **Output**: ReportLab or similar for PDF generation

## Design Considerations

### Invoice Design
- **Visual Customization**: Focus on templates, typography, and layout (no branding needed)
- **Content Requirements**:
  - Required fields: invoice number, dates, line items, rate per hour, total invoice value, payment information
  - Optional fields with customizable labels
  - Notes and terms sections
- **Tax Structure**: 1099 tax structure based in Austin, TX
- **Currency**: Single currency support (USD)

### Work Logging System
- **Input Methods**:
  - Structured entry with standardized fields
  - Free-form natural language entry processed by LLM
  - Templates for common activities
- **Organization**:
  - Predefined and custom task categories
  - Hierarchical relationship (Project → Task → Subtask)
  - Tagging system for cross-cutting concerns
- **Time Tracking**:
  - Duration tracking (not start/end times)
  - Consistent date formatting
  - All data fed to AI must be structured for consistent performance

### User Experience Priorities
- Fast and easy daily work entry
- Flexible format to account for different kinds of work
- Low-friction to establish daily habit
- Editable for auditing before invoice finalization

### Backup Strategy
- SQLite database backups
- Google Drive sync for offsite storage

## Project Phases

### Phase 1: Basic Setup and Data Management
- Project structure setup
- Database schema design and implementation
- Basic CLI for data entry
- Data storage implementation

### Phase 2: Ollama Integration
- Local Ollama setup and configuration
- API integration for AI processing
- Basic prompt engineering for invoice generation

### Phase 3: Invoice Generation
- Template design
- Invoice generation logic
- PDF output generation

### Phase 4: Refinement
- User experience improvements
- Additional features based on usage
- Testing and bug fixing

## Next Steps
1. Set up project structure and environment
2. Design database schema
3. Implement basic data entry functionality
4. Configure Ollama integration

## Open Questions / Considerations
- How to optimize prompt engineering for best results with Llama 3.2 8B?
- What is the optimal balance between structured and free-form logging?
- How to ensure consistent data quality when processing free-form entries?
- What level of customization is necessary for invoice templates? 