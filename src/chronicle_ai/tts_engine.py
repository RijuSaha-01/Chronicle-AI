"""
Chronicle AI - TTS Engine
Handles local text-to-speech generation for audiobook narration.
Supports Coqui XTTS v2 and Piper.
"""

import os
import logging
from pathlib import Path
from typing import Optional, List, Dict

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TTSEngine")

class TTSEngine:
    """
    Local TTS Engine supporting high-quality (XTTS v2) and high-speed (Piper) backends.
    """
    
    VOICES = {
        "storyteller": {
            "name": "Abrahan Mack",  # Warm storyteller style
            "description": "Warm, engaging narrative voice, perfect for daily chronicles.",
            "backend": "xtts"
        },
        "dramatic": {
            "name": "Baldur Valur",   # Dramatic, deep style
            "description": "Deep, resonant voice for high-tension moments.",
            "backend": "xtts"
        },
        "calm": {
            "name": "Asya Arafat",    # Calm, reflective style
            "description": "Soft and steady voice for peaceful reflections.",
            "backend": "xtts"
        },
        "piper_default": {
            "name": "en_US-lessac-medium",
            "description": "Fast, clear robotic/natural hybrid voice.",
            "backend": "piper"
        }
    }

    def __init__(self, output_dir: str = "exports/audio"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._xtts_model = None
        self._piper_model = None
        
        # Agreement to Coqui TOS (required for XTTS)
        os.environ["COQUI_TOS_AGREED"] = "1"

    def _get_xtts(self):
        """Lazy load Coqui TTS engine."""
        if self._xtts_model is None:
            try:
                from TTS.api import TTS
                logger.info("🚀 Loading Coqui XTTS v2 model... (This may take a moment)")
                self._xtts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
            except ImportError:
                logger.warning("⚠️ Coqui TTS not installed. Install with 'pip install TTS'")
                return None
            except Exception as e:
                logger.error(f"❌ Error loading XTTS: {e}")
                return None
        return self._xtts_model

    def generate(self, text: str, output_filename: str, voice_key: str = "storyteller") -> Optional[str]:
        """
        Generate audio from text.
        
        Args:
            text: The narrative text to convert.
            output_filename: Name of the output file (e.g., 'episode_01.wav').
            voice_key: Key from VOICES dictionary.
            
        Returns:
            Absolute path to the generated audio file, or None if failed.
        """
        voice_config = self.VOICES.get(voice_key, self.VOICES["storyteller"])
        output_path = self.output_dir / output_filename
        
        if voice_config["backend"] == "xtts":
            return self._generate_xtts(text, output_path, voice_config["name"])
        else:
            return self._generate_piper(text, output_path, voice_config["name"])

    def _generate_xtts(self, text: str, output_path: Path, speaker: str) -> Optional[str]:
        engine = self._get_xtts()
        if not engine:
            return None
            
        try:
            logger.info(f"🎙️ Narrating with XTTS (Speaker: {speaker})...")
            engine.tts_to_file(
                text=text,
                speaker=speaker,
                language="en",
                file_path=str(output_path)
            )
            return str(output_path.absolute())
        except Exception as e:
            logger.error(f"❌ XTTS Generation failed: {e}")
            return None

    def _generate_piper(self, text: str, output_path: Path, model_name: str) -> Optional[str]:
        # Simple placeholder for Piper integration (usually via subprocess or specific wrapper)
        logger.warning("⚠️ Piper backend integration is a placeholder. Please use XTTS or implement Piper wrapper.")
        return None

    def list_voices(self) -> Dict:
        """Return available voice presets."""
        return self.VOICES

# Singleton instance
tts_engine = TTSEngine()
