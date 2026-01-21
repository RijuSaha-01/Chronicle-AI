"""
Chronicle AI - Recap Generator

Analyzes previous episodes to create "Previously on Chronicle..." summaries.
"""

from typing import List, Optional
from datetime import date

from .models import Entry, Recap
from .repository import get_repository
from .llm_client import _make_request
from .director import director_engine


class RecapGenerator:
    """
    Generates dramatic TV-style recaps of previous diary entries.
    """
    
    def __init__(self, repository=None):
        self.repo = repository or get_repository()

    def generate_recap(self, entries: List[Entry]) -> Recap:
        """
        Generate a Recap object for the given entries.
        
        Args:
            entries: List of entries to summarize (usually last 3-7 days)
            
        Returns:
            A new Recap object with generated content.
        """
        if not entries:
            return Recap(content="No previous episodes found to recap.")
        
        # Sort entries by date (descending) but we might want them ascending for the prompt
        sorted_entries = sorted(entries, key=lambda e: e.date)
        
        # Prepare content for the prompt
        entry_summaries = []
        for entry in sorted_entries:
            summary = f"Date: {entry.date}\nTitle: {entry.display_title()}\n"
            if entry.conflict_data:
                summary += f"Conflict: {entry.conflict_data.central_conflict}\n"
            summary += f"Narrative: {entry.narrative_text or entry.raw_text[:200]}...\n"
            entry_summaries.append(summary)
        
        episodes_text = "\n---\n".join(entry_summaries)
        
        prompt = f"""You are a dramatic TV series narrator. 
Your task is to create a 'Previously on Chronicle...' summary for the upcoming episode.

Analyze the last {len(entries)} episodes for ongoing threads, unresolved conflicts, recurring themes, and character arcs. 
Then, generate a 2-3 paragraph dramatic recap in a compelling TV narrator style.
Highlight any cliffhangers or setups that feel like they might pay off in the next episode.

PREVIOUS EPISODES:
{episodes_text}

GENERATE RECAP (2-3 paragraphs, TV narrator style):
"Previously on Chronicle..."
"""

        import time
        start = time.time()
        content = _make_request(prompt)
        duration = time.time() - start
        director_engine.perf_logger.log_event("recap_generation", duration)
        
        if not content:
            content = "Previously on Chronicle... The journey continues as our protagonist navigates the complexities of daily life, facing internal struggles and external challenges in an ever-unfolding narrative."

        # Ensure it starts with the classic line if the LLM forgot
        if not content.strip().startswith("Previously on Chronicle..."):
            content = f"Previously on Chronicle...\n\n{content}"

        recap = Recap(
            date=date.today().isoformat(),
            content=content,
            entry_ids=[e.id for e in entries if e.id is not None]
        )
        
        return recap

    def get_recap_for_days(self, days: int = 7) -> Recap:
        """
        Convenience method to generate a recap for the last N days.
        """
        entries = self.repo.list_entries_last_n_days(days)
        # Exclude today's entry if it's already there? 
        # Actually, "previously on" usually excludes the current one.
        today = date.today().isoformat()
        past_entries = [e for e in entries if e.date < today]
        
        # If no past entries in last N days, just take the last N entries regardless of date
        if not past_entries:
            past_entries = self.repo.list_recent_entries(days)
            # still filter out today
            past_entries = [e for e in past_entries if e.date < today]

        return self.generate_recap(past_entries)
