"""
Chronicle AI - LLM Client

Integration with local Ollama Llama 3.2 for narrative and title generation.
"""

import logging
from typing import Optional, List, Dict

from .models import ConflictAnalysis
from .style_guide import CinematicStyleGuide
from .llm_utils import _make_request, is_ollama_available, OLLAMA_TIMEOUT
from .conflict import ConflictDetector
from .director import director_engine

# Initialize the Cinematic Style Guide and Conflict Detector
style_guide = CinematicStyleGuide()
conflict_detector = ConflictDetector()


# Redundant functions removed as they are now in llm_utils


def detect_mood(raw_text: str) -> str:
    """Detect mood from raw diary text."""
    lower_text = raw_text.lower()
    if any(w in lower_text for w in ["productive", "finished", "accomplished", "work", "busy"]):
        return "productive"
    elif any(w in lower_text for w in ["sad", "reflective", "thought", "lonely", "missing"]):
        return "reflective"
    elif any(w in lower_text for w in ["stress", "deadline", "fast", "rushed", "panic"]):
        return "stressful"
    elif any(w in lower_text for w in ["relax", "chill", "calm", "peace", "quiet"]):
        return "relaxed"
    elif any(w in lower_text for w in ["mystery", "weird", "strange", "dark", "unknown"]):
        return "mysterious"
    else:
        return "neutral"


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
        mood = detect_mood(raw_text)
    
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

    # Check cache
    cache_key = f"narrative_{hash(prompt)}"
    cached = director_engine.cache.get(cache_key)
    if cached:
        return cached

    # 4. Request from LLM
    import time
    start = time.time()
    result = _make_request(prompt)
    duration = time.time() - start
    director_engine.perf_logger.log_event("generate_narrative", duration)
    
    if result:
        # 5. Enrich the output with sensory layers
        final_narrative = style_guide.add_sensory_layer(result)
        director_engine.cache.set(cache_key, final_narrative)
        return final_narrative
    
    # Fallback when Ollama is not available
    logger.info("Using fallback narrative (Ollama offline)")
    fallback = f"[Demo narrative] {raw_text[:200]}{'...' if len(raw_text) > 200 else ''}"
    return style_guide.add_sensory_layer(fallback)


def generate_title_options(text: str) -> List[Dict]:
    """
    Generate 5 title options using different patterns and scoring.
    """
    if not text or not text.strip():
        return [{"title": "Untitled Episode", "score": 1.0, "pattern": "Default"}]
    
    prompt = f"""You are creating episode titles for a personal life documentary series.
Analyze the following diary content and generate 5 title options using these patterns:
1. 'The One Where...' (Friends style)
2. Single evocative word ('Pilot', 'Crossroads', 'Aftermath')
3. Song, book, or movie reference relevant to content
4. Metaphorical title
5. Direct dramatic statement

For each title, provide a 'relevance_score' (0.0 to 1.0) based on how well it matches keywords and mood.
Output the result as a raw JSON list of objects with 'title', 'pattern', and 'score' keys.
Do not include any other text, only the JSON.

Example:
[
  {{"title": "The One Where Dreams Collide", "pattern": "Friends-style", "score": 0.85}},
  {{"title": "Crossroads", "pattern": "Single-word", "score": 0.92}}
]

Diary content:
{text[:800]}

JSON Output:"""

    result = _make_request(prompt, timeout=40)
    
    if result:
        try:
            # Try to find JSON in the response if it's not raw
            import json
            import re
            json_match = re.search(r'\[.*\]', result, re.DOTALL)
            if json_match:
                options = json.loads(json_match.group(0))
                # Normalize and validate
                valid_options = []
                for opt in options:
                    if isinstance(opt, dict) and "title" in opt:
                        valid_options.append({
                            "title": str(opt.get("title")).strip().strip('"\''),
                            "pattern": str(opt.get("pattern", "Unknown")),
                            "score": float(opt.get("score", 0.5))
                        })
                if valid_options:
                    return valid_options
        except Exception as e:
            logging.error(f"Failed to parse title options JSON: {e}")

    # Fallback to single generation or dummy options
    title = generate_title(text) # Use the old one as fallback
    return [{"title": title, "pattern": "Direct", "score": 0.5}]


