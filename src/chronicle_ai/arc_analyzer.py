"""
Chronicle AI - Season Arc Analyzer

Analyzes complete seasons to identify storylines, character growth, climaxes, and themes.
"""

from typing import List, Optional, Dict
import json
from .models import Season, Entry, SeasonArc, ConflictAnalysis
from .llm_client import get_llm_client
from .repository import get_repository


class SeasonArcAnalyzer:
    """
    Analyzes a season's worth of episodes to extract deep narrative insights.
    """

    def __init__(self, repository=None, llm_client=None):
        self.repo = repository or get_repository()
        self.llm = llm_client or get_llm_client()

    def analyze_season(self, season_id: int) -> SeasonArc:
        """
        Performs a full narrative analysis of a season.
        
        Args:
            season_id: The ID of the season to analyze.
            
        Returns:
            A SeasonArc object containing the results of the analysis.
        """
        season = self.repo.get_season_by_id(season_id)
        if not season:
            raise ValueError(f"Season with ID {season_id} not found.")

        # Get all entries for this season
        entries = self.repo.list_entries_between_dates(season.start_date, season.end_date)
        # Reverse to get them in chronological order
        entries.sort(key=lambda x: x.date)

        if not entries:
            return SeasonArc(summary="No episodes found in this season.")

        # Prepare context for LLM
        # We need a condensed version of each episode to fit in context
        episode_summaries = []
        for i, entry in enumerate(entries):
            episode_summaries.append({
                "id": entry.id,
                "episode_number": i + 1,
                "date": entry.date,
                "title": entry.title or f"Episode {i+1}",
                "synopsis": entry.synopsis or entry.snippet(200),
                "tension_level": entry.conflict_data.tension_level if entry.conflict_data else 1,
                "central_conflict": entry.conflict_data.central_conflict if entry.conflict_data else "None"
            })

        # LLM Analysis Prompt
        prompt = self._build_analysis_prompt(season, episode_summaries)
        
        # Call LLM
        response_text = self.llm.generate(prompt, system_prompt="You are an expert TV story editor and narrative analyst.")
        
        # Parse response
        arc_data = self._parse_llm_response(response_text)
        
        # Create SeasonArc object
        arc = SeasonArc(
            storylines=arc_data.get("storylines", {}),
            character_growth=arc_data.get("character_growth", ""),
            climax_episode_id=arc_data.get("climax_episode_id"),
            motifs=arc_data.get("motifs", []),
            summary=arc_data.get("summary", ""),
            finale_worthy_episodes=arc_data.get("finale_worthy_episodes", [])
        )

        # Store the analysis
        season.arc_analysis = arc
        self.repo.update_season(season)

        return arc

    def _build_analysis_prompt(self, season: Season, episodes: List[dict]) -> str:
        episodes_json = json.dumps(episodes, indent=2)
        
        prompt = f"""
Analyze the following TV season data for a show called "Chronicle AI".
This season is titled "{season.title}" and spans from {season.start_date} to {season.end_date}.

SEASON DATA (EPISODES):
{episodes_json}

Please provide a detailed narrative analysis of this season. Your response MUST be in JSON format with the following structure:
{{
  "storylines": {{
    "career": "Description of the career/professional arc across the season",
    "health": "Description of the health/well-being arc across the season",
    "relationships": "Description of the social/relationship arcs across the season"
  }},
  "character_growth": "A detailed description of how the protagonist has changed from the premiere to the finale.",
  "climax_episode_id": 123, (The ID of the episode that represents the emotional or narrative peak of the season)
  "motifs": ["motif1", "motif2", ...], (Recurring symbols, themes, or metaphors)
  "summary": "A comprehensive 'Wikipedia plot style' narrative summary of the entire season (3-5 paragraphs).",
  "finale_worthy_episodes": [121, 125, ...] (List of episode IDs that felt like they could have served as a season finale due to stakes or resolution)
}}

Focus on identifying threads that span multiple episodes and payoffs to earlier setups. The climax should be the episode with the highest drama or most significant turning point.
"""
        return prompt

    def _parse_llm_response(self, response_text: str) -> dict:
        """Extract JSON from LLM response."""
        try:
            # Try to find JSON block
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response_text)
        except Exception:
            # Fallback if parsing fails
            return {
                "summary": "Full analysis failed to parse. Raw response: " + response_text[:500] + "...",
                "storylines": {},
                "character_growth": "Analysis parsing failed.",
                "motifs": [],
                "finale_worthy_episodes": []
            }
