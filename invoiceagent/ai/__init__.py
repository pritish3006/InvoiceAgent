"""
AI module for the InvoiceAgent application.

Provides functionality for AI-powered processing of work logs and
generation of invoice content using Ollama.
"""

from invoiceagent.ai.models import AIPromptTemplate, InvoiceItem, WorkLog
from invoiceagent.ai.ollama_client import (OllamaClient, format_prompt,
                                           load_prompt_template)
from invoiceagent.ai.work_processor import WorkLogProcessor

__all__ = [
    "OllamaClient",
    "WorkLogProcessor",
    "WorkLog",
    "InvoiceItem",
    "AIPromptTemplate",
    "format_prompt",
    "load_prompt_template",
]
