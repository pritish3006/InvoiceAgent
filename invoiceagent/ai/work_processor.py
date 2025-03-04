"""
Work log processing module for InvoiceAgent.

Handles the conversion of free-form work logs to structured data
and generation of invoice line items.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from invoiceagent.ai.models import InvoiceItem, WorkLog
from invoiceagent.ai.ollama_client import (OllamaClient, OllamaClientError,
                                          format_prompt,
                                          load_prompt_template_as_model)

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
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["client", "project", "work_date", "hours", "description"],
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
            "category": {"type": "string"},
        },
        "required": ["description", "hours", "unit", "rate", "amount"],
    },
}


class WorkLogProcessor:
    """
    Processes work logs and generates structured invoice data.
    """

    def __init__(
        self, 
        ollama_client: Optional[OllamaClient] = None,
        cache_dir: Optional[str] = None
    ):
        """
        Initialize the work log processor.

        Args:
            ollama_client: OllamaClient instance to use, or None to create a new one
            cache_dir: Directory to store cache files (None for no caching)
        """
        # Set up cache directory
        if cache_dir is None:
            # Default to ~/.invoiceagent/cache
            cache_dir = os.path.expanduser("~/.invoiceagent/cache")
            os.makedirs(cache_dir, exist_ok=True)
        
        # Create or use provided Ollama client
        self.client = ollama_client or OllamaClient(cache_dir=cache_dir)

    async def process_free_form_log(self, log_text: str) -> WorkLog:
        """
        Process a free-form work log entry and convert it to structured data.

        Args:
            log_text: The free-form work log text

        Returns:
            Structured work log data as a WorkLog model
            
        Raises:
            OllamaClientError: If there's an error communicating with Ollama
            ValueError: If the response cannot be parsed into a valid WorkLog
        """
        # Load template as model to get optimal parameters
        template = load_prompt_template_as_model("work_log_processing")
        
        # Format the prompt with the work log text
        prompt = format_prompt("work_log_processing", work_log=log_text)

        print(f"DEBUG: Sending prompt to Ollama: {prompt[:100]}...")

        try:
            raw_result = await self.client.structured_generate(
                prompt=prompt,
                output_schema=WORK_LOG_SCHEMA,
                system_prompt=template.system_prompt,
                temperature=template.temperature,
                max_tokens=template.max_tokens
            )
            
            print(f"DEBUG: Raw result from Ollama: {raw_result}")
            
            # Check if we got an error response
            if isinstance(raw_result, dict) and "error" in raw_result:
                error_msg = raw_result["error"]
                raw_response = raw_result.get("raw_response", "")
                raise ValueError(f"Failed to process work log: {error_msg}\nRaw response: {raw_response}")
            
            # Try to convert response to WorkLog model
            try:
                # If raw_result contains nested JSON (as a string), try to parse it
                if isinstance(raw_result, str):
                    print(f"DEBUG: Parsing string result: {raw_result}")
                    import json
                    try:
                        raw_result = json.loads(raw_result)
                    except json.JSONDecodeError as e:
                        print(f"DEBUG: JSON decode error: {str(e)}")
                        raise ValueError(f"Failed to parse AI response: {str(e)}")
                
                print(f"DEBUG: Creating WorkLog from: {raw_result}")
                work_log = WorkLog(**raw_result)
                return work_log
            except Exception as e:
                print(f"DEBUG: Error creating WorkLog: {str(e)}")
                raise ValueError(f"Failed to create WorkLog model: {str(e)}")
                
        except Exception as e:
            print(f"DEBUG: Unexpected error in processing: {str(e)}")
            raise ValueError(f"Unexpected error: {str(e)}")

    async def generate_invoice_items(
        self, work_logs: List[WorkLog], rate: float
    ) -> List[InvoiceItem]:
        """
        Generate professional invoice line items from work logs.

        Args:
            work_logs: List of structured work log entries
            rate: Hourly rate to apply

        Returns:
            List of invoice line items
            
        Raises:
            OllamaClientError: If there's an error communicating with Ollama
            ValueError: If the response cannot be parsed into valid InvoiceItems
        """
        # Load template as model to get optimal parameters
        template = load_prompt_template_as_model("invoice_item_generation")
        
        # Convert Pydantic models to dictionaries for JSON serialization
        work_logs_dicts = [log.model_dump() for log in work_logs]

        # Format the work logs for the prompt
        work_logs_text = json.dumps(work_logs_dicts, indent=2, default=str)

        prompt = format_prompt("invoice_item_generation", work_logs=work_logs_text)

        try:
            raw_result = await self.client.structured_generate(
                prompt=prompt,
                output_schema=INVOICE_ITEM_SCHEMA,
                system_prompt=template.system_prompt,
                temperature=template.temperature,
                use_cache=True,
                max_retries=2
            )

            # Check for error in response
            if isinstance(raw_result, dict) and "error" in raw_result:
                raise ValueError(f"Failed to generate invoice items: {raw_result['error']}")

            # Apply rate to any items that don't have it and validate with Pydantic
            invoice_items = []
            for item_dict in raw_result:
                if "rate" not in item_dict or not item_dict["rate"]:
                    item_dict["rate"] = rate

                if "amount" not in item_dict or not item_dict["amount"]:
                    item_dict["amount"] = item_dict["hours"] * rate

                invoice_items.append(InvoiceItem(**item_dict))

            return invoice_items
            
        except OllamaClientError as e:
            # Re-raise with more context
            raise OllamaClientError(f"Error generating invoice items: {str(e)}")
        except Exception as e:
            # Catch any other errors and provide context
            raise ValueError(f"Failed to generate invoice items: {str(e)}")
            
    async def generate_invoice_summary(
        self, invoice_details: Dict[str, Any]
    ) -> str:
        """
        Generate a professional summary for an invoice.
        
        Args:
            invoice_details: Dictionary with invoice details including items and client info
            
        Returns:
            A professional summary for the invoice
            
        Raises:
            OllamaClientError: If there's an error communicating with Ollama
            ValueError: If the response cannot be processed
        """
        # Load template as model to get optimal parameters
        template = load_prompt_template_as_model("invoice_summary")
        
        # Format the invoice details for the prompt
        invoice_details_text = json.dumps(invoice_details, indent=2, default=str)
        
        prompt = format_prompt("invoice_summary", invoice_details=invoice_details_text)
        
        try:
            # For summary, we just want text, not structured data
            summary = await self.client.generate(
                prompt=prompt,
                system_prompt=template.system_prompt,
                temperature=template.temperature,
                max_tokens=template.max_tokens,
                use_cache=True
            )
            
            # Clean up the summary
            summary = summary.strip()
            
            return summary
            
        except OllamaClientError as e:
            # Re-raise with more context
            raise OllamaClientError(f"Error generating invoice summary: {str(e)}")
        except Exception as e:
            # Catch any other errors and provide context
            raise ValueError(f"Failed to generate invoice summary: {str(e)}")
