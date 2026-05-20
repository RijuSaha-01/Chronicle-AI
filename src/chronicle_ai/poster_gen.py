"""
Chronicle AI - Season Poster Generator
Analyzes season metadata/episodes and generates cinematic 2:3 vertical movie posters.
"""

import os
import logging
import io
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from .models import Season, SeasonArc
from .repository import get_repository
from .arc_analyzer import SeasonArcAnalyzer
from .image_client import ImageGenerator
from .storage import storage_manager

logger = logging.getLogger(__name__)

class SeasonPosterGenerator:
    """
    Orchestrates the analysis and generation of season poster art.
    """

    def __init__(self, image_gen: Optional[ImageGenerator] = None, base_data_dir: str = "data"):
        self.repo = get_repository()
        # Default to localhost ComfyUI if no client provided, supporting configuration via environment variables
        sd_url = os.getenv("STABLE_DIFFUSION_URL") or os.getenv("SD_URL", "http://127.0.0.1:8188")
        sd_backend = os.getenv("STABLE_DIFFUSION_BACKEND", "comfyui")
        self.image_gen = image_gen or ImageGenerator(base_url=sd_url, backend=sd_backend)
        self.arc_analyzer = SeasonArcAnalyzer(repository=self.repo)
        self.base_data_dir = base_data_dir

    def generate_poster(self, season_id: int, variant: str = "dramatic", regenerate: bool = False) -> Optional[str]:
        """
        Generate a 2:3 vertical movie poster (800x1200) for the given season.
        
        Args:
            season_id: The ID of the season to generate art for.
            variant: The artistic variant ('dramatic', 'minimalist', 'artistic').
            regenerate: Whether to overwrite existing poster art.
            
        Returns:
            The path to the generated image, or None if failed.
        """
        season = self.repo.get_season_by_id(season_id)
        if not season:
            logger.error(f"Season {season_id} not found.")
            return None

        # Check if already exists for this variant
        if not regenerate and season.poster_variants and variant in season.poster_variants:
            path = season.poster_variants[variant]
            if os.path.exists(path):
                logger.info(f"Poster variant '{variant}' already exists for season {season_id}: {path}")
                return path

        # 1. Ensure season arc analysis exists
        if not season.arc_analysis or not season.arc_analysis.summary:
            logger.info(f"Performing arc analysis for season {season_id}...")
            season.arc_analysis = self.arc_analyzer.analyze_season(season_id)

        # 2. Build prompt based on variant and season arc
        pos_prompt, neg_prompt = self._build_poster_prompt(season, variant)

        # 3. Generate 2:3 vertical poster (800x1200)
        # Using higher quality settings: more steps (35), better sampler
        logger.info(f"Generating {variant} poster for season {season_id} ({season.title})...")
        image_bytes = self.image_gen.generate(
            prompt=pos_prompt,
            negative_prompt=neg_prompt,
            width=800,
            height=1200,
            steps=35,
            sampler_name="DPM++ 2M Karras",
            seed=None # Random seed for variants
        )

        if not image_bytes:
            logger.error(f"Failed to generate poster bytes for season {season_id}")
            return None

        # 4. Save using ImageStorageManager
        try:
            poster_path = storage_manager.save_season_poster(season_id, image_bytes, pos_prompt)
            
            # 5. Update season metadata (variants support)
            if not season.poster_variants:
                season.poster_variants = {}
            
            season.poster_variants[variant] = poster_path
            
            # Set primary path to the dramatic one or the first one generated
            if variant == "dramatic" or not season.poster_path:
                season.poster_path = poster_path
                
            self.repo.update_season(season)
            
            logger.info(f"Successfully generated and linked {variant} poster for season {season_id}.")
            return poster_path
        except Exception as e:
            logger.error(f"Error saving season poster: {e}")
            return None

    def _build_poster_prompt(self, season: Season, variant: str) -> (str, str):
        """Constructs artistic prompts based on season analysis and style variant."""
        arc = season.arc_analysis
        motifs = ", ".join(arc.motifs) if arc.motifs else season.title
        summary = arc.summary[:500] # Limit summary length
        
        base_quality = "masterpiece, high quality, 8k, highly detailed, cinematic lighting, movie poster aesthetic"
        neg_prompt = "text, watermark, logo, blurry, low quality, distorted, deformed, ugly, bad anatomy, bad hands, multiple people if not specified"

        if variant == "minimalist":
            pos_prompt = f"Minimalist movie poster for a season titled '{season.title}'. Visual motifs: {motifs}. Symbolic representation of {summary}. Flat design, bold composition, negative space, elegant typography influence (but no text), vector style, iconic imagery."
        elif variant == "artistic":
            pos_prompt = f"Artistic, abstract movie poster for '{season.title}'. Themes of {motifs}. Impressionistic, oil painting style, vibrant textures, emotional color palette, dreamlike atmosphere, representing {summary}. Fine art aesthetic."
        else: # dramatic (default)
            pos_prompt = f"Dramatic cinematic movie poster for '{season.title}'. Starring the motifs: {motifs}. High contrast, deep shadows, epic scale, moody atmosphere, representing the arc: {summary}. Professional color grading, blockbuster style."

        return f"{pos_prompt}, {base_quality}", neg_prompt

# Initialize a global instance
poster_generator = SeasonPosterGenerator()
