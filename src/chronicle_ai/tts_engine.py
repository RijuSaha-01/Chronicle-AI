"""
Chronicle AI - TTS Engine
Handles local text-to-speech generation for audiobook narration.
Supports Coqui XTTS v2 and Piper.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TTSEngine")

from .tts_client import NarratorTTS, get_tts_client

class TTSEngine:
    """
    Local TTS Engine supporting high-quality (XTTS v2) and high-speed (Piper) backends.
    Now optimized with VoiceProfiles and mood-based selection.
    """
    
    def __init__(self, output_dir: str = "exports/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._client_cache = {}

    def _get_client(self, voice_key: str) -> NarratorTTS:
        if voice_key not in self._client_cache:
            self._client_cache[voice_key] = get_tts_client(voice_profile=voice_key)
        return self._client_cache[voice_key]

    def generate(self, text: str, output_filename: str, voice_key: Optional[str] = None, mood: Optional[str] = None) -> Optional[str]:
        """
        Generate audio from text, with optional mood-based auto-selection.
        
        Args:
            text: The narrative text to convert.
            output_filename: Name of the output file.
            voice_key: Specific profile key (STORYTELLER, DRAMATIC, etc.).
            mood: Episode mood for auto-selection if voice_key is None.
            
        Returns:
            Absolute path to the generated audio file, or None if failed.
        """
        if not voice_key:
            voice_key = NarratorTTS.get_profile_for_mood(mood)
            logger.info(f"🎭 Auto-selected voice profile '{voice_key}' for mood '{mood}'")
        
        # Normalize key for lookup
        voice_key = voice_key.upper()
        if voice_key not in NarratorTTS.DEFAULT_PROFILES:
            logger.warning(f"Voice '{voice_key}' not found. Falling back to STORYTELLER.")
            voice_key = "STORYTELLER"

        output_path = self.output_dir / output_filename
        client = self._get_client(voice_key)
        
        return client.synthesize(text, str(output_path))

    def preview(self, voice_key: str) -> Optional[str]:
        """Generate a preview sample for a specific voice."""
        client = self._get_client(voice_key.upper())
        return client.preview_voice(voice_key.upper())

    def list_voices(self) -> List[Dict]:
        """Return available voice profiles."""
        return [p.to_dict() for p in NarratorTTS.DEFAULT_PROFILES.values()]

# Singleton instance
tts_engine = TTSEngine()
