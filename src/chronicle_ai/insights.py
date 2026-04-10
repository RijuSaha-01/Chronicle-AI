"""
Chronicle AI - Memory Insights

Generates periodic insights from memory analysis including patterns, 
mood trends, and growth areas.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict

from .models import InsightsReport, Entry
from .llm_client import get_llm_client
from .repository import get_repository

logger = logging.getLogger(__name__)

class MemoryInsights:
    """
    Generator for periodic life insights based on diary history.
    """
    
    def __init__(self, repository=None, llm_client=None):
        """
        Initialize with optional repository and LLM client.
        """
        self.repo = repository or get_repository()
        self.llm = llm_client or get_llm_client()

    def generate_insights(self, period: str = 'week') -> InsightsReport:
        """
        Generate insights for a specific period (week or month).
        
        Args:
            period: The time frame to analyze ('week' or 'month').
            
        Returns:
            An InsightsReport object containing synthesized analysis.
        """
        end_date = datetime.now()
        
        if period == 'week':
            start_date = end_date - timedelta(days=7)
        elif period == 'month':
            start_date = end_date - timedelta(days=30)
        else:
            raise ValueError("Unsupported period. Use 'week' or 'month'.")

        # 1. Fetch entries for current period
        current_entries = self.repo.list_entries_between_dates(
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d")
        )
        
        if not current_entries:
            return InsightsReport(
                period=period, 
                date_range=f"{start_date.date()} to {end_date.date()}", 
                patterns=["No memories found for this period to analyze."]
            )

        # 2. Fetch entries for "This time last year" (Comparison)
        year_ago_start = start_date - timedelta(days=365)
        year_ago_end = end_date - timedelta(days=365)
        last_year_entries = self.repo.list_entries_between_dates(
            year_ago_start.strftime("%Y-%m-%d"),
            year_ago_end.strftime("%Y-%m-%d")
        )

        # 3. Prepare data for LLM
        episodes_context = self._prepare_context(current_entries)
        last_year_context = self._prepare_context(last_year_entries) if last_year_entries else "No memories found for this time last year."

        # 4. Build Prompt
        prompt = self._build_prompt(period, episodes_context, last_year_context)

        # 5. Get LLM Response
        logger.info(f"Generating {period} insights for range {start_date.date()} to {end_date.date()}...")
        response_text = self.llm.generate(
            prompt, 
            system_prompt="You are an insightful personal historian and pattern analyst specializing in narrative therapy and life coaching."
        )

        # 6. Parse and Return
        return self._parse_response(period, f"{start_date.date()} to {end_date.date()}", response_text)

    def _prepare_context(self, entries: List[Entry]) -> str:
        """Convert entries into a condensed JSON format for LLM context."""
        context_items = []
        for entry in sorted(entries, key=lambda x: x.date):
            context_items.append({
                "date": entry.date,
                "title": entry.title or f"Entry on {entry.date}",
                "mood": entry.mood or "unknown",
                "themes": entry.themes,
                "synopsis": entry.synopsis or entry.snippet(200),
                "tension": entry.conflict_data.tension_level if entry.conflict_data else 1,
                "conflicts": entry.conflict_data.central_conflict if entry.conflict_data else "None"
            })
        return json.dumps(context_items, indent=2)

    def _build_prompt(self, period: str, episodes_context: str, last_year_context: str) -> str:
        """Construct the analysis prompt for the LLM."""
        return f"""
Generate a comprehensive 'Memory Insights' report for the user's last {period} of life.

CURRENT PERIOD DATA:
{episodes_context}

THIS TIME LAST YEAR DATA (For Comparison):
{last_year_context}

Please analyze the current period data deeply to identify trends and patterns. Use the last year data to provide perspective on growth or recurring life cycles.

REQUIRED SECTIONS:
1. Weekly/Monthly Insights: Patterns noticed (behavioral habits), mood trends (emotional landscape), and recurring themes (topics of focus).
2. Growth & Challenges: Areas where the user showed development, obstacles they overcame, and positive highlights of the period.
3. Historical Comparison: A reflection on how this time compares to last year.
4. Anomalies: Identify any unusual patterns or rare breaks in the user's typical routine or sentiment.
5. Reflections: 3 personalized, deep reflection questions based on the data provided.

Your response MUST be in RAW JSON format with the following structure:
{{
  "patterns": ["pattern1", "pattern2", ...],
  "mood_trends": "Detailed description of emotional landscape strings",
  "recurring_themes": ["theme1", "theme2", ...],
  "growth_areas": ["area1", "area2", ...],
  "challenges_overcome": ["challenge1", "challenge2", ...],
  "highlights": ["highlight1", "highlight2", ...],
  "year_ago_comparison": "Comparison narrative highlighting change or stability",
  "anomalies": ["anomaly1", "anomaly2", ...],
  "reflection_questions": ["question1", "question2", "question3"]
}}

Only output the JSON. Do not include conversational filler.
"""

    def _parse_response(self, period: str, date_range: str, text: str) -> InsightsReport:
        """Extract and validate the JSON response into an InsightsReport."""
        try:
            import re
            # Extract JSON block
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group(0))
            else:
                data = json.loads(text)
            
            return InsightsReport(
                period=period,
                date_range=date_range,
                patterns=data.get("patterns", []),
                mood_trends=data.get("mood_trends", ""),
                recurring_themes=data.get("recurring_themes", []),
                growth_areas=data.get("growth_areas", []),
                challenges_overcome=data.get("challenges_overcome", []),
                highlights=data.get("highlights", []),
                year_ago_comparison=data.get("year_ago_comparison"),
                anomalies=data.get("anomalies", []),
                reflection_questions=data.get("reflection_questions", [])
            )
        except Exception as e:
            logger.error(f"Failed to parse insights JSON: {e}")
            return InsightsReport(
                period=period,
                date_range=date_range,
                patterns=[f"Analysis parsing error. Raw response summary: {text[:100]}..."],
                mood_trends=f"Failed to generate detailed trends due to parsing error: {str(e)}"
            )

def get_memory_insights():
    return MemoryInsights()
