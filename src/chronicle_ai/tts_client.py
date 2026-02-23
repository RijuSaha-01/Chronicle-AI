"""
Chronicle AI - TTS Client

Abstraction layer for Text-to-Speech operations, providing a consistent 
interface for narrative generation matching LLM and Image clients.
"""

import logging
import os
import time
from typing import Optional, List, Dict, Any, Generator
from pathlib import Path

# Try to import TTS if available
try:
    from TTS.api import TTS
    TTS_AVAILABLE = True
except ImportError:
    TTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class NarratorTTS:
    """
    NarratorTTS handles high-level TTS operations for the Chronicle project.
    It provides an abstraction over local engines (like Coqui XTTS) and
    streaming interfaces.
    """

    VOICES = {
        "default": {
            "name": "Abrahan Mack",
            "description": "Warm, engaging narrative voice, perfect for daily chronicles.",
            "engine": "coqui"
        },
        "storyteller": {
            "name": "Abrahan Mack",
            "description": "Warm, engaging narrative voice, perfect for daily chronicles.",
            "engine": "coqui"
        },
        "dramatic": {
            "name": "Baldur Valur",
            "description": "Deep, resonant voice for high-tension moments.",
            "engine": "coqui"
        },
        "calm": {
            "name": "Asya Arafat",
            "description": "Soft and steady voice for peaceful reflections.",
            "engine": "coqui"
        }
    }

    def __init__(self, engine: str = 'coqui', voice: str = 'default', speed: float = 1.0):
        """
        Initialize the NarratorTTS client.

        Args:
            engine: The TTS engine to use ('coqui' or future 'piper')
            voice: The voice model name or key from VOICES
            speed: Generation speed multiplier (1.0 is normal)
        """
        self.engine_type = engine.lower()
        self.voice_key = voice if voice in self.VOICES else "default"
        self.speed = speed
        self._model = None
        
        # Agreement to Coqui TOS (required for XTTS)
        os.environ["COQUI_TOS_AGREED"] = "1"

    def _get_model(self):
        """Lazy load the TTS model to save memory when not in use."""
        if self._model is None:
            if not TTS_AVAILABLE:
                logger.error("TTS package not installed. Cannot use Coqui engine.")
                return None
            
            try:
                if self.engine_type == 'coqui':
                    logger.info("🚀 Initializing Coqui XTTS v2 model... (First run may take a moment)")
                    # XTTS v2 is the current high-quality standard for Coqui
                    self._model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
                else:
                    logger.warning(f"Engine '{self.engine_type}' is currently in development. Falling back to Coqui.")
                    self._model = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)
            except Exception as e:
                logger.error(f"❌ Failed to load TTS model: {e}")
                return None
        return self._model

    def synthesize(self, text: str, output_path: str) -> Optional[str]:
        """
        Synthesize text to an audio file.

        Args:
            text: The narrative text to convert
            output_path: Destination path for the .wav or .mp3 file

        Returns:
            Absolute path to the generated audio file or None if failed
        """
        model = self._get_model()
        if not model:
            return None

        try:
            voice_config = self.VOICES.get(self.voice_key, self.VOICES["default"])
            speaker = voice_config["name"]
            
            # Ensure output directory exists
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🎙️ Narrating ({self.voice_key}): {text[:50]}...")
            
            # Use speed if supported by the version, otherwise standard tts
            # Note: XTTS v2 tts_to_file usually takes speed as an argument
            model.tts_to_file(
                text=text,
                speaker=speaker,
                language="en",
                file_path=str(out_path),
                speed=self.speed
            )
            
            return str(out_path.absolute())
        except Exception as e:
            logger.error(f"❌ Synthesis failed: {e}")
            return None

    def stream_synthesize(self, text: str) -> Generator[bytes, None, None]:
        """
        Synthesize text and return an audio stream for real-time playback.
        
        Returns:
            A generator yielding audio byte chunks
        """
        model = self._get_model()
        if not model:
            yield b""
            return

        try:
            voice_config = self.VOICES.get(self.voice_key, self.VOICES["default"])
            speaker = voice_config["name"]
            
            logger.info(f"💾 Streaming narration for: {text[:30]}...")
            
            # Mock streaming for now if tts_stream is not directly available in standard API
            # In production this would use model.tts_stream or similar
            if hasattr(model, 'tts_stream'):
                for chunk in model.tts_stream(text, speaker, language="en", speed=self.speed):
                    yield chunk
            else:
                logger.warning("Stream API not found in this TTS version. Falling back to buffered synthesis.")
                # Fallback: synthesize to temp file and stream that
                temp_path = f"tmp/stream_{int(time.time())}.wav"
                result_path = self.synthesize(text, temp_path)
                if result_path and os.path.exists(result_path):
                    with open(result_path, "rb") as f:
                        while chunk := f.read(4096):
                            yield chunk
                    os.remove(result_path)
        except Exception as e:
            logger.error(f"❌ Streaming failed: {e}")
            yield b""

    def list_voices(self) -> List[Dict[str, str]]:
        """
        Return available narrative voices with descriptions.
        """
        return [
            {
                "id": key, 
                "name": val["name"], 
                "description": val["description"],
                "engine": val["engine"]
            }
            for key, val in self.VOICES.items()
        ]

    def preview_voice(self, voice_name: str, sample_text: str = "Welcome to your story. This is a preview of the narration style.") -> Optional[str]:
        """
        Generate a short audio sample for a specific voice.

        Args:
            voice_name: The voice key to preview
            sample_text: Short text snippet

        Returns:
            Path to preview audio file
        """
        if voice_name not in self.VOICES:
            logger.error(f"Voice '{voice_name}' not found.")
            return None
            
        old_voice = self.voice_key
        self.voice_key = voice_name
        
        preview_dir = Path("exports/previews")
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_path = preview_dir / f"preview_{voice_name}.wav"
        
        result = self.synthesize(sample_text, str(preview_path))
        self.voice_key = old_voice
        return result

    def get_duration_estimate(self, text: str) -> float:
        """
        Estimate audio duration in seconds.
        Normal speaking rate: ~150 words per minute.
        """
        words = text.split()
        # ~2.5 words per second
        base_duration = len(words) / 2.5
        return base_duration / self.speed

    def check_health(self) -> bool:
        """
        Verify if the TTS engine and dependencies are working.
        """
        if not TTS_AVAILABLE:
            logger.error("TTS package (coqui-tts) is not installed.")
            return False
        
        try:
            # Check if we can at least find the model manager
            from TTS.utils.manage import ModelManager
            return True
        except Exception:
            return False

def get_tts_client(engine='coqui', voice='default', speed=1.0):
    """Utility function to get a configured TTS client."""
    return NarratorTTS(engine=engine, voice=voice, speed=speed)
