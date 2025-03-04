"""
Ollama API client for the Invoice Agent.

This module provides a lightweight wrapper around the Ollama API
for generating text completions and processing structured outputs.
"""

import asyncio
import functools
import hashlib
import json
import logging
import os
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import requests

import httpx
import yaml
from pydantic import ValidationError
from aiohttp import ClientConnectorError, ClientOSError, ClientResponseError, ClientSession, ClientTimeout

from invoiceagent.ai.models import AIPromptTemplate
from invoiceagent.config import get_config

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 60  # seconds

class OllamaClientError(Exception):
    """Base exception for Ollama client errors."""
    pass


class OllamaConnectionError(OllamaClientError):
    """Exception raised when connection to Ollama fails."""
    pass


class OllamaResponseError(OllamaClientError):
    """Exception raised when Ollama returns an error response."""
    pass


class OllamaClient:
    """A lightweight client for interacting with Ollama's API."""

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3.2:latest",
        timeout: int = 60,
        cache_dir: Optional[str] = None,
        cache_ttl: int = 3600,  # 1 hour cache TTL by default
    ):
        """
        Initialize the Ollama client.

        Args:
            base_url: Base URL for the Ollama API
            model: Default model to use
            timeout: HTTP timeout in seconds
            cache_dir: Directory to store cache files
            cache_ttl: Cache TTL in seconds
        """
        self.base_url = base_url
        self.model = model
        self.timeout = timeout
        self.cache_dir = cache_dir
        self.cache_ttl = cache_ttl
        self.cache = {}
        
        # Initialize aiohttp session
        self.session = None
    
    async def _ensure_session(self):
        """Ensure an aiohttp session exists."""
        if self.session is None or self.session.closed:
            self.session = ClientSession(timeout=ClientTimeout(total=self.timeout))
        return self.session

    async def __aenter__(self):
        """Enter async context manager."""
        await self._ensure_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit async context manager."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    async def close(self):
        """Explicitly close the client session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

    def __del__(self):
        """Ensure resources are cleaned up."""
        if self.session and not self.session.closed:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    loop.run_until_complete(self.close())
            except Exception:
                pass  # Ignore errors during cleanup

    async def _check_ollama_status(self) -> bool:
        """
        Check if Ollama is running.

        Returns:
            True if Ollama is running, False otherwise
        """
        try:
            # Use requests directly for simplicity
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Error checking Ollama status: {str(e)}")
            return False

    def _get_cache_key(self, prompt: str, system_prompt: Optional[str], temperature: float, max_tokens: int) -> str:
        """
        Generate a cache key for the given parameters.
        
        Args:
            prompt: The input text prompt
            system_prompt: Optional system prompt for context
            temperature: Generation temperature
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            A hash string to use as cache key
        """
        # Create a string with all parameters
        cache_str = f"{self.model}:{prompt}:{system_prompt}:{temperature}:{max_tokens}"
        # Create a hash of the string
        return hashlib.md5(cache_str.encode()).hexdigest()

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """
        Try to get a response from the cache.
        
        Args:
            cache_key: The cache key to look up
            
        Returns:
            The cached response if found and valid, None otherwise
        """
        if not self.cache_dir:
            return None
            
        cache_file = Path(self.cache_dir) / f"{cache_key}.json"
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, "r") as f:
                cache_data = json.load(f)
                
            # Check if cache is expired
            cache_time = datetime.fromisoformat(cache_data["timestamp"])
            if datetime.now() - cache_time > timedelta(seconds=self.cache_ttl):
                return None
                
            return cache_data["response"]
        except (json.JSONDecodeError, KeyError, ValueError):
            # Invalid cache file
            return None

    def _save_to_cache(self, cache_key: str, response: str) -> None:
        """
        Save a response to the cache.
        
        Args:
            cache_key: The cache key to use
            response: The response to cache
        """
        if not self.cache_dir:
            return
            
        cache_file = Path(self.cache_dir) / f"{cache_key}.json"
        cache_data = {
            "timestamp": datetime.now().isoformat(),
            "response": response
        }
        
        with open(cache_file, "w") as f:
            json.dump(cache_data, f)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        top_p: float = 0.9,
        model: str = "llama3.2:latest",
        use_cache: bool = True,
    ) -> str:
        """
        Generate text using Ollama.

        Args:
            prompt: The prompt to generate text from.
            system_prompt: The system prompt to use.
            temperature: The temperature to use for generation.
            max_tokens: The maximum number of tokens to generate.
            top_p: The top_p value to use for generation.
            model: The model to use for generation.
            use_cache: Whether to use the cache for generation.

        Returns:
            The generated text.

        Raises:
            OllamaClientError: If there is an error with the Ollama client.
        """
        if not await self._check_ollama_status():
            raise OllamaClientError(
                "Failed to connect to Ollama API, "
                "please ensure ollama is running and accesible"
            )
        
        # Diagnostic logging
        print(f"[DEBUG] Using model: {model}")
        print(f"[DEBUG] Connecting to Ollama at: {self.base_url}")
        
        # Try to get from cache if caching is enabled
        if use_cache and self.cache:
            cache_key = hashlib.md5(
                f"{prompt}{system_prompt}{temperature}{max_tokens}{top_p}{model}".encode()
            ).hexdigest()
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.debug("Using cached result for prompt: %s", prompt[:100])
                return cached_result
        
        # Prepare payload
        payload = {
            "model": model,
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }
        # if system prompt is provided, add it to the payload
        if system_prompt:
            payload["system"] = system_prompt
            
        # Send the request
        try:
            await self._ensure_session()
            response_data = await self._request("/api/generate", payload)
            
            # Extract the response
            if "response" not in response_data:
                raise OllamaClientError("Unexpected response format from Ollama API")
                
            response_text = response_data["response"]
            
            # Cache the result if caching is enabled
            if use_cache and self.cache:
                self.cache[cache_key] = response_text
                
            return response_text
            
        except Exception as e:
            raise OllamaClientError(f"Error generating text: {str(e)}")

    async def structured_generate(
        self,
        prompt: str,
        output_schema: Dict[str, Any],
        system_prompt: Optional[str] = None,
        temperature: float = 0.2,  # Lower temperature for more deterministic outputs
        use_cache: bool = True,
        max_tokens: int = 2000,
        top_p: float = 0.9,
        model: str = "llama3.2:latest",
        max_retries: int = 2,
    ) -> Dict[str, Any]:
        """
        Generate structured data from a prompt.

        Args:
            prompt: The prompt to generate structured data from.
            output_schema: The schema to use for the structured data output.
            system_prompt: The system prompt to use.
            temperature: The temperature to use for generation.
            use_cache: Whether to use caching for responses.
            max_tokens: The maximum number of tokens to generate.
            top_p: The top_p value to use for generation.
            model: The model to use for generation.
            max_retries: The maximum number of retries for parsing failures.

        Returns:
            The generated structured data.

        Raises:
            OllamaClientError: If there is an error with the Ollama client.
        """
        # Add check for Ollama status
        if not await self._check_ollama_status():
            raise OllamaClientError(
                "Failed to connect to Ollama API, "
                "please ensure ollama is running and accessible"
            )

        # Try to get from cache if caching is enabled
        cache_key = None
        if use_cache and self.cache:
            cache_key = hashlib.md5(
                f"{prompt}{system_prompt}{temperature}{max_tokens}{top_p}{model}{output_schema}".encode()
            ).hexdigest()
            cached_result = self.cache.get(cache_key)
            if cached_result:
                logger.debug("Using cached result for prompt: %s", prompt[:100])
                return json.loads(cached_result)

        # Construct base system prompt
        base_system_prompt = "You are a helpful assistant that responds with structured data only."
        
        if system_prompt:
            combined_system_prompt = f"{base_system_prompt}\n\n{system_prompt}"
        else:
            combined_system_prompt = base_system_prompt
            
        # Add information about the expected output format
        schema_str = json.dumps(output_schema, indent=2)
        combined_system_prompt += f"\n\nYour response must be valid JSON that matches this schema:\n{schema_str}"
        
        # Format the user message to include instructions about returning JSON
        formatted_prompt = f"{prompt}\n\nRespond ONLY with a JSON object matching the specified schema."
        
        logger.debug("Using model: %s", model)
        logger.debug("Using system prompt: %s", combined_system_prompt[:100])
        
        for attempt in range(max_retries + 1):
            try:
                # Use the chat API endpoint for better structured outputs
                data = {
                    "model": model,
                    "messages": [
                        {"role": "system", "content": combined_system_prompt},
                        {"role": "user", "content": formatted_prompt}
                    ],
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "top_p": top_p,
                    "format": "json",  # Request JSON format directly
                    "stream": False    # Request complete response
                }
                
                # Send the request to the chat endpoint
                response_data = await self._request("/api/chat", data)
                logger.debug("Raw response from chat endpoint: %s", response_data)
                
                # Process the response based on its structure
                json_content = None
                
                # Extract content from the response
                if "message" in response_data and "content" in response_data["message"]:
                    # Handle chat endpoint response
                    json_content = response_data["message"]["content"]
                elif "response" in response_data:
                    # Handle generate endpoint response
                    json_content = response_data["response"]
                
                if json_content is not None:
                    # Process the content to extract the structured data
                    result = self._extract_json_from_content(json_content)
                    
                    # Save to cache if caching is enabled
                    if use_cache and self.cache and cache_key:
                        self.cache[cache_key] = json.dumps(result)
                        
                    return result
                else:
                    raise ValueError(f"No usable content found in response: {response_data}")
                
            except (ValueError, json.JSONDecodeError) as e:
                logger.warning("Error in attempt %d: %s", attempt + 1, str(e))
                if attempt == max_retries:
                    logger.error("All retries failed: %s", str(e))
                    return {
                        "error": f"Failed to parse structured response: {str(e)}",
                        "raw_response": str(response_data) if 'response_data' in locals() else "No response"
                    }
                
                # Lower temperature for retry to get more deterministic output
                temperature = max(0.1, temperature * 0.8)
                logger.info("Retrying with temperature: %f", temperature)
                continue
    
    def _extract_json_from_content(self, content: Union[str, Dict]) -> Dict[str, Any]:
        """
        Extract a JSON object from content that might be a string or a dict.
        
        Args:
            content: The content to extract JSON from
            
        Returns:
            The extracted JSON as a dictionary
            
        Raises:
            ValueError: If the content cannot be parsed as JSON
        """
        # If it's already a dict, return it directly
        if isinstance(content, dict):
            return content
        
        # Otherwise, try to parse it as a string
        content_str = content.strip()
        
        # Handle potential markdown code blocks
        if content_str.startswith("```json"):
            content_str = content_str[7:]
        elif content_str.startswith("```"):
            content_str = content_str[3:]
        
        if content_str.endswith("```"):
            content_str = content_str[:-3]
            
        content_str = content_str.strip()
        
        try:
            return json.loads(content_str)
        except json.JSONDecodeError as e:
            # Try to extract JSON from the content if it contains other text
            import re
            json_pattern = r'(\{.*\})'
            match = re.search(json_pattern, content_str, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
                    
            # If we get here, we couldn't parse the JSON
            logger.error("Failed to parse JSON from content: %s", content_str)
            raise ValueError(f"Failed to parse JSON from content: {e}")

    async def _request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Make a request to the Ollama API.

        Args:
            endpoint: The endpoint to make the request to.
            data: The data to send with the request.

        Returns:
            The response from the Ollama API.

        Raises:
            OllamaClientError: If there is an error with the Ollama client.
        """
        url = f"{self.base_url}{endpoint}"
        logger.debug("Making request to: %s", url)
        logger.debug("Request data: %s", data)
        
        await self._ensure_session()
        
        try:
            async with self.session.post(url, json=data) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("Ollama API error: %s", error_text)
                    raise OllamaClientError(
                        f"Ollama API error: {response.status} for url '{url}'\n"
                        f"Response: {error_text}"
                    )
                
                # Check content type to handle different response formats
                content_type = response.headers.get('content-type', '').lower()
                logger.debug("Response content type: %s", content_type)
                
                # Handle streaming NDJSON responses
                if content_type == 'application/x-ndjson':
                    logger.debug("Handling NDJSON streaming response")
                    full_response = ""
                    final_response = {}
                    
                    # Process the NDJSON stream line by line
                    async for line in response.content:
                        line_str = line.decode('utf-8').strip()
                        if not line_str:
                            continue
                            
                        try:
                            chunk = json.loads(line_str)
                            logger.debug("Received chunk: %s", chunk)
                            
                            # For chat endpoint
                            if 'message' in chunk and 'content' in chunk['message']:
                                if 'message' not in final_response:
                                    final_response['message'] = {'content': ''}
                                final_response['message']['content'] += chunk['message']['content']
                            
                            # For generate endpoint
                            elif 'response' in chunk:
                                full_response += chunk['response']
                                
                            # Store other relevant fields
                            for key in ['model', 'created_at', 'done']:
                                if key in chunk:
                                    final_response[key] = chunk[key]
                                    
                        except json.JSONDecodeError as e:
                            logger.warning("Failed to parse NDJSON line: %s", e)
                    
                    # If we got responses from generate endpoint
                    if full_response and 'message' not in final_response:
                        final_response['response'] = full_response
                        
                    logger.debug("Final combined response: %s", final_response)
                    return final_response
                else:
                    # Handle regular JSON response
                    return await response.json()
                
        except Exception as e:
            logger.error("Error in request: %s", e)
            raise OllamaClientError(f"Error in request: {str(e)}")


