"""
Chronicle AI - Audio Episode Generator
Generates full audio narration for episodes with appropriate pauses and metadata.
"""

import os
import re
import time
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple

# Try to import pydub for audio manipulation
try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False

# Try to import mutagen for ID3 tags
try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from .models import Entry
from .tts_engine import tts_engine
from .repository import get_repository

logger = logging.getLogger(__name__)

class AudioEpisodeGenerator:
    """
    Generates full audio narration for episodes with appropriate pauses and metadata.
    """
    
    PAUSES = {
        "paragraph": 0.5,  # seconds
        "scene": 1.5,
        "act": 2.0
    }

    def __init__(self, output_dir: str = "exports/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.repo = get_repository()

    def generate_audio(self, episode_id: int) -> Optional[str]:
        """
        Main method: generate_audio(episode_id) -> audio_path
        
        Args:
            episode_id: The ID of the episode to narrate.
            
        Returns:
            Path to the generated MP3 file or None if failed.
        """
        entry = self.repo.get_entry_by_id(episode_id)
        if not entry:
            logger.error(f"Episode {episode_id} not found.")
            return None

        # Prefer narrative text, fallback to raw text
        text = entry.narrative_text or entry.raw_text
        if not text:
            logger.error(f"No text to narrate for episode {episode_id}")
            return None

        logger.info(f"🎧 Generating full audio for Episode {episode_id}: {entry.title or 'Untitled'}")

        # 1. Parse text into sections (Acts, Scenes, Paragraphs)
        sequence = self._parse_sections(text)
        
        # 2. Generate and combine audio chunks
        combined_audio, total_duration = self._synthesize_and_combine(sequence, entry)
        
        if not combined_audio:
            logger.error("Failed to generate combined audio.")
            return None

        # 3. Save as MP3 to temporary location first
        temp_dir = Path("tmp/audio")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_audio_path = temp_dir / f"episode_{episode_id}_{int(time.time())}.mp3"
        
        try:
            if PYDUB_AVAILABLE:
                logger.info(f"💾 Exporting combined audio to temp: {temp_audio_path}...")
                combined_audio.export(str(temp_audio_path), format="mp3", bitrate="192k")
            else:
                logger.error("pydub is required to export MP3 with pauses.")
                return None
        except Exception as e:
            logger.error(f"Failed to export MP3: {e}")
            return None

        # 4. Hand over to AudioStorageManager for organized storage, metadata embedding, and linking
        from .audio_storage import audio_storage_manager
        final_path = audio_storage_manager.move_to_storage(
            episode_id=episode_id,
            temp_audio_path=str(temp_audio_path),
            duration=total_duration
        )

        return final_path

    def _parse_sections(self, text: str) -> List[Dict]:
        """
        Parses text into a sequence of text blocks and pauses.
        
        Markers:
        - Acts: '### Cold Open', '### Act 1', etc.
        - Scenes: '---'
        - Paragraphs: '\n\n'
        """
        # First, split by likely Act markers
        act_pattern = r'(### (?:Cold Open|Act \d+|Tag|Introduction|Conclusion|Opening|Closing))'
        parts = re.split(act_pattern, text, flags=re.IGNORECASE)
        
        # Initial flattening
        raw_parts = []
        if len(parts) == 1:
            raw_parts.append({"type": "content", "text": text})
        else:
            for i in range(0, len(parts)):
                if not parts[i].strip():
                    continue
                if re.match(act_pattern, parts[i], re.IGNORECASE):
                    raw_parts.append({"type": "act_header", "text": parts[i]})
                else:
                    raw_parts.append({"type": "content", "text": parts[i]})

        # Sequence of (type, value) where type is 'text' or 'pause'
        sequence = []
        
        for i, part in enumerate(raw_parts):
            if part["type"] == "act_header":
                # Add a longer pause before a new act (except the very first item)
                if i > 0:
                    sequence.append({"type": "pause", "duration": self.PAUSES["act"]})
                # We usually don't narrate the header itself unless requested, 
                # but let's keep it as text for now if the user wants it heard.
                # Common practice: silence or a jingle. Here we just use silence.
                continue
                
            content = part["text"]
            # Split by scene markers
            scenes = content.split("---")
            for j, scene in enumerate(scenes):
                if not scene.strip():
                    continue
                
                if j > 0:
                    sequence.append({"type": "pause", "duration": self.PAUSES["scene"]})
                
                # Split by paragraphs
                paragraphs = [p.strip() for p in scene.split("\n\n") if p.strip()]
                for k, para in enumerate(paragraphs):
                    if k > 0:
                        sequence.append({"type": "pause", "duration": self.PAUSES["paragraph"]})
                    sequence.append({"type": "text", "text": para})

        return sequence

    def _synthesize_and_combine(self, sequence: List[Dict], entry: Entry) -> Tuple[Optional['AudioSegment'], float]:
        """
        Synthesizes text items and interleaves pauses.
        """
        if not PYDUB_AVAILABLE:
            return None, 0.0

        combined = AudioSegment.empty()
        total_duration = 0.0
        
        # Temporary directory for chunks
        temp_dir = Path("tmp/audio_chunks")
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            for i, item in enumerate(sequence):
                if item["type"] == "pause":
                    duration_ms = int(item["duration"] * 1000)
                    combined += AudioSegment.silent(duration=duration_ms)
                    total_duration += item["duration"]
                
                elif item["type"] == "text":
                    chunk_filename = f"chunk_{entry.id}_{i}.wav"
                    # Generate wav via tts_engine
                    wav_path = tts_engine.generate(
                        item["text"], 
                        chunk_filename, 
                        voice_key=entry.tts_voice, 
                        mood=entry.mood
                    )
                    
                    if wav_path and os.path.exists(wav_path):
                        segment = AudioSegment.from_wav(wav_path)
                        combined += segment
                        total_duration += len(segment) / 1000.0
                        # Clean up temp chunk
                        try:
                            os.remove(wav_path)
                        except:
                            pass
                    else:
                        logger.warning(f"Failed to generate audio for text: {item['text'][:30]}...")
            
            return combined, total_duration
        except Exception as e:
            logger.error(f"Error during audio assembly: {e}")
            return None, 0.0


# Singleton instance
audio_generator = AudioEpisodeGenerator()
