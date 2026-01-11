"""
Chronicle AI - LLM Client

Integration with local Ollama Llama 3.2 for narrative and title generation.
"""

import logging
from typing import Optional

from .models import ConflictAnalysis
from .style_guide import CinematicStyleGuide
from .llm_utils import _make_request, is_ollama_available, OLLAMA_TIMEOUT
from .conflict import ConflictDetector

# Initialize the Cinematic Style Guide and Conflict Detector
style_guide = CinematicStyleGuide()
conflict_detector = ConflictDetector()


# Redundant functions removed as they are now in llm_utils


def generate_narrative(raw_text: str, mood: Optional[str] = None, conflict_data: Optional[ConflictAnalysis] = None) -> str:
    """
    Generate a narrative paragraph from raw diary text with cinematic enhancement.
    
    Uses Ollama Llama 3.2 to transform diary entries into engaging
    narrative prose, enriched with cinematic visual direction and sensory layers.
    
    Args:
        raw_text: The user's raw diary entry text
        mood: Optional mood to guide the cinematic style
        conflict_data: Optional ConflictAnalysis to drive the narrative structure
        
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
    
    # 1.5 Incorporate conflict data into the prompt
    conflict_context = ""
    if conflict_data:
        conflict_context = f"\nCentral Conflict: {conflict_data.central_conflict}"
        if conflict_data.internal_conflicts:
            conflict_context += f"\nInternal Struggles: {', '.join(conflict_data.internal_conflicts)}"
        if conflict_data.external_conflicts:
            conflict_context += f"\nExternal Obstacles: {', '.join(conflict_data.external_conflicts)}"
        conflict_context += f"\nTension Level: {conflict_data.tension_level}/10"
    
    # 2. Prepare the base prompt
    base_prompt = f"""You are a creative writer helping to transform personal diary entries into engaging narrative prose.

Transform the following diary entry into a short, cinematic narrative paragraph (2-4 sentences). 
Write in third person, present tense, as if describing scenes from a movie about the protagonist's life.
Keep it personal and emotionally resonant while maintaining the key events and feelings.
Use the identified conflicts to drive the narrative, treating them as the 'inciting incidents' or 'climax' of the story acts.
{conflict_context}

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
        entry.narrative_text = generate_narrative(entry.raw_text, conflict_data=entry.conflict_data)


def ensure_conflict_analysis(entry) -> None:
    """
    Ensure an entry has conflict analysis data.
    
    Args:
        entry: Entry object to update (modified in place)
    """
    if not entry.conflict_data:
        entry.conflict_data = conflict_detector.analyze_entry(entry.raw_text)


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
    ensure_conflict_analysis(entry)
    ensure_narrative(entry)
    ensure_title(entry)
