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
from typing import Optional, Dict, List

try:
    from PIL import Image
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False

from .models import Entry
from .repository import get_repository
from .visual_prompts import mood_to_visual, VisualIdentity
from .image_client import ImageGenerator
from .conflict import ConflictDetector
from .storage import storage_manager

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


    def _add_to_history(self, episode: Entry):
        """Add current cover to history, keeping only max 5."""
        if not episode.cover_art_path:
            return

        # Check if already in history (to avoid duplicates if re-selecting)
        history_paths = [h.get("path") for h in episode.cover_history]
        if episode.cover_art_path in history_paths:
            return

        # Get style from metadata if possible, otherwise use setting
        style = self.repo.get_setting("visual_style", "cinematic")
        
        metadata = {
            "path": episode.cover_art_path,
            "prompt": episode.image_variants.get("prompt", "Unknown"),
            "style": style,
            "date": datetime.now().isoformat(),
            "variants": episode.image_variants,
            "settings": {} # Could store steps, sampler etc
        }

        episode.cover_history.insert(0, metadata)
        # Keep max 5
        episode.cover_history = episode.cover_history[:5]

    def select_cover(self, episode_id: int, history_index: int) -> bool:
        """Select a cover from history to be the active one."""
        episode = self.repo.get_entry_by_id(episode_id)
        if not episode or history_index >= len(episode.cover_history):
            return False

        # Add current to history before switching
        self._add_to_history(episode)

        # Move selected from history to active
        selected = episode.cover_history.pop(history_index)
        episode.cover_art_path = selected["path"]
        episode.image_variants = selected["variants"]
        
        self.repo.update_entry(episode)
        return True

    def generate_cover(
        self, 
        episode_id: int, 
        regenerate: bool = False, 
        style_name: Optional[str] = None,
        prompt_override: Optional[str] = None,
        variations: int = 1
    ) -> List[str]:
        """
        Generate one or more 16:9 landscape covers for the given episode.
        
        Args:
            episode_id: The ID of the episode to generate art for.
            regenerate: Whether to overwrite existing cover art.
            style_name: Optional style preset name to use.
            prompt_override: Optional custom prompt to use instead of generated one.
            variations: Number of variations to generate.
            
        Returns:
            List of paths to the generated images.
        """
        episode = self.repo.get_entry_by_id(episode_id)
        if not episode:
            logger.error(f"Episode {episode_id} not found.")
            return []

        if episode.cover_art_path and not regenerate and variations == 1 and not prompt_override and not style_name:
            if os.path.exists(episode.cover_art_path):
                logger.info(f"Cover art already exists for episode {episode_id}: {episode.cover_art_path}")
                return [episode.cover_art_path]

        # 1. Analyze episode: mood and visual moments
        if not episode.conflict_data:
            logger.info(f"Analyzing conflicts for episode {episode_id}...")
            episode.conflict_data = self.conflict_detector.analyze_entry(episode.raw_text)
            self.repo.update_entry(episode)

        # 2. Use MoodToVisualPrompt to create the prompt
        style = style_name or self.repo.get_setting("visual_style", "cinematic")
        pos_prompt, neg_prompt, preset = mood_to_visual.generate_cover_prompt(episode, style_name=style)
        
        if prompt_override:
            # Still use the identity layer but replace the core prompt
            pos_prompt = VisualIdentity.apply_identity(
                prompt_override, 
                season_number=episode.season_id, 
                episode_id=episode.id
            )
            logger.info(f"Using prompt override: {prompt_override}")
        else:
            # Inject central conflict into the prompt for narrative depth
            if episode.conflict_data and episode.conflict_data.central_conflict:
                pos_prompt = f"{pos_prompt}, depicting the struggle of: {episode.conflict_data.central_conflict}"

        # 3. Handle history if we are about to replace the active cover
        if episode.cover_art_path:
            self._add_to_history(episode)

        generated_paths = []
        
        for i in range(variations):
            logger.info(f"Generating cover variation {i+1}/{variations} for episode {episode_id} using style: {style}...")
            
            # Use a random seed for variations if i > 0
            current_seed = preset.get("seed")
            if i > 0 and current_seed is not None:
                current_seed += i * 77 # Simple offset for variations

            image_bytes = self.image_gen.generate(
                prompt=pos_prompt,
                negative_prompt=neg_prompt,
                width=1280,
                height=720,
                steps=preset.get("steps", 25),
                sampler_name=preset.get("sampler"),
                seed=current_seed
            )

            if not image_bytes:
                logger.error(f"Failed to generate image bytes for variation {i+1}")
                continue

            # 4. Save using ImageStorageManager
            try:
                variants = storage_manager.save_episode_images(episode_id, image_bytes, pos_prompt, is_primary=(i == 0))
                file_path = variants.get("original")
                
                # 5. For the FIRST variation (or single generation), it becomes the active cover
                if i == 0:
                    # save_episode_images already updates episode.cover_art_path and image_variants in DB
                    pass
                else:
                    # Add others to history immediately
                    history_item = {
                        "path": str(file_path),
                        "prompt": pos_prompt,
                        "style": style,
                        "date": datetime.now().isoformat(),
                        "variants": variants,
                        "settings": {"seed": current_seed, "steps": preset.get("steps"), "sampler": preset.get("sampler")}
                    }
                    episode.cover_history.insert(0, history_item)
                    episode.cover_history = episode.cover_history[:5]
                
                generated_paths.append(str(file_path))
            except Exception as e:
                logger.error(f"Error saving image variation {i}: {e}")
                continue

        # Final save
        self.repo.update_entry(episode)
        
        logger.info(f"Successfully generated {len(generated_paths)} covers.")
        return generated_paths

# Initialize a global instance
cover_generator = EpisodeCoverGenerator()
