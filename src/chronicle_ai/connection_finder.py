"""
Chronicle AI - Connection Finder

Identifies recurring themes, characters, locations, and "on this day" memories 
to surface connections between life episodes.
"""

from typing import List, Dict, Optional
from datetime import datetime
from .repository import get_repository
from .models import Entry

class ConnectionFinder:
    """
    Analyzes episodes to find various types of narrative connections.
    """
    
    def __init__(self, repo=None):
        self.repo = repo or get_repository()

    def find_connections(self, episode_id: int) -> List[Dict]:
        """
        Find connections for a specific episode.
        
        Returns a list of connected episodes with metadata about the connection type.
        """
        target_entry = self.repo.get_entry_by_id(episode_id)
        if not target_entry:
            return []

        all_entries = self.repo.list_entries()
        connections = []
        
        target_date = datetime.fromisoformat(target_entry.date)
        
        for entry in all_entries:
            if entry.id == target_entry.id:
                continue
            
            reasons = []
            
            # 1. On This Day (Memories from previous years)
            entry_date = datetime.fromisoformat(entry.date)
            if entry_date.month == target_date.month and entry_date.day == target_date.day and entry_date.year != target_date.year:
                reasons.append({
                    "type": "on_this_day",
                    "description": f"On this day in {entry_date.year}"
                })

            # 2. Recurring Characters
            common_characters = set(target_entry.characters) & set(entry.characters)
            if common_characters:
                reasons.append({
                    "type": "character",
                    "description": f"Features {', '.join(list(common_characters))}",
                    "shared": list(common_characters)
                })

            # 3. Recurring Locations
            common_locations = set(target_entry.locations) & set(entry.locations)
            if common_locations:
                reasons.append({
                    "type": "location",
                    "description": f"Took place at {', '.join(list(common_locations))}",
                    "shared": list(common_locations)
                })

            # 4. Similar Mood
            if target_entry.mood and entry.mood and target_entry.mood == entry.mood:
                reasons.append({
                    "type": "mood",
                    "description": f"Shared {target_entry.mood} mood"
                })

            # 5. Similar Conflict
            if (target_entry.conflict_data and entry.conflict_data and 
                target_entry.conflict_data.archetype != "none" and
                target_entry.conflict_data.archetype == entry.conflict_data.archetype):
                reasons.append({
                    "type": "conflict",
                    "description": f"Both explore '{target_entry.conflict_data.archetype}'"
                })

            # 6. Callback Moments (Echoes) - Based on keyword/theme overlap
            common_keywords = set(target_entry.keywords) & set(entry.keywords)
            if len(common_keywords) >= 2:
                reasons.append({
                    "type": "callback",
                    "description": f"Thematic echo: {', '.join(list(common_keywords)[:2])}",
                    "shared": list(common_keywords)
                })

            if reasons:
                connections.append({
                    "episode_id": entry.id,
                    "title": entry.display_title(),
                    "date": entry.date,
                    "reasons": reasons,
                    "relevance_score": len(reasons) # Simple scoring
                })

        # Sort by relevance and then by date (most recent first)
        connections.sort(key=lambda x: (x['relevance_score'], x['date']), reverse=True)
        
        return connections[:10] # Limit to top 10 connections

# Global instance
connection_finder = ConnectionFinder()
