"""
Chronicle AI - Season Manager

Logic for organizing episodes into Seasons based on time or narrative chapters.
"""

import logging
from typing import List, Optional, Dict
from datetime import datetime
import json

from .models import Entry, Season
from .repository import EntryRepository, get_repository
from .llm_client import _make_request
from .director import director_engine

logger = logging.getLogger(__name__)

class SeasonManager:
    """
    Manages the lifecycle of Seasons: creation, organization, and metadata generation.
    """

    def __init__(self, repo: Optional[EntryRepository] = None):
        self.repo = repo or get_repository()

    def organize_seasons(self, mode: str = "default", clear_existing: bool = True):
        """
        Retroactively organize all existing episodes into seasons.
        
        Args:
            mode: "default" (monthly), "smart" (chapter detection), or "manual"
            clear_existing: Whether to wipe current seasons before re-organizing
        """
        if clear_existing:
            self.repo.clear_seasons()

        entries = self.repo.list_entries()
        if not entries:
            logger.info("No episodes found to organize.")
            return

        # Sort entries by date ascending for processing
        entries.sort(key=lambda x: x.date)

        if mode == "default":
            self._organize_by_month(entries)
        elif mode == "smart":
            self._organize_smartly(entries)
        else:
            logger.warning(f"Unsupported organization mode: {mode}")

    def _organize_by_month(self, entries: List[Entry]):
        """Default mode: Group by calendar month."""
        seasons_data = {}
        
        for entry in entries:
            # YYYY-MM
            month_key = entry.date[:7]
            if month_key not in seasons_data:
                seasons_data[month_key] = []
            seasons_data[month_key].append(entry)

        season_count = 1
        sorted_months = sorted(seasons_data.keys())
        
        for month in sorted_months:
            month_entries = seasons_data[month]
            start_date = month_entries[0].date
            end_date = month_entries[-1].date
            
            # Create season
            season = Season(
                start_date=start_date,
                end_date=end_date,
                episode_count=len(month_entries),
                mode="default"
            )
            
            # Generate metadata
            self._enhance_season_metadata(season, month_entries, season_count)
            saved_season = self.repo.create_season(season)
            
            # Link entries
            for entry in month_entries:
                entry.season_id = saved_season.id
                self.repo.update_entry(entry)
            
            season_count += 1

    def _organize_smartly(self, entries: List[Entry]):
        """Smart mode: Use LLM to detect life chapters via major events."""
        if len(entries) < 3:
            # Not enough data for smart mode, fallback to month
            logger.info("Not enough entries for smart mode, using default monthly organization.")
            return self._organize_by_month(entries)

        # Prepare a summary of episodes for the LLM
        summary_lines = []
        for i, entry in enumerate(entries):
            title = entry.title or entry.snippet(50)
            summary_lines.append(f"{i}: {entry.date} - {title}")
        
        episodes_context = "\n".join(summary_lines)
        
        prompt = f"""You are a master story editor for a long-running documentary series.
Below is a list of episodes (daily diary entries) from a person's life.
Your task is to identify 'Life Chapters' or 'Seasons' based on shifts in tone, major events, or recurring themes.

Look for boundaries where something significant changed: a project started/ended, a move, a shift in focus, or an emotional transition.

Episodes:
{episodes_context}

Output a JSON list of season boundaries. Each object should have:
- 'start_index': The index of the first episode in the season.
- 'end_index': The index of the last episode in the season.
- 'reason': A brief explanation of why this is a distinct chapter.

Ensure every episode is included in exactly one season, and seasons are chronological.

JSON Output:"""

        import time
        start = time.time()
        result = _make_request(prompt, timeout=60)
        duration = time.time() - start
        director_engine.perf_logger.log_event("season_smart_organization", duration)
        
        boundaries = []
        if result:
            try:
                import re
                json_match = re.search(r'\[.*\]', result, re.DOTALL)
                if json_match:
                    boundaries = json.loads(json_match.group(0))
            except Exception as e:
                logger.error(f"Failed to parse smart season boundaries: {e}")

        if not boundaries:
            logger.warning("Smart detection failed, falling back to monthly.")
            return self._organize_by_month(entries)

        season_count = 1
        for b in boundaries:
            try:
                start_idx = b.get('start_index', 0)
                end_idx = b.get('end_index', len(entries)-1)
                
                # Safety check
                start_idx = max(0, min(start_idx, len(entries)-1))
                end_idx = max(start_idx, min(end_idx, len(entries)-1))
                
                season_entries = entries[start_idx:end_idx+1]
                if not season_entries: continue
                
                season = Season(
                    start_date=season_entries[0].date,
                    end_date=season_entries[-1].date,
                    episode_count=len(season_entries),
                    description=b.get('reason', ''),
                    mode="smart"
                )
                
                self._enhance_season_metadata(season, season_entries, season_count)
                saved_season = self.repo.create_season(season)
                
                for entry in season_entries:
                    entry.season_id = saved_season.id
                    self.repo.update_entry(entry)
                
                season_count += 1
            except Exception as e:
                logger.error(f"Error processing smart season: {e}")

    def _enhance_season_metadata(self, season: Season, episodes: List[Entry], season_number: int):
        """Use LLM to generate title and dominant themes for a season."""
        # Collate themes from episodes
        all_keywords = []
        for e in episodes:
            if e.keywords:
                all_keywords.extend(e.keywords)
        
        # Take the most frequent keywords as dominant themes if LLM fails
        from collections import Counter
        top_themes = [t for t, count in Counter(all_keywords).most_common(5)]
        season.dominant_themes = top_themes

        # Prepare context for metadata generation
        episode_summaries = "\n".join([f"- {e.title or e.snippet(50)}" for e in episodes[:10]])
        if len(episodes) > 10:
            episode_summaries += f"\n...and {len(episodes)-10} more episodes."

        prompt = f"""You are a creative producer for a cinematic life documentary.
Generate metadata for 'Season {season_number}' based on these episodes:
{episode_summaries}

Output a JSON object with:
- 'title': A dramatic season title (e.g., 'Season {season_number}: The Foundation', 'The Rising Tide', 'Shadows of Doubt').
- 'themes': List of 3-5 dominant themes.
- 'description': A 1-2 sentence high-level summary of this arc.

JSON Output:"""

        result = _make_request(prompt, timeout=40)
        if result:
            try:
                import re
                json_match = re.search(r'{{.*}}', result, re.DOTALL)
                if json_match:
                    meta = json.loads(json_match.group(0))
                    season.title = meta.get('title', f"Season {season_number}")
                    season.dominant_themes = meta.get('themes', top_themes)
                    if not season.description:
                        season.description = meta.get('description', "")
                    return
            except Exception as e:
                logger.error(f"Failed to parse season metadata: {e}")
        
        # Fallback
        if not season.title:
            season.title = f"Season {season_number}: The Journey Continues"

    def create_manual_season(self, title: str, start_date: str, end_date: str):
        """Manually define a season boundary."""
        entries = self.repo.list_entries_between_dates(start_date, end_date)
        season = Season(
            title=title,
            start_date=start_date,
            end_date=end_date,
            episode_count=len(entries),
            mode="manual"
        )
        
        self._enhance_season_metadata(season, entries, len(self.repo.list_seasons()) + 1)
        saved_season = self.repo.create_season(season)
        
        for entry in entries:
            entry.season_id = saved_season.id
            self.repo.update_entry(entry)
            
        return saved_season

    def suggest_seasons(self) -> Dict:
        """
        Suggest season boundaries based on semantic analysis of embeddings.
        
        Method:
        1. Calculate embedding distances between consecutive episodes.
        2. Detect major life chapter shifts (large embedding jumps).
        3. Suggest season breaks at significant transitions.
        4. Name seasons based on dominant themes in that period.
        5. Compare semantic seasons vs calendar-based seasons.
        """
        import numpy as np
        from .embedding_engine import get_embedding_engine
        
        engine = get_embedding_engine()
        entries = self.repo.list_entries()
        if len(entries) < 3:
            return {"suggestions": [], "message": "Not enough episodes for semantic analysis (minimum 3 required)."}
            
        # 1. Sort chronologically
        entries.sort(key=lambda x: x.date)
        
        # 2. Get embeddings (average of narrative chunks)
        embs = []
        valid_entries = []
        
        logger.info("Fetching embeddings for semantic analysis...")
        for e in entries:
            # We use narrative section as the primary signal for thematic shifts
            res = engine.collection.get(
                where={"episode_id": str(e.id), "section": "narrative"},
                include=["embeddings"]
            )
            
            if res["embeddings"]:
                # Compute average embedding if multi-chunk, else use first
                avg_emb = np.mean(res["embeddings"], axis=0)
                embs.append(avg_emb)
                valid_entries.append(e)
                
        if len(embs) < 3:
            return {
                "suggestions": [], 
                "message": "Missing embeddings for many episodes. Please run 'chronicle embed --batch' first."
            }
            
        # 3. Calculate distances between consecutive episodes
        distances = []
        for i in range(len(embs) - 1):
            v1 = embs[i]
            v2 = embs[i+1]
            # Cosine distance: 1 - cosine similarity
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            if norm1 == 0 or norm2 == 0:
                distances.append(0.0)
            else:
                dist = 1 - (np.dot(v1, v2) / (norm1 * norm2))
                distances.append(float(dist))
            
        # 4. Detect significant jumps (Threshold: Mean + 1.3 * StdDev)
        mean_dist = np.mean(distances)
        std_dist = np.std(distances)
        threshold = mean_dist + 1.3 * std_dist
        
        jump_indices = [i for i, d in enumerate(distances) if d > threshold]
        
        # 5. Group into potential boundaries (marks the START of a new season)
        # Season 1 always starts at index 0
        potential_starts = {0}
        for idx in jump_indices:
            # A jump after episode i means season i ends, and i+1 is a potential new start
            potential_starts.add(idx + 1)
        
        potential_starts = sorted(list(potential_starts))
        
        # 6. Prepare summary for LLM to validate and name
        summary_lines = []
        for i, entry in enumerate(valid_entries):
            marker = " [CHAPTER TRANSITION DETECTED]" if i in potential_starts and i != 0 else ""
            summary_lines.append(f"{i}: {entry.date} - {entry.title or entry.snippet(50)}{marker}")
            
        episodes_context = "\n".join(summary_lines)
        
        prompt = f"""You are a master story editor for a cinematic life documentary. 
I have analyzed the semantic distance between consecutive episodes in a person's life and detected major jumps in the underlying themes/emotions (marked with [CHAPTER TRANSITION DETECTED]).

Episodes:
{episodes_context}

Your Task:
1. Review the suggested transitions. If they make thematic sense based on titles/dates, keep them. If a transition seems weak, ignore it. If there's a clear gap elsewhere that I missed, add it.
2. Group the episodes into a final list of 'Seasons'.
3. For each season, provide:
   - 'start_index': Index of the first episode.
   - 'end_index': Index of the last episode.
   - 'title': A dramatic, cinematic season title (e.g., 'Winter of Discontent', 'The Rising Phoenix').
   - 'themes': 3-5 dominant keywords.
   - 'description': A one-sentence summary of the chapter's arc.

Also, provide a 'Comparison' explaining why these Semantic Seasons are more meaningful than Calendar Seasons (which just break every 30 days regardless of what happened).

Output JSON only:
{{
  "seasons": [
    {{ "start_index": 0, "end_index": 5, "title": "...", "themes": [...], "description": "..." }},
    ...
  ],
  "comparison": "Your analysis of semantic vs calendar breaks."
}}"""

        logger.info("Sending semantic transitions to LLM for validation...")
        result = _make_request(prompt, timeout=90)
        
        data = {"seasons": [], "comparison": ""}
        if result:
            try:
                import re
                json_match = re.search(r'\{.*\}', result, re.DOTALL)
                if json_match:
                    data = json.loads(json_match.group(0))
            except Exception as e:
                logger.error(f"Failed to parse suggested seasons JSON: {e}")

        return {
            "suggestions": data.get("seasons", []),
            "comparison": data.get("comparison", ""),
            "episodes": valid_entries,
            "metrics": {
                "mean_distance": float(mean_dist),
                "threshold": float(threshold),
                "jumps_found": len(jump_indices)
            }
        }
