"""
Pydantic models for AI-related data structures.

This module defines the data models used for AI processing,
including work logs, invoice items, and prompt templates.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class WorkLog(BaseModel):
    """
    Structured representation of a work log entry.
    """
    client: str
    project: str
    work_date: Union[date, str] = Field(default_factory=lambda: date.today())
    hours: float
    description: str
    category: Optional[str] = None
    billable: bool = True
    tags: List[str] = Field(default_factory=list)

    @field_validator("work_date", mode="before")
    @classmethod
    def parse_date(cls, value: Any) -> Union[date, str]:
        """
        Parse date from string if needed.
        """
        if isinstance(value, (date, datetime)):
            return value
        if isinstance(value, str):
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return value
        return value


class InvoiceItem(BaseModel):
    """
    Representation of an invoice line item.
    """
    description: str
    hours: float
    unit: str = "hour"
    rate: float
    amount: float
    category: Optional[str] = None

    @field_validator("amount", mode="before")
    @classmethod
    def calculate_amount(cls, value: Any, values: Dict[str, Any]) -> float:
        """
        Calculate amount if not provided.
        """
        if value is not None:
            return float(value)
        
        hours = values.get("hours", 0)
        rate = values.get("rate", 0)
        
        if hours is not None and rate is not None:
            return float(hours) * float(rate)
        
        return 0.0


class AIPromptTemplate(BaseModel):
    """
    Model for AI prompt templates with metadata.
    """
    name: str
    template: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def format(self, **kwargs: Any) -> str:
        """
        Format the template with the provided variables.
        
        Args:
            **kwargs: Variables to format the template with
            
        Returns:
            The formatted prompt
        """
        return self.template.format(**kwargs)
