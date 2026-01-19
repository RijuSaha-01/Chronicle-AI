"""
Chronicle AI - Data Models

Defines the Entry model and related data structures for diary entries.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date
import json


@dataclass
class Season:
    """
    Organizes episodes into distinct narrative arcs or time periods.
    """
    id: Optional[int] = None
    title: str = ""
    start_date: str = ""
    end_date: str = ""
    episode_count: int = 0
    dominant_themes: List[str] = field(default_factory=list)
    description: str = ""
    mode: str = "default"  # default, smart, manual

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "episode_count": self.episode_count,
            "dominant_themes": self.dominant_themes,
            "description": self.description,
            "mode": self.mode
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Season":
        if not data:
            return cls()
        return cls(
            id=data.get("id"),
            title=data.get("title", ""),
            start_date=data.get("start_date", ""),
            end_date=data.get("end_date", ""),
            episode_count=data.get("episode_count", 0),
            dominant_themes=data.get("dominant_themes", []),
            description=data.get("description", ""),
            mode=data.get("mode", "default")
        )


@dataclass
class ConflictAnalysis:
    """
    Metadata about conflicts found in a diary entry.
    """
    internal_conflicts: List[str] = field(default_factory=list)  # doubt, fear, etc.
    external_conflicts: List[str] = field(default_factory=list)  # deadlines, people, obstacles
    tension_level: int = 1  # 1-10
    archetype: str = "none"  # person vs self, vs environment, vs system, vs time
    central_conflict: str = ""

    def to_dict(self) -> dict:
        return {
            "internal_conflicts": self.internal_conflicts,
            "external_conflicts": self.external_conflicts,
            "tension_level": self.tension_level,
            "archetype": self.archetype,
            "central_conflict": self.central_conflict
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ConflictAnalysis":
        if not data:
            return cls()
        return cls(
            internal_conflicts=data.get("internal_conflicts", []),
            external_conflicts=data.get("external_conflicts", []),
            tension_level=data.get("tension_level", 1),
            archetype=data.get("archetype", "none"),
            central_conflict=data.get("central_conflict", "")
        )


@dataclass
class Recap:
    """
    Generated summary of previous episodes.
    """
    id: Optional[int] = None
    date: str = field(default_factory=lambda: date.today().isoformat())
    content: str = ""
    entry_ids: List[int] = field(default_factory=list)  # IDs of entries summarized

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "date": self.date,
            "content": self.content,
            "entry_ids": self.entry_ids
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Recap":
        if not data:
            return cls()
        return cls(
            id=data.get("id"),
            date=data.get("date", date.today().isoformat()),
            content=data.get("content", ""),
            entry_ids=data.get("entry_ids", [])
        )


@dataclass
class Entry:
    """
    Represents a single diary entry with optional AI-generated content.
    
    Attributes:
        id: Unique identifier (auto-assigned by database)
        date: ISO date string (YYYY-MM-DD)
        raw_text: Original diary text from user
        narrative_text: AI-generated narrative paragraph (optional)
        title: AI-generated episode title (optional)
    """
    id: Optional[int] = None
    date: str = field(default_factory=lambda: date.today().isoformat())
    raw_text: str = ""
    narrative_text: Optional[str] = None
    title: Optional[str] = None
    title_options: List[dict] = field(default_factory=list)  # List of {"title": str, "score": float, "pattern": str}
    conflict_data: Optional[ConflictAnalysis] = None
    logline: Optional[str] = None
    synopsis: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    recap_id: Optional[int] = None
    season_id: Optional[int] = None
    
    def to_dict(self) -> dict:
        """Convert entry to dictionary for serialization."""
        return {
            "id": self.id,
            "date": self.date,
            "raw_text": self.raw_text,
            "narrative_text": self.narrative_text,
            "title": self.title,
            "title_options": self.title_options,
            "logline": self.logline,
            "synopsis": self.synopsis,
            "keywords": self.keywords,
            "conflict_data": self.conflict_data.to_dict() if self.conflict_data else None,
            "recap_id": self.recap_id,
            "season_id": self.season_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Entry":
        """Create an Entry from a dictionary."""
        return cls(
            id=data.get("id"),
            date=data.get("date", date.today().isoformat()),
            raw_text=data.get("raw_text", ""),
            narrative_text=data.get("narrative_text"),
            title=data.get("title"),
            title_options=data.get("title_options", []),
            logline=data.get("logline"),
            synopsis=data.get("synopsis"),
            keywords=data.get("keywords", []),
            conflict_data=ConflictAnalysis.from_dict(data.get("conflict_data")) if data.get("conflict_data") else None,
            recap_id=data.get("recap_id"),
            season_id=data.get("season_id")
        )
    
    def snippet(self, max_length: int = 100) -> str:
        """Return a truncated preview of the content."""
        text = self.narrative_text or self.raw_text
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    def display_title(self) -> str:
        """Return title or a fallback display string."""
        return self.title or f"Entry from {self.date}"
