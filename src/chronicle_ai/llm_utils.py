"""
Chronicle AI - LLM Utilities

Low-level Ollama API integration and configuration.
"""

import os
import logging
import json
from typing import Optional

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


# Configuration via environment variables
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
OLLAMA_TIMEOUT = int(os.getenv("OLLAMA_TIMEOUT", "60"))

# Logging setup
logger = logging.getLogger(__name__)


class OllamaError(Exception):
    """Custom exception for Ollama-related errors."""
    pass


def _make_request(prompt: str, timeout: int = OLLAMA_TIMEOUT) -> Optional[str]:
    """
    Make a request to Ollama API.
    
    Args:
        prompt: The prompt to send to the model
        timeout: Request timeout in seconds
        
    Returns:
        Generated text response or None if failed
    """
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        if HTTPX_AVAILABLE:
            with httpx.Client(timeout=timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data.get("response", "").strip()
        elif REQUESTS_AVAILABLE:
            response = requests.post(url, json=payload, timeout=timeout)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
        else:
            logger.warning("Neither httpx nor requests library available")
            return None
    except Exception as e:
        logger.warning(f"Ollama request failed: {e}")
        return None


def is_ollama_available() -> bool:
    """
    Check if Ollama is running and accessible.
    
    Returns:
        True if Ollama is available, False otherwise
    """
    try:
        url = f"{OLLAMA_BASE_URL}/api/tags"
        if HTTPX_AVAILABLE:
            with httpx.Client(timeout=5) as client:
                response = client.get(url)
                return response.status_code == 200
        elif REQUESTS_AVAILABLE:
            response = requests.get(url, timeout=5)
            return response.status_code == 200
        return False
    except Exception:
        return False
