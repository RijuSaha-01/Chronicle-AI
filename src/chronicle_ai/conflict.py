"""
Chronicle AI - Conflict Detector Module

Identifies and analyzes conflicts within diary entries using LLM.
"""

import json
import logging
from typing import Optional
from .models import ConflictAnalysis
from .llm_utils import _make_request

logger = logging.getLogger(__name__)

class ConflictDetector:
    """
    Analyzes diary entries to detect internal and external conflicts,
    tension levels, and conflict archetypes.
    """
    
    def analyze_entry(self, raw_text: str) -> ConflictAnalysis:
        """
        Analyze a diary entry for conflicts.
        
        Args:
            raw_text: The raw diary entry text
            
        Returns:
            ConflictAnalysis object with identified conflicts and metadata
        """
        if not raw_text or not raw_text.strip():
            return ConflictAnalysis()
            
        prompt = f"""Analyze the following diary entry for narrative conflicts. 
Return your analysis in STRICT JSON format with the following keys:
- internal: list of internal conflicts (e.g., doubt, fear, anxiety, indecision)
- external: list of external conflicts (e.g., deadlines, people, physical obstacles, environmental factors)
- tension: tension level from 1 to 10
- archetype: the best fitting conflict archetype (choose one: "person vs self", "person vs person", "person vs environment", "person vs system", "person vs time", "none")
- central_conflict: a one-sentence summary of the day's main struggle

Diary Entry:
{raw_text}

JSON Response:"""

        result = _make_request(prompt)
        
        if result:
            try:
                # Find JSON block if it's wrapped in markdown
                json_str = result.strip()
                if "```json" in json_str:
                    json_str = json_str.split("```json")[1].split("```")[0].strip()
                elif "```" in json_str:
                    json_str = json_str.split("```")[1].split("```")[0].strip()
                
                data = json.loads(json_str)
                
                return ConflictAnalysis(
                    internal_conflicts=data.get("internal", []),
                    external_conflicts=data.get("external", []),
                    tension_level=int(data.get("tension", 1)),
                    archetype=data.get("archetype", "none"),
                    central_conflict=data.get("central_conflict", "")
                )
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                logger.warning(f"Failed to parse conflict analysis JSON: {e}")
                logger.debug(f"Raw result: {result}")
        
        # Fallback analysis based on simple keyword matching if LLM fails
        return self._fallback_analysis(raw_text)

    def _fallback_analysis(self, text: str) -> ConflictAnalysis:
        """Simple heuristic-based analysis used when LLM is unavailable."""
        lower_text = text.lower()
        analysis = ConflictAnalysis()
        
        # Internal hints
        if any(w in lower_text for w in ["doubt", "unsure", "scared", "fear", "worried", "think if"]):
            analysis.internal_conflicts.append("uncertainty")
        if any(w in lower_text for w in ["sad", "depressed", "lonely"]):
            analysis.internal_conflicts.append("emotional struggle")
            
        # External hints
        if any(w in lower_text for w in ["deadline", "work", "boss", "client", "finish"]):
            analysis.external_conflicts.append("pressure")
            analysis.archetype = "person vs time"
        if any(w in lower_text for w in ["traffic", "broken", "rain", "storm"]):
            analysis.external_conflicts.append("environmental hurdle")
            analysis.archetype = "person vs environment"
            
        if analysis.internal_conflicts and not analysis.external_conflicts:
            analysis.archetype = "person vs self"
            analysis.tension_level = 4
        elif analysis.external_conflicts:
            analysis.tension_level = 6
            
        analysis.central_conflict = "Navigating daily challenges."
        
        return analysis
