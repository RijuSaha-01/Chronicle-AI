"""
Chronicle AI - Audio Storage Manager
Handles organized storage, metadata, playlist generation, and storage tracking for generated audio.
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from mutagen.mp3 import MP3
    from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, APIC, CHAP, CTOC
    MUTAGEN_AVAILABLE = True
except ImportError:
    MUTAGEN_AVAILABLE = False

from .repository import get_repository
from .models import Entry, Season

logger = logging.getLogger(__name__)

class AudioStorageManager:
    """
    Manages the filesystem storage of audio files with metadata and playlists.
    """

    def __init__(self, base_data_dir: str = "data"):
        self.base_dir = Path(base_data_dir) / "audio"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.repo = get_repository()

    def _get_episode_audio_path(self, episode: Entry) -> Path:
        """Get the storage path for an episode's audio file."""
        try:
            entry_date = datetime.strptime(episode.date, "%Y-%m-%d")
            year = str(entry_date.year)
        except (ValueError, TypeError):
            year = datetime.now().strftime("%Y")
        
        season_id = str(episode.season_id or "0")
        target_dir = self.base_dir / year / season_id
        target_dir.mkdir(parents=True, exist_ok=True)
        
        return target_dir / f"{episode.id}.mp3"

    def move_to_storage(self, episode_id: int, temp_audio_path: str, duration: float) -> str:
        """
        Moves a generated audio file from temp location to organized storage.
        Updates database and embeds metadata.
        """
        episode = self.repo.get_entry_by_id(episode_id)
        if not episode:
            raise ValueError(f"Episode {episode_id} not found")

        final_path = self._get_episode_audio_path(episode)
        
        # Ensure target directory exists
        final_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Move file
        shutil.move(temp_audio_path, final_path)
        
        # Update episode metadata
        episode.audio_path = str(final_path.absolute())
        episode.audio_duration = duration
        episode.audio_file_size = final_path.stat().st_size
        episode.audio_generation_date = datetime.now().isoformat()
        
        # Embed metadata including cover art
        self.embed_metadata(episode)
        
        # Update DB
        self.repo.update_entry(episode)
        
        logger.info(f"✅ Audio for episode {episode_id} moved to: {final_path}")
        return str(final_path)

    def embed_metadata(self, episode: Entry):
        """
        Embeds ID3 tags and cover art into the MP3 file.
        """
        if not MUTAGEN_AVAILABLE:
            logger.warning("Mutagen not available. Skipping ID3 metadata embedding.")
            return

        audio_path = episode.audio_path
        if not audio_path or not os.path.exists(audio_path):
            return

        try:
            audio = MP3(audio_path, ID3=ID3)
            
            # Create ID3 tags if they don't exist
            try:
                audio.add_tags()
            except:
                pass
            
            # Title
            audio.tags.add(TIT2(encoding=3, text=episode.title or f"Episode {episode.id}"))
            # Artist (Voice)
            audio.tags.add(TPE1(encoding=3, text=episode.tts_voice or "Chronicle AI Narrator"))
            
            # Album (Season)
            season_title = "Chronicle AI"
            if episode.season_id:
                season = self.repo.get_season_by_id(episode.season_id)
                if season:
                    season_title = season.title
            audio.tags.add(TALB(encoding=3, text=season_title))
            
            # Track Number
            audio.tags.add(TRCK(encoding=3, text=str(episode.id or "")))
            
            # Embed Cover Art
            if episode.cover_art_path and os.path.exists(episode.cover_art_path):
                try:
                    with open(episode.cover_art_path, 'rb') as img:
                        audio.tags.add(
                            APIC(
                                encoding=3, # 3 is for utf-8
                                mime='image/webp', # or image/jpeg
                                type=3, # 3 is for the cover image
                                desc=u'Cover',
                                data=img.read()
                            )
                        )
                except Exception as e:
                    logger.error(f"Failed to embed cover art: {e}")

            audio.save()
            logger.info(f"Metadata embedded for {audio_path}")
        except Exception as e:
            logger.error(f"Failed to embed ID3 tags: {e}")

    def add_chapters(self, audio_path: str, chapter_list: List[Dict]):
        """
        Embeds chapter markers into MP3 and creates a companion .chapters file.
        
        chapter_list: List of dicts with 'title' and 'start_ms'
        """
        if not os.path.exists(audio_path):
            return

        # 1. Embed chapters in ID3 if mutagen is available
        if MUTAGEN_AVAILABLE:
            try:
                audio = MP3(audio_path, ID3=ID3)
                
                # Table of Contents
                child_ids = [f"chp{i}" for i in range(len(chapter_list))]
                audio.tags.add(CTOC(
                    element_id="toc",
                    flags=3, # top-level, ordered
                    child_element_ids=child_ids
                ))
                
                # Individual Chapters
                for i, chap in enumerate(chapter_list):
                    start_ms = chap['start_ms']
                    # Use 0xFFFFFFFF (end of file) if it's the last chapter, otherwise next start_ms
                    end_ms = chapter_list[i+1]['start_ms'] if i + 1 < len(chapter_list) else 0xFFFFFFFF
                    
                    audio.tags.add(CHAP(
                        element_id=f"chp{i}",
                        start_time=start_ms,
                        end_time=end_ms,
                        sub_frames=[TIT2(encoding=3, text=chap['title'])]
                    ))
                
                audio.save()
                logger.info(f"Chapter frames embedded for {audio_path}")
            except Exception as e:
                logger.error(f"Failed to embed chapter frames: {e}")

        # 2. Create .chapters file
        chapters_file_path = Path(audio_path).with_suffix('.chapters')
        try:
            with open(chapters_file_path, "w", encoding="utf-8") as f:
                f.write("# Chronicle AI Chapters\n")
                print("\nChapter List:")
                for i, chap in enumerate(chapter_list):
                    start_ms = chap['start_ms']
                    # Calculate duration
                    if i + 1 < len(chapter_list):
                        duration_ms = chapter_list[i+1]['start_ms'] - start_ms
                    else:
                        # For last chapter, we need total duration. Let's try to get it from MP3
                        try:
                            audio = MP3(audio_path)
                            duration_ms = int(audio.info.length * 1000) - start_ms
                        except:
                            duration_ms = 0
                    
                    # Format timestamp HH:MM:SS.mmm
                    s, ms = divmod(start_ms, 1000)
                    m, s = divmod(s, 60)
                    h, m = divmod(m, 60)
                    timestamp = f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}"
                    
                    line = f"{timestamp} {chap['title']}"
                    f.write(f"{line}\n")
                    
                    # Log to console for user visibility
                    dur_s = duration_ms / 1000
                    print(f"- {chap['title']} at {timestamp} ({dur_s:.1f}s)")
                    
            logger.info(f"Companion chapters file created: {chapters_file_path}")
        except Exception as e:
            logger.error(f"Failed to create .chapters file: {e}")

    def generate_season_playlist(self, season_id: int) -> Optional[str]:
        """
        Generates a .m3u playlist for all episodes in a season.
        """
        season = self.repo.get_season_by_id(season_id)
        if not season:
            return None
            
        episodes = [e for e in self.repo.list_entries() if e.season_id == season_id and e.audio_path]
        # Sort by date
        episodes.sort(key=lambda x: x.date)
        
        if not episodes:
            return None
            
        try:
            start_date = season.start_date or datetime.now().strftime("%Y-%m-%d")
            year = start_date.split("-")[0]
        except:
            year = datetime.now().strftime("%Y")
            
        playlist_dir = self.base_dir / year / str(season_id)
        playlist_dir.mkdir(parents=True, exist_ok=True)
        
        playlist_path = playlist_dir / "playlist.m3u"
        
        with open(playlist_path, "w", encoding="utf-8") as f:
            f.write("#EXTM3U\n")
            for ep in episodes:
                f.write(f"#EXTINF:{int(ep.audio_duration or 0)},{ep.title or f'Episode {ep.id}'}\n")
                # Use relative path if possible, or absolute
                f.write(f"{os.path.basename(ep.audio_path)}\n")
                
        logger.info(f"Playlist generated: {playlist_path}")
        return str(playlist_path)

    def get_storage_usage(self) -> Dict[str, Any]:
        """Calculates total storage usage for audio."""
        total_size = 0
        file_count = 0
        total_duration = 0.0
        
        for root, dirs, files in os.walk(self.base_dir):
            for f in files:
                if f.endswith(".mp3"):
                    file_count += 1
                    total_size += os.path.getsize(os.path.join(root, f))
                    
        # Get duration from DB for all entries
        entries = self.repo.list_entries()
        for e in entries:
            if e.audio_path:
                total_duration += (e.audio_duration or 0.0)
                
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "total_duration_hours": round(total_duration / 3600, 2),
            "base_path": str(self.base_dir.absolute())
        }

    def export_audio(self, episode_id: int, target_path: str) -> bool:
        """
        Exports an episode's audio to a target path, preserving metadata.
        """
        episode = self.repo.get_entry_by_id(episode_id)
        if not episode or not episode.audio_path or not os.path.exists(episode.audio_path):
            return False
            
        try:
            # Ensure target directory exists
            Path(target_path).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(episode.audio_path, target_path)
            return True
        except Exception as e:
            logger.error(f"Failed to export audio: {e}")
            return False

# Global instance
audio_storage_manager = AudioStorageManager()
