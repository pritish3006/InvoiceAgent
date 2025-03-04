"""
Configuration module for InvoiceAgent.

This module provides configuration management for the application.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class Config(BaseModel):
    """Application configuration."""
    
    database_path: str = str(Path.home() / ".invoiceagent" / "invoiceagent.db")
    templates_dir: str = str(Path(__file__).parent.parent / "ai" / "templates")
    cache_dir: str = str(Path.home() / ".invoiceagent" / "cache")
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.2:8b"


_config: Optional[Config] = None


def get_config() -> Config:
    """Get the application configuration.
    
    Returns:
        The application configuration
    """
    global _config
    
    if _config is None:
        # Create config directory if it doesn't exist
        config_dir = Path.home() / ".invoiceagent"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        # Load config from environment variables or use defaults
        _config = Config(
            database_path=os.getenv("INVOICEAGENT_DB_PATH", Config().database_path),
            templates_dir=os.getenv("INVOICEAGENT_TEMPLATES_DIR", Config().templates_dir),
            cache_dir=os.getenv("INVOICEAGENT_CACHE_DIR", Config().cache_dir),
            ollama_url=os.getenv("INVOICEAGENT_OLLAMA_URL", Config().ollama_url),
            ollama_model=os.getenv("INVOICEAGENT_OLLAMA_MODEL", Config().ollama_model),
        )
    
    return _config