# Prompt template management

def get_prompt_templates_dir() -> Path:
    """
    get the directory where prompt templates are stored.
    
    Returns:
        path to the templates directory
    """
    # Check for environment variable first
    env_dir = os.environ.get("INVOICEAGENT_TEMPLATES_DIR")
    if env_dir:
        return Path(env_dir)
        
    # Default to package directory
    return Path(__file__).parent / "templates"


def load_prompt_template(template_name: str) -> str:
    """
    load a prompt template from the templates directory.

    Args:
        template_name: name of the template file without extension

    Returns:
        the template content as a string
    """
    templates_dir = get_prompt_templates_dir()
    template_file = templates_dir / f"{template_name}.txt"
    
    logger.debug("Loading template from: %s", template_file)
    
    # Check if template file exists
    if template_file.exists():
        with open(template_file, "r") as f:
            content = f.read()
            logger.debug("Loaded template content (first 100 chars): %s", content[:100])
            return content
    
    # Fallback to built-in templates
    logger.warning("Template file not found, using built-in template")
    built_in_templates = {
        "work_log_processing": """
        you are a capable AI agent that is tasked with appropriately logging the work reported by the user.
        you will be given user entry on the work they did and some context around it - this can include: task description, project name, client name, time taken, date, etc.
        based on the above entered information, you need to create a structured work log entry for invoice generation using the provided schema.
        work log entry into a structured format for invoice generation:

        work log schema: {work_log}

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
        """,
    }

    template = built_in_templates.get(template_name, "")
    logger.debug("Using built-in template (first 100 chars): %s", template[:100])
    return template


