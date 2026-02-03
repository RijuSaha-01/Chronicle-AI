"""
Chronicle AI - Episode Cover Generator
Analyzes episode metadata and generates cinematic 16:9 landscape covers.
"""

import os
import logging
import io
import base64
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from .models import Entry
from .repository import get_repository
from .visual_prompts import mood_to_visual
from .image_client import ImageGenerator
from .conflict import ConflictDetector

logger = logging.getLogger(__name__)

class EpisodeCoverGenerator:
    """
    Orchestrates the analysis and generation of episode cover art.
    """

    def __init__(self, image_gen: Optional[ImageGenerator] = None, base_data_dir: str = "data"):
        self.repo = get_repository()
        # Default to localhost ComfyUI if no client provided
        self.image_gen = image_gen or ImageGenerator(base_url="http://127.0.0.1:8188", backend="comfyui")
        self.conflict_detector = ConflictDetector()
        self.base_data_dir = base_data_dir

    def process_image_variants(self, image_bytes: bytes, target_dir: Path) -> Dict[str, str]:
        """
        Process the primary image into multiple variants and generate a blur placeholder.
        
        Variants:
        - Original: 1280x720 (webp)
        - Medium: 640x360 (webp)
        - Small: 320x180 (webp)
        - Square: 400x400 (webp)
        - Blur: Tiny base64
        """
        if not PILLOW_AVAILABLE:
            logger.warning("Pillow not installed. Skipping thumbnail generation.")
            return {}

        try:
            img = Image.open(io.BytesIO(image_bytes))
            variants = {}
            
            # Define sizes: (name, width, height, is_square)
            sizes = [
                ("original", 1280, 720, False),
                ("medium", 640, 360, False),
                ("small", 320, 180, False),
                ("square", 400, 400, True),
            ]
            
            for name, w, h, is_square in sizes:
                if is_square:
                    # Center crop to square
                    min_dim = min(img.width, img.height)
                    left = (img.width - min_dim) / 2
                    top = (img.height - min_dim) / 2
                    right = (img.width + min_dim) / 2
                    bottom = (img.height + min_dim) / 2
                    variant_img = img.crop((left, top, right, bottom))
                    variant_img = variant_img.resize((w, h), Image.Resampling.LANCZOS)
                else:
                    # Maintain aspect ratio for others (target is 16:9)
                    variant_img = img.resize((w, h), Image.Resampling.LANCZOS)
                
                variant_path = target_dir / f"{name}.webp"
                variant_img.save(variant_path, "WEBP", quality=85)
                variants[name] = str(variant_path)
                
            # Generate blur placeholder (e.g., 20x11 for 16:9)
            blur_img = img.resize((20, 11), Image.Resampling.BOX)
            buffered = io.BytesIO()
            blur_img.save(buffered, format="WEBP", quality=10)
            blur_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            variants["blur"] = f"data:image/webp;base64,{blur_base64}"
            
            return variants
        except Exception as e:
            logger.error(f"Error processing image variants: {e}")
            return {}

    def generate_cover(self, episode_id: int, regenerate: bool = False) -> Optional[str]:
        """
        Generate a 16:9 landscape cover for the given episode.
        
        Args:
            episode_id: The ID of the episode to generate art for.
            regenerate: Whether to overwrite existing cover art.
            
        Returns:
            The path to the generated image, or None if failed.
        """
        episode = self.repo.get_entry_by_id(episode_id)
        if not episode:
            logger.error(f"Episode {episode_id} not found.")
            return None

        if episode.cover_art_path and not regenerate:
            if os.path.exists(episode.cover_art_path):
                logger.info(f"Cover art already exists for episode {episode_id}: {episode.cover_art_path}")
                return episode.cover_art_path

        # 1. Analyze episode: mood and visual moments
        # We ensure conflict data exists as requested
        if not episode.conflict_data:
            logger.info(f"Analyzing conflicts for episode {episode_id}...")
            episode.conflict_data = self.conflict_detector.analyze_entry(episode.raw_text)
            self.repo.update_entry(episode)

        # 2. Use MoodToVisualPrompt to create the prompt
        style = self.repo.get_setting("visual_style", "cinematic")
        pos_prompt, neg_prompt, preset = mood_to_visual.generate_cover_prompt(episode, style_name=style)
        
        # Inject central conflict into the prompt for narrative depth
        if episode.conflict_data and episode.conflict_data.central_conflict:
            pos_prompt = f"{pos_prompt}, depicting the struggle of: {episode.conflict_data.central_conflict}"

        # 3. Generate 16:9 landscape cover (1280x720)
        logger.info(f"Generating 16:9 cover for episode {episode_id} using style: {style}...")
        image_bytes = self.image_gen.generate(
            prompt=pos_prompt,
            negative_prompt=neg_prompt,
            width=1280,
            height=720,
            steps=preset.get("steps", 25),
            sampler_name=preset.get("sampler"),
            seed=preset.get("seed")
        )

        if not image_bytes:
            logger.error(f"Failed to generate image bytes for episode {episode_id}")
            return None

        # 4. Save to: /data/images/{year}/{season}/{episode_id}/cover.png
        try:
            entry_date = datetime.strptime(episode.date, "%Y-%m-%d")
            year = str(entry_date.year)
        except (ValueError, TypeError):
            year = datetime.now().strftime("%Y")
            
        season = str(episode.season_id or "0")
        
        # Ensure the directory exists
        target_dir = Path(self.base_data_dir) / "images" / year / season / str(episode_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # 4. Generate variants (including cover.webp and thumbnails)
        variants = self.process_image_variants(image_bytes, target_dir)
        
        # 5. Save the primary PNG for backward compatibility (optional, but good for now)
        file_path = target_dir / "cover.png"
        with open(file_path, "wb") as f:
            f.write(image_bytes)
            
        # 6. Link image path and variants to episode in database
        episode.cover_art_path = str(file_path)
        episode.image_variants = variants
        self.repo.update_entry(episode)
        
        logger.info(f"Successfully generated and linked cover art and {len(variants)} variants.")
        return str(file_path)

# Initialize a global instance
cover_generator = EpisodeCoverGenerator()
