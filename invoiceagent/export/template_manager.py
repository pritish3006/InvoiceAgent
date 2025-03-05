"""
Template manager for invoice templates.

This module provides functionality for loading and validating invoice templates.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional

from invoiceagent.export.models import InvoiceTemplateConfig

logger = logging.getLogger(__name__)


def get_templates_dir() -> Path:
    """
    Get the directory where invoice template configurations are stored.

    Returns:
        Path to the templates directory
    """
    # Check if templates directory is specified in environment
    templates_dir = os.environ.get("INVOICEAGENT_TEMPLATES_DIR")
    if templates_dir:
        path = Path(templates_dir)
        if path.exists() and path.is_dir():
            return path

    # Default to the package templates directory
    return Path(__file__).parent.parent / "templates" / "invoice_configs"


def get_logo_path() -> Path:
    """
    Get the path to the logo file.

    Returns:
        Path to the logo file
    """
    return Path(__file__).parent.parent / "templates" / "logos" / "logo.png"


def list_available_templates() -> List[str]:
    """
    List all available invoice templates.

    Returns:
        List of template names (without .json extension)
    """
    templates_dir = get_templates_dir()
    template_files = list(templates_dir.glob("*.json"))
    return [template.stem for template in template_files]


def load_template(template_name: str) -> Optional[InvoiceTemplateConfig]:
    """
    Load an invoice template configuration.

    Args:
        template_name: Name of the template (without .json extension)

    Returns:
        InvoiceTemplateConfig if found, None otherwise
    """
    templates_dir = get_templates_dir()
    template_path = templates_dir / f"{template_name}.json"

    if not template_path.exists():
        logger.warning(f"Template '{template_name}' not found at {template_path}")
        # Fall back to default template if the requested one doesn't exist
        if template_name != "default":
            logger.info("Falling back to default template")
            return load_template("default")
        return None

    try:
        with open(template_path, "r") as f:
            template_data = json.load(f)
        
        # Validate and convert to model
        template_config = InvoiceTemplateConfig(**template_data)
        return template_config
    
    except json.JSONDecodeError as e:
        logger.error(f"Error parsing template '{template_name}': {str(e)}")
        return None
    except Exception as e:
        logger.error(f"Error loading template '{template_name}': {str(e)}")
        return None


def get_template_details() -> List[Dict[str, str]]:
    """
    Get details of all available templates.

    Returns:
        List of dictionaries with template name and description
    """
    template_names = list_available_templates()
    templates = []
    
    for name in template_names:
        template = load_template(name)
        if template:
            templates.append({
                "name": template.name,
                "description": template.description
            })
    
    return templates 