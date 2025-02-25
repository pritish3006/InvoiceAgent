"""
Work log processing module for InvoiceAgent.

Handles the conversion of free-form work logs to structured data
and generation of invoice line items.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from invoiceagent.ai.ollama_client import OllamaClient, format_prompt
from invoiceagent.ai.models import WorkLog, InvoiceItem

# Output schemas for structured generation
WORK_LOG_SCHEMA = {
    "type": "object",
    "properties": {
        "client": {"type": "string"},
        "project": {"type": "string"},
        "work_date": {"type": "string", "format": "date"},
        "hours": {"type": "number"},
        "description": {"type": "string"},
        "category": {"type": "string"},
        "billable": {"type": "boolean"},
        "tags": {"type": "array", "items": {"type": "string"}}
    },
    "required": ["client", "project", "work_date", "hours", "description"]
}

INVOICE_ITEM_SCHEMA = {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "description": {"type": "string"},
            "hours": {"type": "number"},
            "unit": {"type": "string"},
            "rate": {"type": "number"},
            "amount": {"type": "number"},
            "category": {"type": "string"}
        },
        "required": ["description", "hours", "unit", "rate", "amount"]
    }
}


class WorkLogProcessor:
    """
    Processes work logs and generates structured invoice data.
    """
    def __init__(self, ollama_client: Optional[OllamaClient] = None):
        """
        Initialize the work log processor.
        
        Args:
            ollama_client: OllamaClient instance to use, or None to create a new one
        """
        self.client = ollama_client or OllamaClient()
    
    async def process_free_form_log(self, log_text: str) -> WorkLog:
        """
        Process a free-form work log entry and convert it to structured data.
        
        Args:
            log_text: The free-form work log text
            
        Returns:
            Structured work log data as a WorkLog model
        """
        prompt = format_prompt("work_log_processing", work_log=log_text)
        
        system_prompt = """
        You are an LLM assistant that extracts structured information from work logs.
        Identify client name, project, date, hours worked, and work description.
        If the information is ambiguous or missing, ask the user for clarification with clear and specific questions.
        """
        
        raw_result = await self.client.structured_generate(
            prompt=prompt,
            output_schema=WORK_LOG_SCHEMA,
            system_prompt=system_prompt,
            temperature=0.1  # Low temperature for more deterministic extraction
        )
        
        # Convert date string to date object if needed
        if isinstance(raw_result.get('work_date'), str):
            try:
                date_obj = datetime.strptime(raw_result['work_date'], '%Y-%m-%d').date()
                raw_result['work_date'] = date_obj
            except ValueError:
                # Keep as string if parsing fails, Pydantic will handle validation
                pass
                
        # Convert to Pydantic model for validation
        return WorkLog(**raw_result)
    
    async def generate_invoice_items(self, work_logs: List[WorkLog], rate: float) -> List[InvoiceItem]:
        """
        Generate professional invoice line items from work logs.
        
        Args:
            work_logs: List of structured work log entries
            rate: Hourly rate to apply
            
        Returns:
            List of invoice line items
        """
        # Convert Pydantic models to dictionaries for JSON serialization
        work_logs_dicts = [log.model_dump() for log in work_logs]
        
        # Format the work logs for the prompt
        work_logs_text = json.dumps(work_logs_dicts, indent=2, default=str)
        
        prompt = format_prompt("invoice_item_generation", work_logs=work_logs_text)
        
        system_prompt = """
        You are an AI assistant that generates professional invoice line items.
        Create clear, concise descriptions that accurately reflect the work performed.
        Group similar tasks where appropriate to create more readable invoices.
        Ensure all required fields are included and calculations are accurate.
        """
        
        raw_result = await self.client.structured_generate(
            prompt=prompt,
            output_schema=INVOICE_ITEM_SCHEMA,
            system_prompt=system_prompt,
            temperature=0.3  # Slightly higher for more creative descriptions
        )
        
        if isinstance(raw_result, dict) and "error" in raw_result:
            # Return empty list in case of error
            return []
            
        # Apply rate to any items that don't have it and validate with Pydantic
        invoice_items = []
        for item_dict in raw_result:
            if 'rate' not in item_dict or not item_dict['rate']:
                item_dict['rate'] = rate
                
            if 'amount' not in item_dict or not item_dict['amount']:
                item_dict['amount'] = item_dict['hours'] * rate
                
            invoice_items.append(InvoiceItem(**item_dict))
            
        return invoice_items