# Invoice Agent PRD (Product Requirements Document)

## 1. Overview

### 1.1 Product Vision
Invoice Agent is a lightweight, AI-powered tool for independent contractors to log daily work, maintain client information, and generate professional invoices with minimal effort. The system uses Ollama with Llama 3.2 to process work logs and generate invoice content.

### 1.2 Target User
Myself for my independent contracting, freelancing work to:
- Track my billable time
- Generate consistent, professional invoices
- Maintain records of client work
- Operate with minimal overhead

### 1.3 Success Metrics
- Time saved in invoice generation process
- Accuracy of work logging
- Consistency of invoice content
- User adoption of daily logging habit

## 2. Core Functionality

### 2.1 Data Management

#### 2.1.1 Client & Project Information
- **Required Fields**:
  - Client name, contact information, address
  - Project name, description
  - Contract terms (rates, payment terms)
  - Tax information (using 1099 structure for Austin, TX)

#### 2.1.2 Work Logging System
- **Dual Input Methods**:
  - Structured entry with standardized fields
  - Free-form natural language entry (processed by LLM into structured format)
- **Required Fields**:
  - Date (consistent format)
  - Client/Project reference
  - Task description
  - Duration (hours)
  - Category/Tags
  - Billable status
- **Organization**:
  - Hierarchical: Project → Task → Subtask
  - Predefined and custom categories
  - Tagging system for cross-cutting concerns

#### 2.1.3 Invoice Records
- **Required Fields**:
  - Invoice number, date, due date
  - Client information
  - Line items (description, quantity, rate, amount)
  - Subtotal, taxes, total
  - Payment information and terms
- **Optional Fields**:
  - Notes
  - Custom terms
  - Reference numbers

### 2.2 AI Integration

#### 2.2.1 Ollama Configuration
- Use Llama 3.2 8B model
- Local deployment for privacy and speed
- Configurable inference parameters

#### 2.2.2 AI Processing Functions
- Convert free-form logs to structured data
- Generate professional line item descriptions
- Summarize work for invoice purposes
- Suggest categorization of work entries

### 2.3 Invoice Generation

#### 2.3.1 Template System
- Basic invoice template with customizable typography and layout
- HTML/CSS based for flexibility
- PDF output generation

#### 2.3.2 Content Customization
- Configurable required and optional fields
- Customizable field labels
- Notes and terms sections

#### 2.3.3 Financial Calculations
- Automatic calculation of totals
- Tax handling for 1099 contractors
- Support for hourly, fixed, and mixed billing types

## 3. User Experience

### 3.1 Work Logging Interface
- **Design Principles**:
  - Fast entry of daily work
  - Flexible to accommodate different types of work
  - Low-friction to establish daily habit
  - Editable for corrections and adjustments
- **Functionality**:
  - CLI-based interface with guided prompts
  - Templates for common activities
  - Batch entry capabilities
  - Review and edit capabilities

### 3.2 Invoice Management
- **Generation Process**:
  - Select time period and client
  - Review and edit line items
  - Customize invoice options
  - Generate and save invoice
- **Review Capabilities**:
  - Preview before finalization
  - Edit individual line items
  - Add notes or special terms

### 3.3 Data Visibility
- Summary views of logged work
- Historical invoice access
- Client and project overviews

## 4. Technical Implementation

### 4.1 System Architecture
- Python-based CLI application
- SQLite database for data storage
- Ollama API integration
- PDF generation using ReportLab or similar

### 4.2 Database Schema
- Clients table
- Projects table
- Work logs table
- Invoices table
- Settings & Templates tables

### 4.3 Backup System
- SQLite database backups
- Google Drive sync for offsite storage
- Automated backup schedule
- Simple recovery procedures

## 5. Development Approach

### 5.1 Project Phases
Follow the implementation roadmap defined in implementation_roadmap.md:
- Phase 1: Foundation (Weeks 1-2)
- Phase 2: Core Functionality (Weeks 3-4)
- Phase 3: Invoice Generation (Weeks 5-6)
- Phase 4: Refinement & Usability (Weeks 7-8)

### 5.2 Prioritization
- **Must Have**:
  - Work logging (structured)
  - Client/project management
  - Basic invoice generation
  - Data backup
- **Should Have**:
  - Hybrid of Free-form and structured logging with AI processing
  - Template customization
  - Tagging and categorization
- **Nice to Have**:
  - Web interface
  - Advanced reporting
  - Auto-categorization

### 5.3 Testing Approach
- Unit tests for core functionality
- Integration tests for AI components
- User acceptance testing for workflows

## 6. Future Considerations

### 6.1 Potential Enhancements
- Simple web UI for data entry
- Enhanced reporting and analytics
- Integration with accounting software
- Multi-currency support

### 6.2 Scalability Considerations
While currently focused on personal use, consider:
- Data model design that allows for future expansion
- Clear separation of concerns in architecture
- Extensible template system 