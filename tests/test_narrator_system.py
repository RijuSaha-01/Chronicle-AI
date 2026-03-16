
import os
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from chronicle_ai.models import VoiceProfile, Entry
from chronicle_ai.tts_client import NarratorTTS, get_tts_client
from chronicle_ai.audio_generator import AudioEpisodeGenerator
from chronicle_ai.audio_storage import AudioStorageManager

@pytest.fixture
def mock_tts_model():
    with patch('chronicle_ai.tts_client.TTS', create=True) as mock_tts:
        model_instance = MagicMock()
        mock_tts.return_value = model_instance
        yield model_instance

@pytest.fixture
def temp_audio_dir(tmp_path):
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    return audio_dir

class TestVoiceProfile:
    def test_voice_profile_init(self):
        profile = VoiceProfile(
            key="TEST",
            name="Test Voice",
            voice_model="model/path",
            speed=1.2,
            pitch=0.1,
            description="A test profile"
        )
        assert profile.key == "TEST"
        assert profile.name == "Test Voice"
        assert profile.speed == 1.2
        assert profile.pitch == 0.1
        assert "sentence" in profile.pause_durations

    def test_to_from_dict(self):
        original = VoiceProfile(key="TEST", name="Test", voice_model="model")
        data = original.to_dict()
        assert data["key"] == "TEST"
        
        reconstructed = VoiceProfile.from_dict(data)
        assert reconstructed.key == "TEST"
        assert reconstructed.name == "Test"

class TestNarratorTTS:
    def test_init_default(self):
        tts = NarratorTTS()
        assert tts.profile_key == "STORYTELLER"
        assert tts.engine_type == "coqui"

    def test_get_profile_for_mood(self):
        assert NarratorTTS.get_profile_for_mood("productive") == "STORYTELLER"
        assert NarratorTTS.get_profile_for_mood("stressful") == "DRAMATIC"
        assert NarratorTTS.get_profile_for_mood("reflective") == "CALM"
        assert NarratorTTS.get_profile_for_mood("mysterious") == "NOIR"
        assert NarratorTTS.get_profile_for_mood("unknown") == "STORYTELLER"

    def test_duration_estimate(self):
        tts = NarratorTTS(speed_override=1.0)
        # 10 words (now without the 'now.')
        text = "This is a simple test sentence with exactly ten words"
        estimate = tts.get_duration_estimate(text)
        assert estimate == 4.0

    @patch('chronicle_ai.tts_client.TTS_AVAILABLE', True)
    def test_synthesize_mocked(self, mock_tts_model, temp_audio_dir):
        tts = NarratorTTS()
        output_path = temp_audio_dir / "test.wav"
        
        # Mock the tts_to_file call
        mock_tts_model.tts_to_file.return_value = None
        
        result = tts.synthesize("Hello world", str(output_path))
        
        assert result == str(output_path.absolute())
        mock_tts_model.tts_to_file.assert_called_once()

    @patch('chronicle_ai.tts_client.TTS_AVAILABLE', False)
    def test_fallback_when_tts_unavailable(self):
        tts = NarratorTTS()
        assert tts.check_health() is False
        assert tts.synthesize("test", "test.wav") is None

