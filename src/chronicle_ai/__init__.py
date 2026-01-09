"""
Chronicle AI - Turn your daily diary into episodic stories.

A diary-to-episodes application that transforms your daily entries
into cinematic narratives using AI-powered storytelling.
"""

__version__ = "0.1.0"
__author__ = "Riju Saha"
__project__ = "Chronicle AI"

# Convenient imports
from .models import Entry
from .repository import EntryRepository, get_repository
from .llm_client import generate_narrative, generate_title, process_entry
from .exports import export_entry_to_markdown, export_weekly
from .processor import segment_diary_text
from .style_guide import CinematicStyleGuide

__all__ = [
    "__version__",
    "Entry",
    "EntryRepository", 
    "get_repository",
    "generate_narrative",
    "generate_title",
    "process_entry",
    "export_entry_to_markdown",
    "export_weekly",
    "segment_diary_text",
    "CinematicStyleGuide",
]
