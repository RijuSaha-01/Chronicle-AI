"""
Chronicle AI - LLM Client

Integration with local Ollama Llama 3.2 for narrative and title generation.
"""

import os
import json
import logging
from typing import Optional

from .style_guide import CinematicStyleGuide

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


# Initialize the Cinematic Style Guide
style_guide = CinematicStyleGuide()


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


def generate_narrative(raw_text: str, mood: Optional[str] = None) -> str:
    """
    Generate a narrative paragraph from raw diary text with cinematic enhancement.
    
    Uses Ollama Llama 3.2 to transform diary entries into engaging
    narrative prose, enriched with cinematic visual direction and sensory layers.
    
    Args:
        raw_text: The user's raw diary entry text
        mood: Optional mood to guide the cinematic style
        
    Returns:
        Generated narrative paragraph or fallback text
    """
    if not raw_text or not raw_text.strip():
        return "No diary content provided for this day."
    
    # 1. Detect mood if not explicitly provided
    if not mood:
        lower_text = raw_text.lower()
        if any(w in lower_text for w in ["productive", "finished", "accomplished", "work", "busy"]):
            mood = "productive"
        elif any(w in lower_text for w in ["sad", "reflective", "thought", "lonely", "missing"]):
            mood = "reflective"
        elif any(w in lower_text for w in ["stress", "deadline", "fast", "rushed", "panic"]):
            mood = "stressful"
        elif any(w in lower_text for w in ["relax", "chill", "calm", "peace", "quiet"]):
            mood = "relaxed"
        elif any(w in lower_text for w in ["mystery", "weird", "strange", "dark", "unknown"]):
            mood = "mysterious"
        else:
            mood = "neutral"
    
    # 2. Prepare the base prompt
    base_prompt = f"""You are a creative writer helping to transform personal diary entries into engaging narrative prose.

Transform the following diary entry into a short, cinematic narrative paragraph (2-4 sentences). 
Write in third person, present tense, as if describing scenes from a movie about the protagonist's life.
Keep it personal and emotionally resonant while maintaining the key events and feelings.

Diary entry:
{raw_text}"""

    # 3. Enhance the prompt with cinematic instructions
    prompt = style_guide.enhance_prompt(base_prompt, mood)
    prompt += "\n\nNarrative (2-4 sentences, cinematic style):"

    # 4. Request from LLM
    result = _make_request(prompt)
    
    if result:
        # 5. Enrich the output with sensory layers
        return style_guide.add_sensory_layer(result)
    
    # Fallback when Ollama is not available
    logger.info("Using fallback narrative (Ollama offline)")
    fallback = f"[Demo narrative] {raw_text[:200]}{'...' if len(raw_text) > 200 else ''}"
    return style_guide.add_sensory_layer(fallback)


def generate_title(text: str) -> str:
    """
    Generate a catchy episode title from diary text.
    
    Creates a short, memorable title (3-7 words) that captures
    the essence of the diary entry like a TV episode title.
    
    Args:
        text: The diary entry text (raw or narrative)
        
    Returns:
        Generated episode title or fallback
    """
    if not text or not text.strip():
        return "Untitled Episode"
    
    prompt = f"""You are creating episode titles for a personal life documentary series.

Generate a single catchy, evocative episode title (3-7 words) for this diary entry.
The title should feel like a TV episode title - intriguing, memorable, and capturing the essence of the day.
Only output the title, nothing else. No quotes, no explanation.

Diary content:
{text[:500]}

Episode title:"""

    result = _make_request(prompt, timeout=30)
    
    if result:
        # Clean up the result (remove quotes, extra whitespace)
        title = result.strip().strip('"\'').strip()
        # Ensure reasonable length
        words = title.split()
        if len(words) > 8:
            title = ' '.join(words[:7])
        return title
    
    # Fallback when Ollama is not available
    logger.info("Using fallback title (Ollama offline)")
    words = text.split()[:3]
    return f"Episode: {' '.join(words)}..."


def ensure_narrative(entry) -> None:
    """
    Ensure an entry has narrative_text, generating if needed.
    
    Modifies the entry object in place. If narrative_text is already
    set, this function does nothing.
    
    Args:
        entry: Entry object to update (modified in place)
    """
    if not entry.narrative_text:
        entry.narrative_text = generate_narrative(entry.raw_text)


def ensure_title(entry) -> None:
    """
    Ensure an entry has a title, generating if needed.
    
    Modifies the entry object in place. Uses narrative_text if available,
    otherwise falls back to raw_text for title generation.
    
    Args:
        entry: Entry object to update (modified in place)
    """
    if not entry.title:
        text = entry.narrative_text or entry.raw_text
        entry.title = generate_title(text)


def process_entry(entry) -> None:
    """
    Fully process an entry: generate both narrative and title.
    
    Convenience function that ensures both narrative_text and title
    are populated. Modifies the entry object in place.
    
    Args:
        entry: Entry object to process (modified in place)
    """
    ensure_narrative(entry)
    ensure_title(entry)
