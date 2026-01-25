"""
Chronicle AI - Visual Prompts
Mood-to-Visual Prompt Converter for SD-optimized cover art prompts.
"""

import logging
from typing import Dict, List, Tuple, Optional
from .models import Entry
from .llm_client import detect_mood, _make_request

class MoodToVisualPrompt:
    """
    Converts episode moods and narratives into rich, SD-optimized visual prompts.
    """
    
    MOOD_LIBRARY = {
        "anxious": {
            "elements": "cool blues, harsh shadows, isolated figure, frantic brushstrokes, sharp angles",
            "lighting": "cold fluorescent light, long distorted shadows",
            "atmosphere": "claustrophobic, tense, unsettling",
            "negative": "warm colors, soft light, cozy, relaxing, crowded, smiling, bright"
        },
        "triumphant": {
            "elements": "warm golds, dynamic pose, expansive vista, rays of light, heroic scale",
            "lighting": "divine golden hour, brilliant sunburst",
            "atmosphere": "epic, powerful, celebratory",
            "negative": "muted tones, dark, small, weak, static, dull, sad"
        },
        "melancholic": {
            "elements": "muted colors, rain, empty spaces, window reflection, wilted flowers",
            "lighting": "overcast gray light, dim interior",
            "atmosphere": "sad, reflective, quiet, somber",
            "negative": "vibrant colors, sunny, happy, busy, energetic, bright light"
        },
        "peaceful": {
            "elements": "soft light, nature, gentle tones, calm water, soft textures",
            "lighting": "soft diffused sunlight, ethereal glow",
            "atmosphere": "serene, tranquil, harmonious",
            "negative": "harsh shadows, high contrast, chaotic, urban, loud, sharp"
        },
        "adventurous": {
            "elements": "winding paths, mountain peaks, backpack, compass, rugged terrain",
            "lighting": "crisp morning light, clear blue sky",
            "atmosphere": "exciting, vast, energetic",
            "negative": "indoor, stagnant, domestic, boring, dark, closed spaces"
        },
        "lonely": {
            "elements": "single chair, empty street, silhouette, distant city lights",
            "lighting": "solitary street lamp, moonlight, cold blue hour",
            "atmosphere": "isolated, quiet, vast, distant",
            "negative": "crowds, parties, people talking, warmth, intimate, close-up"
        },
        "energetic": {
            "elements": "vivid colors, motion blur, fast movement, neon lights, urban rhythm",
            "lighting": "vibrant flashing lights, high contrast",
            "atmosphere": "dynamic, fast-paced, electric",
            "negative": "slow, static, pale, muted, sleepy, calm, boring"
        },
        "frustrated": {
            "elements": "crimson accents, cluttered desk, broken glass, messy environment",
            "lighting": "harsh red light, flickering bulbs",
            "atmosphere": "chaotic, heated, overwhelming",
            "negative": "organized, calm, blue, peaceful, slow, clear"
        },
        "hopeful": {
            "elements": "dawn breaking, sprout through concrete, far horizon, pastel colors",
            "lighting": "first light of morning, soft pinks and oranges",
            "atmosphere": "optimistic, fresh, beginning",
            "negative": "dead, dark, finality, ending, black, gray, heavy shadows"
        },
        "nostalgic": {
            "elements": "sepia tones, vintage objects, film grain, hazy memories",
            "lighting": "faded warm light, light leaks",
            "atmosphere": "sentimental, soft, dreamlike",
            "negative": "modern, high-tech, sharp, digital, neon, futuristic"
        }
    }

    QUALITY_BOOSTERS = "masterpiece, 8k, highly detailed, photorealistic, cinematic lighting, dramatic composition, professional photography"

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def _extract_visual_moments(self, narrative: str) -> str:
        """Extract key visual moments from the episode narrative using LLM."""
        if not narrative:
            return ""
            
        prompt = f"""Extract 2-3 key visual elements or striking images from this narrative for an image generation prompt.
Focus on tangible objects, settings, or poses.
Narrative: {narrative}
Visual elements (short phrases, comma separated):"""
        
        result = _make_request(prompt, timeout=20)
        if result:
            return result.strip().strip('"')
        return ""

    def generate_cover_prompt(self, episode: Entry) -> Tuple[str, str]:
        """
        Generate a positive and negative prompt for the episode's cover art.
        
        Args:
            episode: The Entry object containing narrative and other metadata.
            
        Returns:
            A tuple of (positive_prompt, negative_prompt).
        """
        text = episode.narrative_text or episode.raw_text
        mood = detect_mood(text)
        
        # Default to neutral/peaceful if mood not in library
        mood_data = self.MOOD_LIBRARY.get(mood, self.MOOD_LIBRARY["peaceful"])
        
        # Extract visual moments from narrative
        visual_moments = self._extract_visual_moments(text)
        
        # Compose positive prompt
        components = [
            f"A {mood} scene",
            visual_moments,
            mood_data["elements"],
            f"Lighting: {mood_data['lighting']}",
            f"Atmosphere: {mood_data['atmosphere']}",
            self.QUALITY_BOOSTERS
        ]
        
        # Filter out empty components
        positive_prompt = ", ".join([c for c in components if c])
        negative_prompt = f"low quality, blurry, distorted, {mood_data['negative']}"
        
        return positive_prompt, negative_prompt

# Initialize a global instance
mood_to_visual = MoodToVisualPrompt()
