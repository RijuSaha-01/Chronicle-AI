"""
Chronicle AI - Image Storage Manager
Handles organized storage, metadata, cleanup, and usage tracking for generated images.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from .repository import get_repository
from .models import Entry, Season

logger = logging.getLogger(__name__)

class ImageStorageManager:
    """
    Manages the filesystem storage of images with metadata and variants.
    """

    def __init__(self, base_data_dir: str = "data"):
        self.base_dir = Path(base_data_dir) / "images"
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.repo = get_repository()

    def _get_episode_path(self, episode: Entry) -> Path:
        """Get the storage directory for an episode's images."""
        try:
            entry_date = datetime.strptime(episode.date, "%Y-%m-%d")
            year = str(entry_date.year)
        except (ValueError, TypeError):
            year = datetime.now().strftime("%Y")
        
        season_id = str(episode.season_id or "0")
        return self.base_dir / year / season_id / str(episode.id)

    def _get_season_path(self, season: Season) -> Path:
        """Get the storage directory for a season's images."""
        start_date = season.start_date or datetime.now().strftime("%Y-%m-%d")
        try:
            year = start_date.split("-")[0]
        except (IndexError, AttributeError):
            year = datetime.now().strftime("%Y")
            
        return self.base_dir / year / str(season.id) / "season_assets"

    def save_episode_images(self, episode_id: int, image_bytes: bytes, prompt: str, is_primary: bool = True, is_placeholder: bool = False) -> Dict[str, str]:
        """
        Saves the primary cover and generated variants for an episode.
        
        Names: cover.webp, thumb_md.webp, thumb_sm.webp
        """
        episode = self.repo.get_entry_by_id(episode_id)
        if not episode:
            raise ValueError(f"Episode {episode_id} not found")

        target_dir = self._get_episode_path(episode)
        target_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suffix = "" if is_primary else f"_{timestamp}"
        
        variants = {}
        
        if not PILLOW_AVAILABLE:
            main_path = target_dir / f"cover{suffix}.png"
            with open(main_path, "wb") as f:
                f.write(image_bytes)
            variants["original"] = str(main_path)
            return variants

        from io import BytesIO
        img = Image.open(BytesIO(image_bytes))
        
        # 1. Primary Cover (WebP) - use exact name if primary
        cover_filename = f"cover{suffix}.webp"
        cover_path = target_dir / cover_filename
        img.save(cover_path, "WEBP", quality=90)
        variants["original"] = str(cover_path)

        # 2. Medium Thumbnail (640x360)
        thumb_md_filename = f"thumb_md{suffix}.webp"
        thumb_md_path = target_dir / thumb_md_filename
        img.resize((640, 360), Image.Resampling.LANCZOS).save(thumb_md_path, "WEBP", quality=80)
        variants["medium"] = str(thumb_md_path)

        # 3. Small Thumbnail (320x180)
        thumb_sm_filename = f"thumb_sm{suffix}.webp"
        thumb_sm_path = target_dir / thumb_sm_filename
        img.resize((320, 180), Image.Resampling.LANCZOS).save(thumb_sm_path, "WEBP", quality=75)
        variants["small"] = str(thumb_sm_path)
        
        # 4. Poster variant (vertical 2:3) if helpful
        if is_primary:
            poster_path = target_dir / f"poster{suffix}.webp"
            # Crop to 2:3
            target_ratio = 2/3
            curr_ratio = img.width / img.height
            if curr_ratio > target_ratio:
                # Too wide, crop sides
                new_width = int(img.height * target_ratio)
                offset = (img.width - new_width) // 2
                poster_img = img.crop((offset, 0, offset + new_width, img.height))
            else:
                # Too tall, crop top/bottom
                new_height = int(img.width / target_ratio)
                offset = (img.height - new_height) // 2
                poster_img = img.crop((0, offset, img.width, offset + new_height))
            
            poster_img.resize((800, 1200), Image.Resampling.LANCZOS).save(poster_path, "WEBP", quality=85)
            variants["poster"] = str(poster_path)

        # 5. Meta JSON
        metadata = {
            "prompt": prompt,
            "date": datetime.now().isoformat(),
            "dimensions": f"{img.width}x{img.height}",
            "file_size": len(image_bytes),
            "episode_id": episode_id,
            "season_id": episode.season_id,
            "is_primary": is_primary,
            "is_placeholder": is_placeholder
        }
        
        meta_filename = f"metadata{suffix}.json"
        with open(target_dir / meta_filename, "w") as f:
            json.dump(metadata, f, indent=4)

        if is_primary:
            # Update Episode in DB
            episode.cover_art_path = str(cover_path)
            episode.image_variants = variants
            episode.is_placeholder = is_placeholder
            self.repo.update_entry(episode)

        return variants

    def save_season_poster(self, season_id: int, image_bytes: bytes, prompt: str) -> str:
        """Saves the season poster and updates link."""
        season = self.repo.get_season_by_id(season_id)
        if not season:
            raise ValueError(f"Season {season_id} not found")

        target_dir = self._get_season_path(season)
        target_dir.mkdir(parents=True, exist_ok=True)

        poster_path = target_dir / "poster.webp"
        
        img_width, img_height = 0, 0
        if PILLOW_AVAILABLE:
            from io import BytesIO
            img = Image.open(BytesIO(image_bytes))
            img_width, img_height = img.width, img.height
            img.save(poster_path, "WEBP", quality=90)
        else:
            with open(poster_path, "wb") as f:
                f.write(image_bytes)

        metadata = {
            "prompt": prompt,
            "date": datetime.now().isoformat(),
            "dimensions": f"{img_width}x{img_height}",
            "file_size": len(image_bytes),
            "season_id": season_id
        }
        with open(target_dir / "metadata.json", "w") as f:
            json.dump(metadata, f, indent=4)

        season.poster_path = str(poster_path)
        self.repo.update_season(season)
        
        return str(poster_path)

    def get_storage_usage(self) -> Dict[str, Any]:
        """Calculates total storage usage for images."""
        total_size = 0
        file_count = 0
        
        for root, dirs, files in os.walk(self.base_dir):
            for f in files:
                file_count += 1
                total_size += os.path.getsize(os.path.join(root, f))
        
        return {
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "file_count": file_count,
            "base_path": str(self.base_dir)
        }

    def cleanup_orphaned_images(self) -> List[str]:
        """
        Removes image directories that don't have a linked episode or season.
        Returns list of deleted paths.
        """
        deleted_paths = []
        
        # Get all valid IDs from DB
        entries = self.repo.list_entries()
        seasons = self.repo.list_seasons()
        
        valid_episode_ids = {str(e.id) for e in entries}
        valid_season_ids = {str(s.id) for s in seasons}
        
        # Traverse years
        for year_dir in self.base_dir.iterdir():
            if not year_dir.is_dir(): continue
            
            for season_dir in year_dir.iterdir():
                if not season_dir.is_dir(): continue
                
                # Check if season itself exists
                if season_dir.name not in valid_season_ids and season_dir.name != "0":
                    logger.info(f"Orphaned season dir found: {season_dir}")
                    # shutil.rmtree(season_dir)
                    # deleted_paths.append(str(season_dir))
                    # Deprioritizing full season delete for safety, focus on episodes
                    pass
                
                for episode_dir in season_dir.iterdir():
                    if not episode_dir.is_dir(): continue
                    
                    if episode_dir.name == "season_assets":
                        # Check if season exists
                        if season_dir.name not in valid_season_ids:
                             shutil.rmtree(episode_dir)
                             deleted_paths.append(str(episode_dir))
                        continue
                        
                    if episode_dir.name not in valid_episode_ids:
                        logger.info(f"Removing orphaned episode images: {episode_dir}")
                        shutil.rmtree(episode_dir)
                        deleted_paths.append(str(episode_dir))
                        
        return deleted_paths

    def backup_images(self, export_path: Optional[str] = None) -> str:
        """
        Exports all images and their metadata to a zip file.
        """
        if not export_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = f"exports/chronicle_images_backup_{timestamp}.zip"
            
        Path(export_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Simply zip the images directory
        shutil.make_archive(export_path.replace(".zip", ""), 'zip', self.base_dir)
        
        return export_path + ".zip" if not export_path.endswith(".zip") else export_path

# Global instance
storage_manager = ImageStorageManager()
