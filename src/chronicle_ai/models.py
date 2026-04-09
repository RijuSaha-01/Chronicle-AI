"""
Chronicle AI - Data Models

Defines the Entry model and related data structures for diary entries.
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict
from datetime import date
import json


@dataclass
class VoiceProfile:
    """
    Configuration for a specific narration style.
    """
    key: str
    name: str
    voice_model: str
    speed: float = 1.0
    pitch: float = 0.0
    pause_durations: Dict[str, float] = field(default_factory=lambda: {
        "sentence": 0.5,
        "paragraph": 1.2
    })
    description: str = ""

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "name": self.name,
            "voice_model": self.voice_model,
            "speed": self.speed,
            "pitch": self.pitch,
            "pause_durations": self.pause_durations,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> "VoiceProfile":
        if not data:
            return None
        return cls(
            key=data.get("key", ""),
            name=data.get("name", ""),
            voice_model=data.get("voice_model", ""),
            speed=data.get("speed", 1.0),
            pitch=data.get("pitch", 0.0),
            pause_durations=data.get("pause_durations", {"sentence": 0.5, "paragraph": 1.2}),
            description=data.get("description", "")
        )




@dataclass
class CoverMetadata:
    """
    Metadata about a generated cover image.
    """
    path: str
    prompt: str
    style: str
    date: str
    settings: dict = field(default_factory=dict)
    variants: dict = field(default_factory=dict)
    is_placeholder: bool = False

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "prompt": self.prompt,
            "style": self.style,
            "date": self.date,
            "settings": self.settings,
            "variants": self.variants,
            "is_placeholder": self.is_placeholder
        }

    @classmethod
    def from_dict(cls, data: dict) -> "CoverMetadata":
        if not data:
            return None
        return cls(
            path=data.get("path", ""),
            prompt=data.get("prompt", ""),
            style=data.get("style", ""),
            date=data.get("date", ""),
            settings=data.get("settings", {}),
            variants=data.get("variants", {}),
            is_placeholder=data.get("is_placeholder", False)
        )


@dataclass
class ArcMilestone:
    """
    A key moment in a character's story arc.
    """
    episode_id: int
    date: str
    title: str
    description: str

    def to_dict(self) -> dict:
        return {
            "episode_id": self.episode_id,
            "date": self.date,
            "title": self.title,
            "description": self.description
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArcMilestone":
        return cls(
            episode_id=data.get("episode_id"),
            date=data.get("date"),
            title=data.get("title"),
            description=data.get("description")
        )


@dataclass
class ArcSummary:
    """
    Summary of a character's development over a specific topic and time range.
    """
    topic: str
    time_range: str
    narrative: str
    milestones: List[ArcMilestone] = field(default_factory=list)
    progression_score: float = 0.0  # 1-10 for growth/change

    def to_dict(self) -> dict:
        return {
            "topic": self.topic,
            "time_range": self.time_range,
            "narrative": self.narrative,
            "milestones": [m.to_dict() for m in self.milestones],
            "progression_score": self.progression_score
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ArcSummary":
        return cls(
            topic=data.get("topic"),
            time_range=data.get("time_range"),
            narrative=data.get("narrative"),
            milestones=[ArcMilestone.from_dict(m) for m in data.get("milestones", [])],
            progression_score=data.get("progression_score", 0.0)
        )


@dataclass
class SeasonArc:
    """
    Detailed narrative analysis of a season's arc.
    """
    storylines: dict = field(default_factory=dict)  # career, health, relationships, etc.
    character_growth: str = ""
    climax_episode_id: Optional[int] = None
    motifs: List[str] = field(default_factory=list)
    summary: str = ""
    finale_worthy_episodes: List[int] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "storylines": self.storylines,
            "character_growth": self.character_growth,
            "climax_episode_id": self.climax_episode_id,
            "motifs": self.motifs,
            "summary": self.summary,
            "finale_worthy_episodes": self.finale_worthy_episodes
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SeasonArc":
        if not data:
            return cls()
        return cls(
            storylines=data.get("storylines", {}),
            character_growth=data.get("character_growth", ""),
            climax_episode_id=data.get("climax_episode_id"),
            motifs=data.get("motifs", []),
            summary=data.get("summary", ""),
            finale_worthy_episodes=data.get("finale_worthy_episodes", [])
        )


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
    themes: List[str] = field(default_factory=list)
    description: str = ""
    mode: str = "default"  # default, smart, manual
    arc_analysis: Optional[SeasonArc] = None
    poster_path: Optional[str] = None
    poster_variants: dict = field(default_factory=dict)  # {"dramatic": "path", "minimalist": "path", "artistic": "path"}

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "episode_count": self.episode_count,
            "dominant_themes": self.dominant_themes,
            "themes": self.themes,
            "description": self.description,
            "mode": self.mode,
            "arc_analysis": self.arc_analysis.to_dict() if self.arc_analysis else None,
            "poster_path": self.poster_path,
            "poster_variants": self.poster_variants
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
            themes=data.get("themes", []),
            description=data.get("description", ""),
            mode=data.get("mode", "default"),
            arc_analysis=SeasonArc.from_dict(data.get("arc_analysis")) if data.get("arc_analysis") else None,
            poster_path=data.get("poster_path"),
            poster_variants=data.get("poster_variants", {})
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
    themes: List[str] = field(default_factory=list)
    recap_id: Optional[int] = None
    season_id: Optional[int] = None
    cover_art_path: Optional[str] = None
    image_variants: dict = field(default_factory=dict)
    cover_history: List[dict] = field(default_factory=list)
    audio_path: Optional[str] = None
    audio_duration: Optional[float] = None
    audio_file_size: Optional[int] = None
    audio_generation_date: Optional[str] = None
    playback_position: float = 0.0  # seconds
    tts_voice: Optional[str] = None
    mood: Optional[str] = None
    style: Optional[str] = None
    characters: List[str] = field(default_factory=list)
    locations: List[str] = field(default_factory=list)
    cluster_label: Optional[str] = None
    needs_image_retry: bool = False
    is_placeholder: bool = False
    

    def to_dict(self) -> dict:
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
            "themes": self.themes,
            "conflict_data": self.conflict_data.to_dict() if self.conflict_data else None,
            "recap_id": self.recap_id,
            "season_id": self.season_id,
            "cover_art_path": self.cover_art_path,
            "image_variants": self.image_variants,
            "cover_history": self.cover_history,
            "audio_path": self.audio_path,
            "audio_duration": self.audio_duration,
            "audio_file_size": self.audio_file_size,
            "audio_generation_date": self.audio_generation_date,
            "playback_position": self.playback_position,
            "tts_voice": self.tts_voice,
            "mood": self.mood,
            "style": self.style,
            "characters": self.characters,
            "locations": self.locations,
            "cluster_label": self.cluster_label,
            "needs_image_retry": self.needs_image_retry,
            "is_placeholder": self.is_placeholder
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Entry":
        if not data:
            return None
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
            themes=data.get("themes", []),
            conflict_data=ConflictAnalysis.from_dict(data.get("conflict_data")) if data.get("conflict_data") else None,
            recap_id=data.get("recap_id"),
            season_id=data.get("season_id"),
            cover_art_path=data.get("cover_art_path"),
            image_variants=data.get("image_variants") or {},
            cover_history=data.get("cover_history") or [],
            audio_path=data.get("audio_path"),
            audio_duration=data.get("audio_duration"),
            audio_file_size=data.get("audio_file_size"),
            audio_generation_date=data.get("audio_generation_date"),
            playback_position=data.get("playback_position", 0.0),
            tts_voice=data.get("tts_voice"),
            mood=data.get("mood"),
            style=data.get("style"),
            characters=data.get("characters", []),
            locations=data.get("locations", []),
            cluster_label=data.get("cluster_label"),
            needs_image_retry=data.get("needs_image_retry", False),
            is_placeholder=data.get("is_placeholder", False)
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
