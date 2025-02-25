# Technical Architecture and Design Decisions

## Core Technologies

### Language Choice: Python
- **Rationale**: Python offers excellent libraries for both CLI applications and AI integration. It's lightweight, readable, and has strong support for data processing tasks.
- **Alternatives Considered**: 
  - Node.js (rejected due to higher resource usage)
  - Rust (rejected due to development speed considerations)

### Database: SQLite
- **Rationale**: File-based, zero-configuration, lightweight yet powerful enough for our needs. Perfect for personal use with minimal setup.
- **Alternatives Considered**:
  - JSON files (rejected due to lack of query capabilities)
  - PostgreSQL (rejected as overkill for personal use case)

### AI Processing: Ollama
- **Rationale**: Runs locally, providing privacy and no recurring costs. Can run smaller models with reasonable performance on consumer hardware.
- **Model Recommendations**:
  - Primary: Mistral-7B or Llama-2-7B (good balance of performance and resource usage)
  - Lightweight alternative: Phi-2 (if resource constraints are significant)
- **Alternatives Considered**:
  - OpenAI API (rejected due to recurring costs and privacy concerns)
  - Hugging Face Inference API (rejected due to dependence on internet connection)

### UI Approach: CLI First
- **Rationale**: Faster development, lower resource usage, and easier automation. Better suited for regular quick entries.
- **Web UI as Optional Extension**: Simple Flask-based web interface could be added later if desired.

## Data Architecture

### Database Schema Design
Normalized structure to minimize redundancy:

1. **Clients**:
   - `id` (PRIMARY KEY)
   - `name`
   - `address`
   - `contact_email`
   - `contact_phone`
   - `notes`

2. **Projects**:
   - `id` (PRIMARY KEY)
   - `client_id` (FOREIGN KEY)
   - `name`
   - `description`
   - `hourly_rate`
   - `start_date`
   - `end_date` (nullable)
   - `status` (active/completed)
   - `contract_terms` (text)

3. **WorkLogs**:
   - `id` (PRIMARY KEY)
   - `project_id` (FOREIGN KEY)
   - `date`
   - `hours`
   - `description`
   - `category` (e.g., development, meetings, etc.)

4. **ExpenseItems**:
   - `id` (PRIMARY KEY)
   - `project_id` (FOREIGN KEY)
   - `date`
   - `amount`
   - `description`
   - `receipt_path` (optional)

5. **Invoices**:
   - `id` (PRIMARY KEY)
   - `invoice_number`
   - `client_id` (FOREIGN KEY)
   - `issue_date`
   - `due_date`
   - `status` (draft/sent/paid)
   - `notes`
   - `total_amount`

6. **InvoiceItems**:
   - `id` (PRIMARY KEY)
   - `invoice_id` (FOREIGN KEY)
   - `description`
   - `quantity`
   - `unit_price`
   - `total_price`
   - `work_log_ids` (JSON array, for reference)

## File Storage Structure

```
/data
  /db
    invoice_agent.db       # SQLite database
  /receipts                # Storage for expense receipts
  /generated_invoices      # Storage for generated invoice PDFs
/templates
  /invoice                 # Invoice templates
    default.html
    minimal.html
/logs                      # Application logs
```

## API Design

### Internal API Layers
1. **Data Access Layer**: Abstracts database operations
2. **Business Logic Layer**: Handles work log summarization, invoice generation
3. **Ollama Integration Layer**: Manages AI processing requests

### Ollama Integration
- Use local HTTP API (typically http://localhost:11434/api/generate)
- Implement retry mechanism for potential failures
- Cache responses where appropriate to reduce processing

## Security Considerations
- Local-only application, no internet-facing components
- Data stored locally, consider file permissions
- No sensitive authentication needed for personal use
- Consider simple encryption for stored client data if handling sensitive information

## Performance Considerations
- Batch processing for invoice generation
- Potential for background processing of AI tasks
- Minimal memory footprint due to SQLite's efficiency
- Ollama model selection based on available hardware 