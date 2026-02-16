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

    def generate_covers_batch(
        self, 
        episode_ids: List[int], 
        style_name: Optional[str] = None, 
        quality: str = "quality",
        clear_vram: bool = True
    ) -> Dict[int, List[str]]:
        """
        Processes multiple episodes in a queue with progress tracking and ETA.
        """
        total = len(episode_ids)
        results = {}
        start_time = time.time()
        
        print(f"\n--- Batch Image Generation Started ({total} covers) ---")
        
        for i, ep_id in enumerate(episode_ids):
            ep_start = time.time()
            progress = (i + 1) / total * 100
            
            # Calculate ETA
            elapsed = time.time() - start_time
            avg_time = elapsed / (i) if i > 0 else 0
            eta_secs = avg_time * (total - i)
            eta_str = f"{int(eta_secs // 60)}m {int(eta_secs % 60)}s" if i > 0 else "Calculating..."
            
            print(f"[{i+1}/{total}] {progress:.1f}% | ETA: {eta_str} | Processing Episode {ep_id}...")
            
            try:
                paths = self.generate_cover(
                    ep_id, 
                    style_name=style_name, 
                    quality_preset=quality
                )
                results[ep_id] = paths
                
                # Memory management: Clear VRAM between generations if requested
                if clear_vram and i < total - 1:
                    self.image_gen.unload_models()
                    
            except Exception as e:
                logger.error(f"Failed to generate cover for episode {ep_id}: {e}")
                results[ep_id] = []
        
        total_time = time.time() - start_time
        print(f"\n--- Batch Generation Complete! Total time: {total_time:.1f}s ---\n")
        return results

    def generate_cover(
        self, 
        episode_id: int, 
        regenerate: bool = False, 
        style_name: Optional[str] = None,
        prompt_override: Optional[str] = None,
        variations: int = 1,
        quality_preset: str = "quality"
    ) -> List[str]:
        """
        Generate one or more 16:9 landscape covers for the given episode.
        Optimized with caching and quality presets.
        """
        episode = self.repo.get_entry_by_id(episode_id)
        if not episode:
            logger.error(f"Episode {episode_id} not found.")
            return []

        # 1. Analyze and prepare prompts
        style = style_name or self.repo.get_setting("visual_style", "cinematic")
        if not episode.mood or regenerate:
            episode.mood = mood_to_visual._detect_detailed_mood(episode.narrative_text or episode.raw_text)
        
        pos_prompt, neg_prompt, preset = mood_to_visual.generate_cover_prompt(episode, style_name=style)
        
        if prompt_override:
            pos_prompt = VisualIdentity.apply_identity(prompt_override, episode.season_id, episode.id)
        elif episode.conflict_data and episode.conflict_data.central_conflict:
            pos_prompt = f"{pos_prompt}, depicting the struggle of: {episode.conflict_data.central_conflict}"

        # Caching logic: Skip if prompt and style haven't changed
        current_config = {
            "prompt": pos_prompt,
            "style": style,
            "quality": quality_preset
        }
        
        # Check if we already have this exact generation
        # Stored in episode.image_variants["config"]
        last_config = (episode.image_variants or {}).get("config", {})
        if not regenerate and variations == 1 and last_config == current_config:
            if episode.cover_art_path and os.path.exists(episode.cover_art_path):
                logger.info(f"Skipping generation for episode {episode_id} (cache hit)")
                return [episode.cover_art_path]

        # 2. Set steps based on quality preset
        steps = preset.get("steps", 25)
        if quality_preset == "fast":
            steps = max(12, int(steps * 0.6))
        elif quality_preset == "quality":
            steps = min(50, int(steps * 1.2))

        # 3. Handle history
        if episode.cover_art_path:
            self._add_to_history(episode)

        generated_paths = []
        
        for i in range(variations):
            current_seed = preset.get("seed")
            if i > 0 and current_seed is not None:
                current_seed += i * 77

            sd_available = self.image_gen.check_health()
            image_bytes = None
            is_placeholder = False

            if sd_available:
                image_bytes = self.image_gen.generate(
                    prompt=pos_prompt,
                    negative_prompt=neg_prompt,
                    width=1280,
                    height=720,
                    steps=steps,
                    sampler_name=preset.get("sampler"),
                    seed=current_seed
                )
            
            if not image_bytes:
                image_bytes = self._generate_gradient_fallback(episode.mood or "peaceful")
                is_placeholder = True
                episode.needs_image_retry = True
            else:
                episode.needs_image_retry = False

            if not image_bytes:
                continue

            # 4. Save and generate thumbnails in parallel
            try:
                save_prompt = pos_prompt if not is_placeholder else f"Placeholder: {episode.mood}"
                
                # We modify storage_manager to handle parallel generation internally 
                # or we just call it here. For the "Parallel thumbnail generation" requirement,
                # I'll update save_episode_images to use a ThreadPoolExecutor.
                
                variants = storage_manager.save_episode_images(
                    episode_id, 
                    image_bytes, 
                    save_prompt, 
                    is_primary=(i == 0),
                    is_placeholder=is_placeholder
                )
                
                # Inject config for caching
                if i == 0:
                    episode.image_variants["config"] = current_config
                    episode.is_placeholder = is_placeholder
                
                file_path = variants.get("original")
                
                if i > 0:
                    history_item = {
                        "path": str(file_path),
                        "prompt": save_prompt,
                        "style": style,
                        "date": datetime.now().isoformat(),
                        "variants": variants,
                        "settings": {"seed": current_seed, "steps": steps, "sampler": preset.get("sampler")},
                        "is_placeholder": is_placeholder,
                        "config": current_config
                    }
                    episode.cover_history.insert(0, history_item)
                    episode.cover_history = episode.cover_history[:5]
                
                generated_paths.append(str(file_path))
            except Exception as e:
                logger.error(f"Error saving image variation {i}: {e}")
                continue

        self.repo.update_entry(episode)
        return generated_paths

# Initialize a global instance
cover_generator = EpisodeCoverGenerator()
