"""
Chronicle AI - Season Arc Analyzer

Analyzes complete seasons to identify storylines, character growth, climaxes, and themes.
"""

from typing import List, Optional, Dict, Any
import json
import logging
from .models import Season, Entry, SeasonArc, ConflictAnalysis, ArcSummary, ArcMilestone
from .llm_client import get_llm_client
from .repository import get_repository
from .semantic_search import get_semantic_search

logger = logging.getLogger(__name__)

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
                "motifs": [],
                "finale_worthy_episodes": []
            }


class StoryArcAnalyzer:
    """
    Analyzes specific topics or life arcs across time ranges.
    """

    def __init__(self, repository=None, llm_client=None, search_engine=None):
        self.repo = repository or get_repository()
        self.llm = llm_client or get_llm_client()
        self.search = search_engine or get_semantic_search()

    def get_arc(self, topic: str, time_range: str = "all time") -> ArcSummary:
        """
        Retrieves and analyzes a character arc related to a specific topic.
        
        Args:
            topic: The area of life to analyze (e.g., 'career', 'fitness').
            time_range: Optional filter for time period.
            
        Returns:
            An ArcSummary object.
        """
        # 1. Search for episodes related to the topic
        # We increase the limit to capture more context for an arc
        search_results = self.search.search(topic, limit=15)
        
        if not search_results:
            return ArcSummary(topic=topic, time_range=time_range, narrative="No related memories found.")

        # 2. Extract full entry objects (to get full context)
        entries = []
        for res in search_results:
            entry = self.repo.get_entry_by_id(res.get("episode_id"))
            if entry:
                entries.append(entry)

        # 3. Order chronologically
        entries.sort(key=lambda x: x.date)

        # 4. Filter by time_range if specified
        # (This can be more sophisticated but let's do a basic date check if we find dates)
        # Note: SemanticSearch already supports this via its filters arg.
        # But if the user passed 'time_range' as a string like 'last year', we might need to parse it.
        # For now, let's assume 'time_range' is informative or handled by search_results filter if passed.

        # 5. Prepare data for LLM
        arc_snapshots = []
        for entry in entries:
            arc_snapshots.append({
                "episode_id": entry.id,
                "date": entry.date,
                "title": entry.title or f"Entry on {entry.date}",
                "content": entry.synopsis or entry.snippet(300)
            })

        # 6. Call LLM for narrative synthesis
        prompt = self._build_arc_prompt(topic, time_range, arc_snapshots)
        response_text = self.llm.generate(prompt, system_prompt="You are an expert biographer and narrative psychologist.")
        
        # 7. Parse response and format into ArcSummary
        arc_data = self._parse_arc_response(response_text)
        
        milestones = []
        for m in arc_data.get("milestones", []):
            milestones.append(ArcMilestone(
                episode_id=m.get("episode_id"),
                date=m.get("date"),
                title=m.get("title"),
                description=m.get("description")
            ))

        return ArcSummary(
            topic=topic,
            time_range=time_range,
            narrative=arc_data.get("narrative", ""),
            milestones=milestones,
            progression_score=arc_data.get("progression_score", 0.0)
        )

    def _build_arc_prompt(self, topic: str, time_range: str, entries: List[dict]) -> str:
        entries_json = json.dumps(entries, indent=2)
        
        return f"""
Analyze the user's development regarding the topic: "{topic}" over the time range: "{time_range}".
Below are relevant memories from their life in chronological order.

MEMORIES:
{entries_json}

Please synthesize a narrative arc describing the progression, key turning points, and growth.
Focus on how their perspective or situation evolved over time.

Your response MUST be in JSON format with the following structure:
{{
  "narrative": "A high-level overview of the progression and evolution for this topic (2-3 paragraphs).",
  "progression_score": 7.5, (A score from 1-10 on how much transformation/growth happened, 1=static, 10=radical change)
  "milestones": [
    {{
      "episode_id": 123,
      "date": "YYYY-MM-DD",
      "title": "Short descriptive title for this milestone",
      "description": "How this specific episode contributed to the arc."
    }},
    ... (Identify 3-5 key milestones)
  ]
}}
"""

    def _parse_arc_response(self, response_text: str) -> dict:
        try:
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(0))
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Failed to parse arc analysis JSON: {e}")
            return {
                "narrative": f"Analysis parsing failed. Raw: {response_text[:300]}...",
                "progression_score": 0.0,
                "milestones": []
            }


def get_story_arc_analyzer():
    return StoryArcAnalyzer()
