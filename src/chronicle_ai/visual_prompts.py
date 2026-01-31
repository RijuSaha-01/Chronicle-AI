"""
Chronicle AI - Visual Prompts
Mood-to-Visual Prompt Converter for SD-optimized cover art prompts.
"""

import logging
from typing import Dict, List, Tuple, Optional
from .models import Entry
from .llm_utils import _make_request

class VisualStylePresets:
    """
    Defines 5 distinct visual looks for Chronicle AI cover art.
    """
    CINEMATIC = {
        "name": "CINEMATIC",
        "description": "Film grain, dramatic lighting, realistic photography style",
        "positive": "cinematic film, 35mm, film grain, dramatic lighting, realistic photography, masterful cinematography, high dynamic range",
        "negative": "cartoon, anime, drawing, illustration, sketch, low contrast, flat lighting, CG, 3d render",
        "sampler": "DPM++ 2M Karras",
        "steps": 30
    }
    ANIME = {
        "name": "ANIME",
        "description": "Studio Ghibli inspired, soft colors, illustrated style",
        "positive": "studio ghibli style, anime art, soft colors, illustrated, high quality cel shading, whimsical atmosphere, hand-drawn look",
        "negative": "photography, realistic, 3d render, low quality, messy, noisy, dark, gritty",
        "sampler": "Euler a",
        "steps": 25
    }
    NOIR = {
        "name": "NOIR",
        "description": "Black and white, high contrast, dramatic shadows",
        "positive": "black and white, high contrast, dramatic shadows, film noir, gritty urban setting, moody lighting, 1940s aesthetic, sharp focus",
        "negative": "color, bright, sunny, cheerful, soft, low contrast, modern, futuristic",
        "sampler": "DPM++ SDE Karras",
        "steps": 35
    }
    WATERCOLOR = {
        "name": "WATERCOLOR",
        "description": "Soft, artistic, dreamy, painterly",
        "positive": "watercolor painting, soft artistic edges, dreamy, painterly style, paper texture, fluid brushstrokes, pastel palette, ethereal",
        "negative": "realistic, photography, sharp, hard edges, digital art, neon, high contrast, dark",
        "sampler": "Euler a",
        "steps": 20
    }
    MINIMALIST = {
        "name": "MINIMALIST",
        "description": "Simple shapes, limited palette, clean design",
        "positive": "minimalist design, simple shapes, limited palette, clean lines, flat design, modern aesthetic, spacious composition, sharp focus",
        "negative": "cluttered, detailed, busy, realistic, complex textures, messy, dark, gritty",
        "sampler": "DPM++ 2M Karras",
        "steps": 25
    }

    PRESETS = {
        "cinematic": CINEMATIC,
        "anime": ANIME,
        "noir": NOIR,
        "watercolor": WATERCOLOR,
        "minimalist": MINIMALIST
    }

    @classmethod
    def get_preset(cls, name: str) -> Dict:
        return cls.PRESETS.get(name.lower(), cls.CINEMATIC)

class MoodToVisualPrompt:
    """
    Converts episode moods and narratives into rich, SD-optimized visual prompts.
    """
    
    # Library of 14 mood mappings (10+ as requested)
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
        },
        "mysterious": {
            "elements": "deep purples, fog, hidden details, occult symbols, obscured face",
            "lighting": "dim moonlight, flickering candles",
            "atmosphere": "enigmatic, secretive, dark",
            "negative": "clear, bright, sunny, simple, obvious"
        },
        "determined": {
            "elements": "strong contrast, forward motion, clenched focus, urban grit, focused gaze",
            "lighting": "stark side lighting, hard shadows",
            "atmosphere": "resilient, gritty, intense",
            "negative": "soft, weak, lazy, blurry, peaceful"
        },
        "exhausted": {
            "elements": "desaturated tones, heavy lids, slumped posture, cluttered background, dying light",
            "lighting": "dim twilight, fading embers",
            "atmosphere": "weary, drained, heavy",
            "negative": "energetic, bright, fresh, active"
        },
        "joyful": {
            "elements": "bright yellows, laughter, colorful confetti, vibrant flowers, upward motion",
            "lighting": "brilliant sunlight, rainbow refraction",
            "atmosphere": "happy, lighthearted, exuberant",
            "negative": "sad, dark, muted, rain, shadows"
        }
    }

    QUALITY_BOOSTERS = "masterpiece, 8k, highly detailed, professional composition"

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

    def _detect_detailed_mood(self, text: str) -> str:
        """Use LLM to detect specific mood from the library."""
        moods = ", ".join(self.MOOD_LIBRARY.keys())
        prompt = f"""Analyze the following text and pick the most appropriate mood from this list: {moods}.
Only output the single word for the mood.

Text: {text}
Mood:"""
        
        result = _make_request(prompt, timeout=15)
        if result:
            detected = result.strip().lower().strip('.')
            if detected in self.MOOD_LIBRARY:
                return detected
        return "peaceful" # Default

    def generate_cover_prompt(self, episode: Entry, style_name: str = "cinematic") -> Tuple[str, str, Dict]:
        """
        Generate a positive and negative prompt for the episode's cover art based on a style preset.
        
        Args:
            episode: The Entry object containing narrative and other metadata.
            style_name: The name of the visual style preset to use.
            
        Returns:
            A tuple of (positive_prompt, negative_prompt, style_metadata).
        """
        text = episode.narrative_text or episode.raw_text
        if not text:
            return "", "", {}
            
        # 1. Detect mood
        mood = self._detect_detailed_mood(text)
        mood_data = self.MOOD_LIBRARY.get(mood, self.MOOD_LIBRARY["peaceful"])
        
        # 2. Extract visual moments from narrative
        visual_moments = self._extract_visual_moments(text)
        
        # 3. Get Style Preset
        preset = VisualStylePresets.get_preset(style_name)
        
        # 4. Compose SD-optimized positive prompt
        components = [
            f"A {mood} scene",
            visual_moments,
            mood_data["elements"],
            f"Lighting: {mood_data['lighting']}",
            f"Atmosphere: {mood_data['atmosphere']}",
            preset["positive"],
            self.QUALITY_BOOSTERS
        ]
        
        positive_prompt = ", ".join([c for c in components if c])
        
        # 5. Generate appropriate negative prompts
        negative_prompt = f"low quality, blurry, distorted, {mood_data['negative']}, {preset['negative']}"
        
        return positive_prompt, negative_prompt, preset

# Initialize a global instance
mood_to_visual = MoodToVisualPrompt()

