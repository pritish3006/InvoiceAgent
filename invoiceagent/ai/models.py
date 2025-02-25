"""
Pydantic models for the AI components:
These models define the structure of data used in AI-related operations,
ensuring type safety and validation.
"""

from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field, field_validator, model_validator


class WorkLog(BaseModel):
    """Structured representation of a work log entry."""
    
    client: str = Field(..., description="Name of the client")
    project: str = Field(..., description="Name of the project")
    work_date: date  = Field(..., description="Date when work was performed")
    hours: float = Field(..., description="Hours spent on the task", ge=0.0)
    description: str = Field(..., description="Description of work performed")
    category: Optional[str] = Field(None, description="Work category or type")
    billable: bool = Field(True, description="Whether the work is billable")
    tags: List[str] = Field(default_factory=list, description="Tags for the work")
    
    @field_validator('hours')
    @classmethod
    def hours_must_be_positive(cls, v):
        """Validate that hours are positive."""
        if v < 0:
            raise ValueError('hours must be positive')
        return round(v, 2)  # Round to 2 decimal places
    

class InvoiceItem(BaseModel):
    """Single line item on an invoice."""
    
    description: str = Field(..., description="Description of the work performed")
    hours: float = Field(..., description="Quantity (usually hours)", ge=0.0)
    unit: str = Field("hour", description="Unit of measurement (hour, day, item, etc.)")
    rate: float = Field(..., description="Rate per unit", ge=0.0)
    amount: float = Field(..., description="Total amount (quantity * rate)", ge=0.0)
    category: Optional[str] = Field(None, description="Category of the work")
    
    @model_validator(mode='after')
    def validate_amount(self):
        """Validate that amount equals hours * rate."""
        expected = round(self.hours * self.rate, 2)
        if abs(self.amount - expected) > 0.01:  # Allow for tiny floating point differences
            raise ValueError(f'amount must equal hours * rate (expected {expected})')
        return self

class AIPromptTemplate(BaseModel):
    """Template for AI prompts."""
    
    name: str = Field(..., description="Name of the template")
    template: str = Field(..., description="Template text with {placeholders}")
    system_prompt: Optional[str] = Field(None, description="System prompt to use with this template")
    temperature: float = Field(0.7, description="Temperature for generation", ge=0.0, le=1.0)
    max_tokens: int = Field(1000, description="Maximum tokens to generate", ge=1)
    
    model_config = {
        "frozen": True  # Makes instances immutable
    } 