class TestAudioEpisodeGenerator:
    @patch('chronicle_ai.audio_generator.PYDUB_AVAILABLE', True)
    @patch('chronicle_ai.audio_generator.MUTAGEN_AVAILABLE', True)
    def test_parse_sections(self):
        generator = AudioEpisodeGenerator()
        text = "### Act 1\nHello world.\n\n--- \n\nNext scene."
        sequence = generator._parse_sections(text)
        
        # Should have: Marker, Text, Pause (Para), Text, Pause (Scene), Text
        # Actually it's: Marker, Text, Pause (Scene), Text
        types = [item["type"] for item in sequence]
        assert "chapter_marker" in types
        assert "text" in types
        assert "pause" in types
        
        # Check if first chapter is correctly identified
        assert sequence[0]["type"] == "chapter_marker"
        assert sequence[0]["text"] == "Act 1"

    @patch('chronicle_ai.audio_generator.tts_engine')
    @patch('chronicle_ai.audio_generator.AudioSegment', create=True)
    @patch('chronicle_ai.audio_generator.PYDUB_AVAILABLE', True)
    def test_synthesize_and_combine(self, mock_audio_segment, mock_tts_engine):
        generator = AudioEpisodeGenerator()
        sequence = [
            {"type": "chapter_marker", "text": "Intro"},
            {"type": "text", "text": "Something"},
            {"type": "pause", "duration": 1.0}
        ]
        entry = Entry(id=1, mood="joyful")
        
        # Mock AudioSegment.empty() and addition
        mock_combined = MagicMock()
        mock_audio_segment.empty.return_value = mock_combined
        mock_audio_segment.silent.return_value = MagicMock()
        
        # Mock tts_engine.generate
        mock_tts_engine.generate.return_value = "fake.wav"
        
        # Mock segment creation from wav
        mock_segment = MagicMock()
        mock_segment.__len__.return_value = 1000 # 1 second
        mock_audio_segment.from_wav.return_value = mock_segment
        
        with patch('os.path.exists', return_value=True), patch('os.remove'):
            combined, duration, chapters = generator._synthesize_and_combine(sequence, entry)
        
        assert len(chapters) == 1
        assert chapters[0]["title"] == "Intro"
        assert duration > 0

class TestMetadataAndChapters:
    @patch('chronicle_ai.audio_storage.MUTAGEN_AVAILABLE', True)
    @patch('chronicle_ai.audio_storage.ID3', create=True)
    @patch('chronicle_ai.audio_storage.TIT2', create=True)
    @patch('chronicle_ai.audio_storage.TPE1', create=True)
    @patch('chronicle_ai.audio_storage.TALB', create=True)
    @patch('chronicle_ai.audio_storage.TRCK', create=True)
    @patch('chronicle_ai.audio_storage.APIC', create=True)
    @patch('chronicle_ai.audio_storage.MP3', create=True)
    def test_embed_metadata(self, mock_mp3, mock_apic, mock_trck, mock_talb, mock_tpe1, mock_tit2, mock_id3, tmp_path):
        storage = AudioStorageManager()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake mp3 content")
        
        entry = Entry(id=99, title="Great Story", audio_path=str(audio_file))
        
        mock_audio_instance = MagicMock()
        mock_mp3.return_value = mock_audio_instance
        
        storage.embed_metadata(entry)
        
        mock_audio_instance.save.assert_called()
        # Verify some tags were added
        assert mock_audio_instance.tags.add.called

    @patch('chronicle_ai.audio_storage.MUTAGEN_AVAILABLE', True)
    @patch('chronicle_ai.audio_storage.CTOC', create=True)
    @patch('chronicle_ai.audio_storage.CHAP', create=True)
    @patch('chronicle_ai.audio_storage.TIT2', create=True)
    @patch('chronicle_ai.audio_storage.MP3', create=True)
    def test_add_chapters(self, mock_mp3, mock_tit2, mock_chap, mock_ctoc, tmp_path):
        storage = AudioStorageManager()
        audio_file = tmp_path / "test.mp3"
        audio_file.write_text("fake mp3 content")
        
        chapters = [{"title": "Part 1", "start_ms": 0}, {"title": "Part 2", "start_ms": 5000}]
        
        mock_audio_instance = MagicMock()
        mock_mp3.return_value = mock_audio_instance
        
        storage.add_chapters(str(audio_file), chapters)
        
        # Check if .chapters file was created
        chapters_file = audio_file.with_suffix('.chapters')
        assert chapters_file.exists()
        assert "Part 1" in chapters_file.read_text()

@patch('chronicle_ai.audio_generator.AudioEpisodeGenerator.generate_audio')
def test_batch_processing(mock_gen_audio):
    # Mock repository
    with patch('chronicle_ai.audio_generator.get_repository') as mock_repo_get:
        mock_repo = MagicMock()
        mock_repo_get.return_value = mock_repo
        mock_repo.get_entry_by_id.return_value = Entry(id=1, title="Test")
        
        generator = AudioEpisodeGenerator()
        mock_gen_audio.return_value = "path/to/audio"
        
        report = generator.batch_generate_audio([1, 2, 3])
        
        assert report["total"] == 3
        assert report["generated"] == 3
        assert mock_gen_audio.call_count == 3
