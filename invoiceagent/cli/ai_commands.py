"""
CLI commands for AI-related functionality.

This module provides commands for testing and managing AI features.
"""

import asyncio
import json
import os
from typing import Optional

import click

from invoiceagent.ai.ollama_client import (OllamaClient, OllamaClientError,
                                          format_prompt,
                                          load_prompt_template)
from invoiceagent.ai.work_processor import WorkLogProcessor
from invoiceagent.cli.utils import (console, print_error, print_info,
                                   print_success, print_warning)


@click.group(name="ai")
def ai_commands():
    """AI-related commands."""
    pass


@ai_commands.command(name="test-connection")
@click.option(
    "--base-url",
    default="http://localhost:11434",
    help="Base URL for the Ollama API",
)
@click.option(
    "--model",
    default="llama3.2:8b",
    help="Model to use for testing",
)
def test_connection(base_url: str, model: str):
    """Test connection to the Ollama API."""
    async def _test_connection():
        client = OllamaClient(base_url=base_url, model=model)
        
        try:
            # Check if Ollama is running
            if not await client._check_ollama_status():
                print_error(f"Cannot connect to Ollama at {base_url}")
                print_info("Make sure Ollama is running and accessible.")
                return
                
            print_success(f"Successfully connected to Ollama at {base_url}")
            
            # Test a simple generation
            print_info("Testing text generation...")
            response = await client.generate(
                "Hello, I'm testing the InvoiceAgent Ollama integration. Please respond with a short greeting.",
                temperature=0.7,
                max_tokens=100
            )
            
            print_success("Generation successful!")
            console.print("\n[bold]Response:[/bold]")
            console.print(response)
            
        except OllamaClientError as e:
            print_error(f"Error: {str(e)}")
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
    
    # Run the async function
    asyncio.run(_test_connection())


@ai_commands.command(name="process-log")
@click.argument("log_text")
@click.option(
    "--base-url",
    default="http://localhost:11434",
    help="Base URL for the Ollama API",
)
@click.option(
    "--model",
    default="llama3.2:8b",
    help="Model to use for processing",
)
@click.option(
    "--cache-dir",
    default=None,
    help="Directory to store cache files",
)
def process_log(log_text: str, base_url: str, model: str, cache_dir: Optional[str]):
    """Process a work log entry and convert it to structured data."""
    async def _process_log():
        # Set up the Ollama client
        client = OllamaClient(base_url=base_url, model=model, cache_dir=cache_dir)
        
        # Create a work log processor
        processor = WorkLogProcessor(ollama_client=client)
        
        try:
            # Process the log
            print_info("Processing work log...")
            result = await processor.process_free_form_log(log_text)
            
            print_success("Processing successful!")
            console.print("\n[bold]Structured Result:[/bold]")
            console.print(json.dumps(result.model_dump(), indent=2, default=str))
            
        except OllamaClientError as e:
            print_error(f"Error: {str(e)}")
        except Exception as e:
            print_error(f"Unexpected error: {str(e)}")
    
    # Run the async function
    asyncio.run(_process_log())


@ai_commands.command(name="list-templates")
@click.option(
    "--show-content",
    is_flag=True,
    help="Show the content of each template",
)
def list_templates(show_content: bool):
    """List available prompt templates."""
    from invoiceagent.ai.ollama_client import get_prompt_templates_dir
    
    templates_dir = get_prompt_templates_dir()
    
    if not os.path.exists(templates_dir):
        print_warning(f"Templates directory not found: {templates_dir}")
        return
        
    # Get all .txt files in the templates directory
    template_files = [f for f in os.listdir(templates_dir) if f.endswith(".txt")]
    
    if not template_files:
        print_warning("No templates found.")
        return
        
    print_success(f"Found {len(template_files)} templates:")
    
    for template_file in sorted(template_files):
        template_name = os.path.splitext(template_file)[0]
        console.print(f"\n[bold]{template_name}[/bold]")
        
        # Check if there's a metadata file
        metadata_file = os.path.join(templates_dir, f"{template_name}.json")
        if os.path.exists(metadata_file):
            with open(metadata_file, "r") as f:
                metadata = json.load(f)
                console.print(f"Temperature: {metadata.get('temperature', 0.7)}")
                console.print(f"Max tokens: {metadata.get('max_tokens', 1000)}")
                if metadata.get("system_prompt"):
                    console.print(f"Has system prompt: Yes")
        
        if show_content:
            template_content = load_prompt_template(template_name)
            console.print("\n[italic]Template content:[/italic]")
            console.print(template_content)
            console.print("\n" + "-" * 80)


if __name__ == "__main__":
    ai_commands() 