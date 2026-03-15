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
    from pydub.effects import normalize, compress_dynamic_range
    from pydub.silence import detect_silence
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
from .style_guide import CinematicStyleGuide

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
        self.style_guide = CinematicStyleGuide()

    def generate_audio(self, episode_id: int, quality_preset: str = "standard") -> Optional[str]:
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
        combined_audio, total_duration, chapters = self._synthesize_and_combine(sequence, entry)
        
        if not combined_audio:
            logger.error("Failed to generate combined audio.")
            return None

        # 2b. Apply audio optimizations
        combined_audio = self._post_process(combined_audio, quality_preset)
        total_duration = len(combined_audio) / 1000.0  # Update duration if silence was removed

        # 3. Save as MP3 to temporary location first
        temp_dir = Path("tmp/audio")
        temp_dir.mkdir(parents=True, exist_ok=True)
        temp_audio_path = temp_dir / f"episode_{episode_id}_{int(time.time())}.mp3"
        
        try:
            if PYDUB_AVAILABLE:
                bitrate = self.style_guide.styles.get("audio_quality", {}).get(quality_preset, "128k")
                logger.info(f"💾 Exporting optimized audio ({bitrate}) to temp: {temp_audio_path}...")
                combined_audio.export(str(temp_audio_path), format="mp3", bitrate=bitrate)
            else:
                logger.error("pydub is required to export MP3 with optimizations.")
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

        # 5. Add chapter markers if available
        if chapters and final_path:
            logger.info(f"🔖 Adding {len(chapters)} chapters to {final_path}")
            audio_storage_manager.add_chapters(final_path, chapters)

        return final_path

    def batch_generate_audio(self, episode_ids: List[int], force: bool = False, quality_preset: str = "standard", console: Optional[Any] = None) -> Dict[str, Any]:
        """
        Batch generate audio for multiple episodes.
        
        Args:
            episode_ids: List of episode IDs to process.
            force: Re-generate even if audio already exists.
            quality_preset: 'standard', 'high', or 'compact'.
            console: Rick console for progress reporting.
            
        Returns:
            Summary report dictionary.
        """
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeRemainingColumn
        
        total = len(episode_ids)
        generated_count = 0
        skipped_count = 0
        failed_count = 0
        total_duration = 0.0
        total_size = 0
        
        start_time = time.time()
        
        # Queue management file
        pause_file = Path("tmp/audio_gen.pause")
        
        def is_paused():
            return pause_file.exists()

        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            TimeRemainingColumn(),
            console=console,
            transient=False
        ) as progress:
            task = progress.add_task("[cyan]Generating Audio Queue...", total=total)
            
            for ep_id in episode_ids:
                # Check for pause
                while is_paused():
                    progress.update(task, description=f"[yellow]⏸️ Paused (Remove {pause_file} to resume)...[/yellow]")
                    time.sleep(2)
                
                entry = self.repo.get_entry_by_id(ep_id)
                if not entry:
                    failed_count += 1
                    progress.advance(task)
                    continue

                # Skip if already exists and not force
                if entry.audio_path and os.path.exists(entry.audio_path) and not force:
                    skipped_count += 1
                    progress.update(task, description=f"[dim]Skipping {ep_id} (already exists)[/dim]")
                    progress.advance(task)
                    continue

                progress.update(task, description=f"🎙️ Narrating {ep_id}: {entry.display_title()[:30]}...")
                
                try:
                    path = self.generate_audio(ep_id, quality_preset=quality_preset)
                    if path:
                        generated_count += 1
                        # Re-fetch entry to get updated duration/size
                        updated = self.repo.get_entry_by_id(ep_id)
                        total_duration += (updated.audio_duration or 0.0)
                        total_size += (updated.audio_file_size or 0)
                    else:
                        failed_count += 1
                except Exception as e:
                    logger.error(f"Failed batch gen for {ep_id}: {e}")
                    failed_count += 1
                
                progress.advance(task)

        elapsed = time.time() - start_time
        
        return {
            "total": total,
            "generated": generated_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "total_duration_sec": total_duration,
            "total_size_bytes": total_size,
            "elapsed_sec": elapsed
        }

    def _parse_sections(self, text: str) -> List[Dict]:
        """
        Parses text into a sequence of text blocks and pauses.
        
        Markers:
        - Acts: '### Cold Open', '### Act 1', etc.
        - Scenes: '---'
        - Paragraphs: '\n\n'
        """
        # First, split by likely Act markers
        act_pattern = r'(### (?:Cold Open|Act \d+|Act [IVXLCDM]+|Tag|Introduction|Conclusion|Opening|Closing))'
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
                    # Clean up marker for title (e.g., '### Act 1' -> 'Act 1')
                    title = parts[i].replace('###', '').strip()
                    raw_parts.append({"type": "chapter_marker", "text": title})
                else:
                    raw_parts.append({"type": "content", "text": parts[i]})

        # Sequence of (type, value) where type is 'text', 'pause', or 'chapter_marker'
        sequence = []
        
        # If the text doesn't start with a marker, add an implicit 'Intro' or 'Start'
        has_initial_marker = any(p["type"] == "chapter_marker" for p in raw_parts[:2])
        if not has_initial_marker:
            sequence.append({"type": "chapter_marker", "text": "Introduction"})

        for i, part in enumerate(raw_parts):
            if part["type"] == "chapter_marker":
                # Add a longer pause before a new act (except the very first item)
                if i > 0:
                    sequence.append({"type": "pause", "duration": self.PAUSES["act"]})
                
                sequence.append({"type": "chapter_marker", "text": part["text"]})
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

    def _post_process(self, audio: 'AudioSegment', quality_preset: str = 'standard') -> 'AudioSegment':
        """
        Applies audio optimizations:
        - Normalize levels (consistent volume)
        - Light compression (better listening)
        - Remove excessive silence (max 2 seconds)
        - Subtle fade in/out
        """
        if not PYDUB_AVAILABLE:
            return audio

        logger.info(f"✨ Optimizing audio pipeline (preset: {quality_preset})...")

        # 1. Remove excessive silence (max 2 seconds = 2000ms)
        try:
            silences = detect_silence(audio, min_silence_len=2000, silence_thresh=audio.dBFS - 16)
            if silences:
                # Process from end to start to maintain indices
                new_audio = audio
                for start, end in reversed(silences):
                    silence_duration = end - start
                    if silence_duration > 2000:
                        # Cap silence at 2 seconds
                        new_audio = new_audio[:start + 2000] + new_audio[end:]
                audio = new_audio
        except Exception as e:
            logger.warning(f"Failed to strip silence: {e}")

        # 2. Normalize audio levels
        try:
            audio = normalize(audio)
        except Exception as e:
            logger.warning(f"Failed to normalize audio: {e}")

        # 3. Apply light compression
        try:
            # -20.0 threshold is a reasonable starting point for speech
            audio = compress_dynamic_range(audio, threshold=-20.0, ratio=2.0)
        except Exception as e:
            logger.warning(f"Failed to apply compression: {e}")

        # 4. Add subtle fade in/out (500ms)
        audio = audio.fade_in(500).fade_out(500)

        return audio

    def _synthesize_and_combine(self, sequence: List[Dict], entry: Entry) -> Tuple[Optional['AudioSegment'], float, List[Dict]]:
        """
        Synthesizes text items and interleaves pauses.
        Returns: (AudioSegment, total_duration_seconds, chapter_list)
        """
        if not PYDUB_AVAILABLE:
            return None, 0.0, []

        combined = AudioSegment.empty()
        total_duration = 0.0
        chapters = []
        
        # Temporary directory for chunks
        temp_dir = Path("tmp/audio_chunks")
        temp_dir.mkdir(parents=True, exist_ok=True)

        try:
            for i, item in enumerate(sequence):
                if item["type"] == "chapter_marker":
                    # Record chapter start time in milliseconds
                    chapters.append({
                        "title": item["text"],
                        "start_ms": int(total_duration * 1000)
                    })
                
                elif item["type"] == "pause":
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
            
            return combined, total_duration, chapters
        except Exception as e:
            logger.error(f"Error during audio assembly: {e}")
            return None, 0.0, []


# Singleton instance
audio_generator = AudioEpisodeGenerator()
