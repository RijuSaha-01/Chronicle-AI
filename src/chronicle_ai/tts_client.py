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
from .models import VoiceProfile

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
    streaming interfaces using customizable VoiceProfiles.
    """

    DEFAULT_PROFILES = {
        "STORYTELLER": VoiceProfile(
            key="STORYTELLER",
            name="Abrahan Mack",
            voice_model="tts_models/multilingual/multi-dataset/xtts_v2",
            speed=1.0,
            pitch=0.0,
            pause_durations={"sentence": 0.5, "paragraph": 1.2},
            description="Warm, engaging, audiobook style"
        ),
        "DRAMATIC": VoiceProfile(
            key="DRAMATIC",
            name="Baldur Valur",
            voice_model="tts_models/multilingual/multi-dataset/xtts_v2",
            speed=0.9,
            pitch=-0.1,
            pause_durations={"sentence": 0.8, "paragraph": 1.5},
            description="Intense, theatrical, for high-tension episodes"
        ),
        "CALM": VoiceProfile(
            key="CALM",
            name="Asya Arafat",
            voice_model="tts_models/multilingual/multi-dataset/xtts_v2",
            speed=0.85,
            pitch=0.1,
            pause_durations={"sentence": 1.0, "paragraph": 2.0},
            description="Soothing, documentary style, for reflective episodes"
        ),
        "NOIR": VoiceProfile(
            key="NOIR",
            name="Baldur Valur",  # Reusing for now, but with deeper pitch if supported
            voice_model="tts_models/multilingual/multi-dataset/xtts_v2",
            speed=0.95,
            pitch=-0.2,
            pause_durations={"sentence": 0.7, "paragraph": 1.4},
            description="Deep, mysterious, for darker moods"
        )
    }

    MOOD_TO_VOICE = {
        "productive": "STORYTELLER",
        "reflective": "CALM",
        "stressful": "DRAMATIC",
        "relaxed": "CALM",
        "mysterious": "NOIR",
        "adventurous": "STORYTELLER",
        "melancholic": "CALM",
        "tense": "DRAMATIC",
        "joyful": "STORYTELLER",
        "gloomy": "NOIR"
    }

    def __init__(self, engine: str = 'coqui', voice_profile: Optional[str] = None, speed_override: Optional[float] = None):
        """
        Initialize the NarratorTTS client.

        Args:
            engine: The TTS engine to use ('coqui' or future 'piper')
            voice_profile: The profile key (e.g., 'STORYTELLER'). Defaults to STORYTELLER.
            speed_override: Optional speed multiplier to override the profile setting.
        """
        self.engine_type = engine.lower()
        self.profile_key = voice_profile or "STORYTELLER"
        
        # Load profile
        self.profile = self.DEFAULT_PROFILES.get(self.profile_key, self.DEFAULT_PROFILES["STORYTELLER"])
        self.speed = speed_override or self.profile.speed
        
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
        Synthesize text to an audio file using the current voice profile.

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
            speaker = self.profile.name
            
            # Ensure output directory exists
            out_path = Path(output_path)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"🎙️ Narrating ({self.profile_key}): {text[:50]}...")
            
            # Note: XTTS v2 tts_to_file takes speed. 
            # Pitch and pause_durations are stored in profile but may need 
            # post-processing or text manipulation to be fully realized.
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
            speaker = self.profile.name
            
            logger.info(f"💾 Streaming narration for ({self.profile_key}): {text[:30]}...")
            
            if hasattr(model, 'tts_stream'):
                for chunk in model.tts_stream(text, speaker, language="en", speed=self.speed):
                    yield chunk
            else:
                logger.warning("Stream API not found. Falling back to buffered synthesis.")
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

    def list_voices(self) -> List[Dict[str, Any]]:
        """
        Return available narrative voice profiles.
        """
        return [profile.to_dict() for profile in self.DEFAULT_PROFILES.values()]

    def preview_voice(self, profile_key: str, sample_text: str = "Welcome to your story. This is a preview of the narration style.") -> Optional[str]:
        """
        Generate a short audio sample for a specific voice profile.

        Args:
            profile_key: The profile key to preview
            sample_text: Short text snippet

        Returns:
            Path to preview audio file
        """
        if profile_key not in self.DEFAULT_PROFILES:
            logger.error(f"Profile '{profile_key}' not found.")
            return None
            
        old_profile = self.profile
        old_key = self.profile_key
        
        self.profile = self.DEFAULT_PROFILES[profile_key]
        self.profile_key = profile_key
        
        preview_dir = Path("exports/previews")
        preview_dir.mkdir(parents=True, exist_ok=True)
        preview_path = preview_dir / f"preview_{profile_key}.wav"
        
        result = self.synthesize(sample_text, str(preview_path))
        
        self.profile = old_profile
        self.profile_key = old_key
        return result

    @classmethod
    def get_profile_for_mood(cls, mood: Optional[str]) -> str:
        """
        Auto-select a voice profile based on episode mood.
        """
        if not mood:
            return "STORYTELLER"
        return cls.MOOD_TO_VOICE.get(mood.lower(), "STORYTELLER")

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

def get_tts_client(engine='coqui', voice_profile='STORYTELLER', speed=None):
    """Utility function to get a configured TTS client."""
    return NarratorTTS(engine=engine, voice_profile=voice_profile, speed_override=speed)