def load_prompt_template_as_model(template_name: str) -> AIPromptTemplate:
    """
    Load a prompt template and convert it to an AIPromptTemplate model.
    
    Args:
        template_name: Name of the template file without extension
        
    Returns:
        AIPromptTemplate model
    """
    template_text = load_prompt_template(template_name)
    
    # Try to load metadata from JSON file
    templates_dir = get_prompt_templates_dir()
    metadata_file = templates_dir / f"{template_name}.json"
    
    if metadata_file.exists():
        with open(metadata_file, "r") as f:
            metadata = json.load(f)
    else:
        # Default metadata
        metadata = {
            "system_prompt": None,
            "temperature": 0.7,
            "max_tokens": 1000
        }
    
    return AIPromptTemplate(
        name=template_name,
        template=template_text,
        system_prompt=metadata.get("system_prompt"),
        temperature=metadata.get("temperature", 0.7),
        max_tokens=metadata.get("max_tokens", 1000)
    )


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
    logger.debug("Formatting template with kwargs: %s", kwargs)
    
    try:
        # The simplest approach: escape all curly braces that aren't format placeholders
        escaped_template = template.replace("{", "{{").replace("}", "}}")
        
        # Restore the format placeholders for our variables
        for key in kwargs:
            placeholder = f"{{{key}}}"  # e.g., {work_log}
            escaped_placeholder = f"{{{{{key}}}}}"  # e.g., {{work_log}}
            escaped_template = escaped_template.replace(escaped_placeholder, placeholder)
        
        # Now format with kwargs
        formatted = escaped_template.format(**kwargs)
        logger.debug("Successfully formatted template")
        return formatted
        
    except KeyError as e:
        logger.error("Failed to format template: %s", str(e))
        raise


@functools.lru_cache(maxsize=32)
def get_cached_prompt_template(template_name: str) -> str:
    """
    Get a prompt template with caching.
    
    Args:
        template_name: Name of the template to load
        
    Returns:
        The template content as a string
    """
    return load_prompt_template(template_name)