def generate_title(text: str) -> str:
    """
    Generate a catchy episode title from diary text.
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
        title = result.strip().strip('"\'').strip()
        words = title.split()
        if len(words) > 8:
            title = ' '.join(words[:7])
        return title
    
    return "Untitled Episode"
    
    
def generate_synopsis(text: str) -> Dict[str, any]:
    """
    Generate a logline, synopsis, and keywords for an episode.
    """
    if not text or not text.strip():
        return {"logline": "", "synopsis": "", "keywords": []}
        
    prompt = f"""You are an expert TV writer and metadata specialist.
Analyze the following episode narrative and extract the following:
1. LOGLINE: Exactly one sentence hook (max 15 words) with intrigue, no spoilers. 
   Example: 'A critical deadline forces an unexpected alliance with an old rival.'
2. SYNOPSIS: A 2-3 sentence summary for an episode listing.
3. KEYWORDS: Exactly 5 searchable/filterable tags that capture themes or events.

Output the result as a raw JSON object with 'logline', 'synopsis', and 'keywords' (list) keys.
Do not include any other text, only the JSON.

Episode Narrative:
{text[:1500]}

JSON Output:"""

    result = _make_request(prompt, timeout=40)
    
    if result:
        try:
            import json
            import re
            json_match = re.search(r'{{.*}}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                return {
                    "logline": str(data.get("logline", "")).strip(),
                    "synopsis": str(data.get("synopsis", "")).strip(),
                    "keywords": [str(k).strip() for k in data.get("keywords", [])[:5]]
                }
        except Exception as e:
            logging.error(f"Failed to parse synopsis JSON: {e}")

    return {"logline": "", "synopsis": "", "keywords": []}


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
    Ensure an entry has a title and title options, generating if needed.
    """
    if not entry.title or not entry.title_options:
        text = entry.narrative_text or entry.raw_text
        options = generate_title_options(text)
        entry.title_options = options
        if options and not entry.title:
            # Pick the highest scoring one
            best_opt = max(options, key=lambda x: x.get('score', 0))
            entry.title = best_opt['title']


def ensure_synopsis(entry) -> None:
    """
    Ensure an entry has synopsis data.
    """
    if not entry.logline or not entry.synopsis or not entry.keywords:
        text = entry.narrative_text or entry.raw_text
        data = generate_synopsis(text)
        entry.logline = data.get("logline")
        entry.synopsis = data.get("synopsis")
        entry.keywords = data.get("keywords", [])


def process_entry(entry, force: bool = False) -> None:
    """
    Fully process an entry: generate narrative, title, and synopsis.
    
    This function uses an optimized single-request approach if all components are missing,
    reusing LLM context by combining instructions.
    
    Args:
        entry: Entry object to process (modified in place)
        force: If True, regenerates even if data exists
    """
    # If all or most are missing, use the optimized full generation
    # Otherwise, use sequential 'ensure' calls to fill gaps.
    is_missing_all = (force or 
                     (not entry.narrative_text and not entry.conflict_data and 
                      not entry.title and not entry.synopsis))
    
    if is_missing_all:
        try:
            _process_entry_full(entry)
            return
        except Exception as e:
            logging.warning(f"Optimized processing failed for entry {entry.id}: {e}. Falling back to sequential.")

    # Sequential fallback / Partial update
    ensure_conflict_analysis(entry)
    ensure_narrative(entry)
    ensure_title(entry)
    ensure_synopsis(entry)


