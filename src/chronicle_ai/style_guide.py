"""
Chronicle AI - Cinematic Style Guide

Enhances narrative generation with cinematic instructions and sensory layers.
"""

import json
import os
import random
from typing import Dict, List, Optional


class CinematicStyleGuide:
    """
    Manages cinematic styles and sensory details to enrich AI-generated narratives.
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the style guide by loading stylistic preferences from a config file.
        
        Args:
            config_path: Path to the style configuration JSON file.
        """
        if config_path is None:
            # Default to style_config.json in the same directory as this file
            config_path = os.path.join(os.path.dirname(__file__), "style_config.json")
        
        self.config_path = config_path
        self.styles = self._load_config()

    def _load_config(self) -> Dict:
        """Loads configuration from the JSON file, or returns defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                # In a real app we might use a logger, but for now we fallback
                pass
        
        # Fallback defaults in case file is missing or corrupted
        return {
            "camera_angles": ["close-up", "wide shot", "tracking shot"],
            "lighting": ["harsh fluorescent", "golden hour warmth"],
            "atmospheres": ["heavy with anticipation", "quiet and reflective"],
            "mood_mappings": {
                "neutral": {"camera": "wide shot", "lighting": "natural light", "atmosphere": "calm"}
            },
            "sensory_elements": {
                "sounds": ["a distant hum"],
                "textures": ["a cool breeze"],
                "smells": ["fresh air"]
            }
        }

    def enhance_prompt(self, base_prompt: str, mood: str = "neutral") -> str:
        """
        Adds cinematic instructions to a base prompt based on the specified mood.
        
        Args:
            base_prompt: The initial prompt for narrative generation.
            mood: The desired mood for the scene.
            
        Returns:
            An enhanced prompt with specific cinematic directives.
        """
        mood_map = self.styles.get("mood_mappings", {})
        
        # Get style for the specific mood, or pick random ones
        mapping = mood_map.get(mood.lower(), {})
        
        camera = mapping.get("camera") or random.choice(self.styles.get("camera_angles", ["medium shot"]))
        lighting = mapping.get("lighting") or random.choice(self.styles.get("lighting", ["natural light"]))
        atmosphere = mapping.get("atmosphere") or random.choice(self.styles.get("atmospheres", ["neutral"]))
        
        cinematic_instructions = (
            f"\n\nVISUAL DIRECTION:\n"
            f"- Imagine the scene captured with a {camera}.\n"
            f"- Set the mood using {lighting} illumination.\n"
            f"- The air should feel {atmosphere}."
            f"\nMaintain this artistic lens throughout the narrative."
        )
        
        return base_prompt + cinematic_instructions

    def get_scene_direction(self, scene_type: str) -> str:
        """
        Returns appropriate visual language for a given scene type.
        
        Args:
            scene_type: The type of scene (e.g., 'morning', 'afternoon', 'night').
            
        Returns:
            A string describing the visual direction.
        """
        directions = {
            "morning": "The world awakens in cool, blue tones, shadows long and soft.",
            "afternoon": "High contrast and sharp lines. The heat of the day is visible in the shimmer.",
            "night": "Deep blacks and pools of artificial light. Every sound echoes.",
            "action": "Fast-paced motion blur and tight framing on specific movements.",
            "reflective": "Lingering close-ups on hands, faces, and small objects."
        }
        return directions.get(scene_type.lower(), "Balanced framing with clear, descriptive visuals.")

    def add_sensory_layer(self, text: str) -> str:
        """
        Enriches a piece of text with sensory details (sounds, textures, smells).
        
        Args:
            text: The narrative text to enrich.
            
        Returns:
            The text with an added sensory layer.
        """
        if not text or len(text) < 10:
            return text

        sensory = self.styles.get("sensory_elements", {})
        sound = random.choice(sensory.get("sounds", ["a subtle hum"]))
        texture = random.choice(sensory.get("textures", ["a faint touch"]))
        smell = random.choice(sensory.get("smells", ["fresh air"]))

        # Append sensory details in a way that feels natural for a story
        sensory_addition = f"\n\nUnderneath it all, {sound} persists. There's {texture} in the air, accompanied by the faint scent of {smell}."
        
        return text.rstrip() + sensory_addition
