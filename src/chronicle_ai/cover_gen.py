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
    from PIL import Image, ImageDraw
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

    def _generate_gradient_fallback(self, mood: str, width: int = 1280, height: int = 720) -> Optional[bytes]:
        """Generate a gradient-based fallback image from mood colors."""
        if not PILLOW_AVAILABLE:
            logger.error("Pillow not available, cannot generate gradient fallback")
            return None
            
        mood_data = mood_to_visual.MOOD_LIBRARY.get(mood, mood_to_visual.MOOD_LIBRARY["peaceful"])
        colors = mood_data.get("colors", ["#434343", "#000000"])
        
        # Convert hex to RGB
        def hex_to_rgb(hex_str):
            hex_str = hex_str.lstrip('#')
            return tuple(int(hex_str[i:i+2], 16) for i in (0, 2, 4))
            
        c1 = hex_to_rgb(colors[0])
        c2 = hex_to_rgb(colors[1])
        
        image = Image.new('RGB', (width, height))
        draw = ImageDraw.Draw(image)
        
        # Draw vertical gradient
        for y in range(height):
            r = int(c1[0] + (c2[0] - c1[0]) * y / height)
            g = int(c1[1] + (c2[1] - c1[1]) * y / height)
            b = int(c1[2] + (c2[2] - c1[2]) * y / height)
            draw.line([(0, y), (width, y)], fill=(r, g, b))
            
        # Add a subtle "Placeholder" indicator
        try:
            # We don't want to depend on font files, so we just use the default if possible
            # or skip text. The requirement says "Show clear indicator when image is placeholder vs generated"
            # We will use metadata and filename for that, but maybe a subtle overlay helps.
            pass
        except Exception:
            pass
            
        buf = io.BytesIO()
        image.save(buf, format='WEBP', quality=80)
        return buf.getvalue()


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
            "settings": {}, # Could store steps, sampler etc
            "is_placeholder": episode.is_placeholder
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
        
        # Detect mood if not already present or if regenerating
        if not episode.mood or regenerate:
            episode.mood = mood_to_visual._detect_detailed_mood(episode.narrative_text or episode.raw_text)
        
        episode.style = style
        
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

            # Check if SD is available
            sd_available = self.image_gen.check_health()
            image_bytes = None
            is_placeholder = False

            if sd_available:
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
                if sd_available:
                    logger.warning(f"SD generation failed for variation {i+1}, using gradient fallback")
                else:
                    logger.info(f"SD is unavailable, generating gradient fallback for {episode.mood}")
                
                image_bytes = self._generate_gradient_fallback(episode.mood or "peaceful")
                is_placeholder = True
                episode.needs_image_retry = True
            else:
                episode.needs_image_retry = False
                is_placeholder = False

            if not image_bytes:
                logger.error(f"Failed to generate ANY image bytes for variation {i+1}")
                continue

            # 4. Save using ImageStorageManager
            try:
                # Add indicator to prompt if it's a placeholder
                save_prompt = pos_prompt if not is_placeholder else f"Placeholder: {episode.mood}"
                variants = storage_manager.save_episode_images(
                    episode_id, 
                    image_bytes, 
                    save_prompt, 
                    is_primary=(i == 0),
                    is_placeholder=is_placeholder
                )
                file_path = variants.get("original")
                
                # Update placeholder flag in episode
                if i == 0:
                    episode.is_placeholder = is_placeholder
                
                # 5. For the FIRST variation (or single generation), it becomes the active cover
                if i == 0:
                    # save_episode_images already updates episode.cover_art_path and image_variants in DB
                    pass
                else:
                    # Add others to history immediately
                    history_item = {
                        "path": str(file_path),
                        "prompt": save_prompt,
                        "style": style,
                        "date": datetime.now().isoformat(),
                        "variants": variants,
                        "settings": {"seed": current_seed, "steps": preset.get("steps"), "sampler": preset.get("sampler")},
                        "is_placeholder": is_placeholder
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