def _process_entry_full(entry) -> None:
    """Internal optimized processing using a single large prompt."""
    import json
    import re
    
    mood = detect_mood(entry.raw_text)
    
    prompt = f"""You are an expert TV writer and metadata specialist.
Analyze the following diary entry and produce a complete episode package.

1. CONFLICTS: Identify internal and external conflicts, assign a tension level (1-10), and determine the primary conflict archetype (person vs self, vs environment, vs system, vs time).
2. NARRATIVES: Write a 2-4 sentence cinematic narrative in third person, present tense. Use identified conflicts to drive the structure.
3. TITLES: Generate 5 title options with these patterns: 'The One Where...', Single evocative word, Reference, Metaphorical, Direct dramatic. Include relevance scores (0.0-1.0).
4. METADATA: Provide a 1-sentence logline, a 2-3 sentence synopsis, and exactly 5 keywords.

Diary entry:
{entry.raw_text}

IMPORTANT: Output ONLY a raw JSON object with these keys: 
'conflict' (object with internal_conflicts, external_conflicts, tension_level, archetype, central_conflict),
'narrative' (string),
'titles' (list of objects with title, pattern, score),
'metadata' (object with logline, synopsis, keywords).
"""

    # Apply cinematic style guide to the prompt
    enhanced_prompt = style_guide.enhance_prompt(prompt, mood)
    
    # Check cache
    cache_key = f"full_process_{hash(enhanced_prompt)}"
    cached = director_engine.cache.get(cache_key)
    if cached:
        # Populate entry from cached data
        data = cached
        _populate_entry_from_data(entry, data)
        return

    import time
    start = time.time()
    result = _make_request(enhanced_prompt, timeout=90)
    duration = time.time() - start
    director_engine.perf_logger.log_event("full_process", duration)
    
    if result:
        try:
            # Extract and parse JSON
            json_match = re.search(r'\{.*\}', result, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
                
                # 1. Conflict
                c_data = data.get('conflict', {})
                entry.conflict_data = ConflictAnalysis(
                    internal_conflicts=c_data.get('internal_conflicts', []),
                    external_conflicts=c_data.get('external_conflicts', []),
                    tension_level=c_data.get('tension_level', 1),
                    archetype=c_data.get('archetype', 'none'),
                    central_conflict=c_data.get('central_conflict', '')
                )
                
                # 2. Narrative
                narrative = data.get('narrative', '')
                if narrative:
                    entry.narrative_text = style_guide.add_sensory_layer(narrative)
                
                # 3. Titles
                titles = data.get('titles', [])
                if titles:
                    entry.title_options = titles
                    best_opt = max(titles, key=lambda x: x.get('score', 0))
                    entry.title = best_opt.get('title')
                
                # 4. Metadata
                meta = data.get('metadata', {})
                entry.logline = meta.get('logline', '')
                entry.synopsis = meta.get('synopsis', '')
                entry.keywords = meta.get('keywords', [])
                
                # Cache the successful result
                director_engine.cache.set(cache_key, data)
                return
        except Exception as e:
            raise Exception(f"Failed to parse integrated JSON: {e}")

    raise Exception("Ollama returned empty or invalid response for integrated processing.")


def _populate_entry_from_data(entry, data: Dict) -> None:
    """Helper to populate an entry object from a parsed data dictionary."""
    from .models import ConflictAnalysis
    
    # 1. Conflict
    c_data = data.get('conflict', {})
    entry.conflict_data = ConflictAnalysis(
        internal_conflicts=c_data.get('internal_conflicts', []),
        external_conflicts=c_data.get('external_conflicts', []),
        tension_level=c_data.get('tension_level', 1),
        archetype=c_data.get('archetype', 'none'),
        central_conflict=c_data.get('central_conflict', '')
    )
    
    # 2. Narrative
    narrative = data.get('narrative', '')
    if narrative:
        entry.narrative_text = style_guide.add_sensory_layer(narrative)
    
    # 3. Titles
    titles = data.get('titles', [])
    if titles:
        entry.title_options = titles
        best_opt = max(titles, key=lambda x: x.get('score', 0))
        entry.title = best_opt.get('title')
    
    # 4. Metadata
    meta = data.get('metadata', {})
    entry.logline = meta.get('logline', '')
    entry.synopsis = meta.get('synopsis', '')
    entry.keywords = meta.get('keywords', [])
