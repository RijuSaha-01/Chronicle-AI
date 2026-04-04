"""
Chronicle AI - Theme Management
Handles episode auto-tagging, grouping, and statistics.
"""

from typing import List, Dict, Optional
from .models import Entry, Season
from .repository import get_repository

class ThemeManager:
    """Manages thematic analysis of episodes and seasons."""
    
    ALLOWED_THEMES = ["work", "health", "relationships", "growth", "conflict", "creativity"]
    
    def __init__(self, repo=None):
        self.repo = repo or get_repository()

    def get_episodes_by_theme(self, theme: str, season_id: Optional[int] = None) -> List[Entry]:
        """Retrieve episodes tagged with a specific theme."""
        all_entries = self.repo.list_entries()
        
        filtered = []
        for entry in all_entries:
            # Check if theme is in themes list
            if theme.lower() in [t.lower() for t in (entry.themes or [])]:
                if season_id is None or entry.season_id == season_id:
                    filtered.append(entry)
        
        return filtered

    def get_theme_stats(self) -> Dict[str, Dict[str, int]]:
        """
        Get statistics about theme distribution.
        Returns: { 'theme_name': { 'Season 1': 5, 'Season 2': 3, 'Total': 8 } }
        """
        all_entries = self.repo.list_entries()
        seasons = {s.id: s.title for s in self.repo.list_seasons()}
        
        stats = {}
        for theme in self.ALLOWED_THEMES:
            stats[theme] = {"Total": 0}
            for s_id, s_title in seasons.items():
                stats[theme][s_title] = 0

        for entry in all_entries:
            for theme in (entry.themes or []):
                theme_lower = theme.lower()
                if theme_lower in stats:
                    stats[theme_lower]["Total"] += 1
                    if entry.season_id in seasons:
                        s_title = seasons[entry.season_id]
                        stats[theme_lower][s_title] = stats[theme_lower].get(s_title, 0) + 1
                else:
                    # External themes (if any)
                    pass
        
        return stats

    def suggest_related_themes(self, theme: str) -> List[str]:
        """Suggest related themes based on co-occurrence in episodes."""
        all_entries = self.repo.list_entries()
        co_occurrences = {}
        
        for entry in all_entries:
            themes = [t.lower() for t in (entry.themes or [])]
            if theme.lower() in themes:
                for other in themes:
                    if other != theme.lower():
                        co_occurrences[other] = co_occurrences.get(other, 0) + 1
        
        # Sort by frequency
        sorted_others = sorted(co_occurrences.items(), key=lambda x: x[1], reverse=True)
        return [item[0] for item in sorted_others[:3]]

theme_manager = ThemeManager()
