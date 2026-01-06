"""
Chronicle AI - Data Models

Defines the Entry model and related data structures for diary entries.
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import date


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
    
    def to_dict(self) -> dict:
        """Convert entry to dictionary for serialization."""
        return {
            "id": self.id,
            "date": self.date,
            "raw_text": self.raw_text,
            "narrative_text": self.narrative_text,
            "title": self.title
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Entry":
        """Create an Entry from a dictionary."""
        return cls(
            id=data.get("id"),
            date=data.get("date", date.today().isoformat()),
            raw_text=data.get("raw_text", ""),
            narrative_text=data.get("narrative_text"),
            title=data.get("title")
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
