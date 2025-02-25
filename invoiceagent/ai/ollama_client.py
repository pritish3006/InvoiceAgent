"""
Ollama API client for the Invoice Agent.

This module provides a lightweight wrapper around the Ollama API
for generating text completions and processing structured outputs.
"""

import json
import httpx
from typing import Dict, Any, Optional, List, Union

class OllamaClient:
    """A lightweight client for interacting with Ollama's API."""
    
    def __init__(
        self, 
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:8b",
        timeout: int = 60
    ):
        """
        Initialize the Ollama client.
        
        Args:
            base_url: The base URL for the Ollama API
            model: The model to use for generation
            timeout: Timeout for API requests in seconds
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        
    async def generate(
        self, 
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        """
        Generate text using the Ollama API.
        
        Args:
            prompt: The input text prompt
            system_prompt: Optional system prompt for context
            temperature: Generation temperature (higher = more creative)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            The generated text
        """
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        if system_prompt:
            payload["system"] = system_prompt
            
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            
            # Ollama streams responses, collect them
            full_response = ""
            for line in response.iter_lines():
                if not line:
                    continue
                    
                data = json.loads(line)
                if "response" in data:
                    full_response += data["response"]
                    
            return full_response
    
    async def structured_generate(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,  # Lower temperature for more deterministic outputs
    ) -> Dict[str, Any]:
        """
        Generate structured output by providing a JSON schema.
        
        Args:
            prompt: The input text prompt
            output_schema: JSON schema describing the expected output structure
            system_prompt: Optional system prompt for context
            temperature: Generation temperature
            
        Returns:
            Structured data according to the provided schema
        """
        schema_str = json.dumps(output_schema, indent=2)
        
        structured_prompt = f"""
        {prompt}
        
        Please provide your response in the following JSON format:
        
        {schema_str}
        
        Output only valid JSON that matches this schema with no additional text.
        """
        
        if system_prompt:
            system_prompt += "\nYou must respond with valid JSON matching the requested schema."
        else:
            system_prompt = "You must respond with valid JSON matching the requested schema."
        
        try:
            response = await self.generate(
                prompt=structured_prompt,
                system_prompt=system_prompt,
                temperature=temperature
            )
            
            # Extract JSON from response
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            # Parse the JSON response
            return json.loads(response.strip())
        except json.JSONDecodeError:
            # Fallback for malformed JSON
            return {"error": "Failed to parse structured response from the model"}


# Convenience functions for template handling

def load_prompt_template(template_name: str) -> str:
    """
    Load a prompt template from the templates directory.
    
    Args:
        template_name: Name of the template file without extension
        
    Returns:
        The template content as a string
    """
    # TODO: Implement template loading from file
    # This is a placeholder for demonstration
    templates = {
        "work_log_processing": """
        You are an invoice generation assistant. You need to convert the following 
        work log entry into a structured format for invoice generation:
        
        Work log: {work_log}
        
        Extract the following information:
        - Client name
        - Project name
        - Date
        - Hours worked
        - Description of work
        - Category
        """,
        
        "invoice_item_generation": """
        You are an invoice generation assistant. Based on the following work logs,
        generate professional invoice line items:
        
        Work logs:
        {work_logs}
        
        Generate concise, professional descriptions for each invoice line item.
        """
    }
    
    return templates.get(template_name, "")


def format_prompt(template_name: str, **kwargs) -> str:
    """
    Format a prompt template with the provided variables.
    
    Args:
        template_name: Name of the template to load
        **kwargs: Variables to format the template with
        
    Returns:
        The formatted prompt
    """
    template = load_prompt_template(template_name)
    return template.format(**kwargs) 