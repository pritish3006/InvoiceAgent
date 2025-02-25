"""
Tests for the AI models in the InvoiceAgent application.
"""

import pytest
from datetime import date
from pydantic import ValidationError

from invoiceagent.ai.models import WorkLog, InvoiceItem


def test_work_log_validation():
    """Test that WorkLog validates correctly."""
    # Valid work log
    work_log = WorkLog(
        client="Test Client",
        project="Test Project",
        work_date=date(2023, 1, 1),
        hours=2.5,
        description="Test description",
        category="Development",
        billable=True
    )
    
    assert work_log.client == "Test Client"
    assert work_log.project == "Test Project"
    assert work_log.work_date == date(2023, 1, 1)
    assert work_log.hours == 2.5
    assert work_log.description == "Test description"
    assert work_log.category == "Development"
    assert work_log.billable is True
    assert work_log.tags == []
    
    # Test hours validation
    with pytest.raises(ValidationError):
        WorkLog(
            client="Test Client",
            project="Test Project",
            work_date=date(2023, 1, 1),
            hours=-1.0,  # Invalid: negative hours
            description="Test description"
        )
    
    # Test required fields
    with pytest.raises(ValidationError):
        WorkLog(
            client="Test Client",
            # Missing project
            work_date=date(2023, 1, 1),
            hours=2.5,
            description="Test description"
        )


def test_invoice_item_validation():
    """Test that InvoiceItem validates correctly."""
    # Valid invoice item
    item = InvoiceItem(
        description="Development work",
        hours=2.5,
        unit="hour",
        rate=100.0,
        amount=250.0
    )
    
    assert item.description == "Development work"
    assert item.hours == 2.5
    assert item.unit == "hour"
    assert item.rate == 100.0
    assert item.amount == 250.0
    
    # Test amount validation
    with pytest.raises(ValidationError):
        InvoiceItem(
            description="Development work",
            hours=2.5,
            unit="hour",
            rate=100.0,
            amount=300.0  # Invalid: doesn't match hours * rate
        )
    
    # Test required fields
    with pytest.raises(ValidationError):
        InvoiceItem(
            description="Development work",
            hours=2.5,
            # Missing rate
            unit="hour",
            amount=250.0
        ) 