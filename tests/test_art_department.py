
import pytest
import os
import json
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from datetime import datetime

# Add src to path
import sys
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from chronicle_ai.models import Entry, Season
from chronicle_ai.repository import EntryRepository
from chronicle_ai.visual_prompts import MoodToVisualPrompt, VisualStylePresets, VisualIdentity
from chronicle_ai.image_client import ImageGenerator
from chronicle_ai.cover_gen import EpisodeCoverGenerator
from chronicle_ai.storage import ImageStorageManager

class TestArtDepartmentUnit:
    """Unit tests for the Art Department components."""

    def test_visual_style_presets(self):
        """Test VisualStylePresets retrieval."""
        preset = VisualStylePresets.get_preset("anime")
        assert preset["name"] == "ANIME"
        assert "studio ghibli" in preset["positive"]
        
        # Test case insensitivity
        preset = VisualStylePresets.get_preset("CINEMATIC")
        assert preset["name"] == "CINEMATIC"
        
        # Test fallback
        preset = VisualStylePresets.get_preset("nonexistent")
        assert preset["name"] == "CINEMATIC"

    @patch("chronicle_ai.visual_prompts._make_request")
    def test_mood_detection(self, mock_make_request):
        """Test mood detection logic."""
        converter = MoodToVisualPrompt()
        
        # Mock LLM return value
        mock_make_request.return_value = "Triumphant"
        
        mood = converter._detect_detailed_mood("I finally finished the project and feel great!")
        assert mood == "triumphant"
        mock_make_request.assert_called_once()

    @patch("chronicle_ai.visual_prompts._make_request")
    def test_generate_cover_prompt(self, mock_make_request):
        """Test full prompt generation for an episode."""
        converter = MoodToVisualPrompt()
        episode = Entry(id=1, season_id=1, narrative_text="A lonely walk in the rain.")
        
        # Mock LLM for mood and visual moments
        mock_make_request.side_effect = ["lonely", "person walking, umbrella, raindrops"]
        
        pos, neg, preset = converter.generate_cover_prompt(episode, style_name="noir")
        
        assert "lonely" in pos.lower()
        assert "noir" in pos.lower()
        assert "person walking" in pos
        assert "low quality" in neg
        assert preset["name"] == "NOIR"
        assert preset["seed"] == 100001 # 1 * 100000 + 1

    def test_visual_identity(self):
        """Test VisualIdentity application."""
        prompt = "test prompt"
        result = VisualIdentity.apply_identity(prompt, season_number=2, episode_id=5)
        
        assert "test prompt" in result
        assert "warm tones" in result # Season 2 palette
        assert "consistent character features" in result
        assert VisualIdentity.SIGNATURE_MOTIFS[5 % len(VisualIdentity.SIGNATURE_MOTIFS)] in result

class TestArtDepartmentIntegration:
    """Integration tests for the image generation pipeline."""

    @pytest.fixture
    def mock_env(self):
        """Setup a mock environment with temp DB and storage."""
        temp_dir = tempfile.mkdtemp()
        db_path = os.path.join(temp_dir, "test.db")
        data_dir = os.path.join(temp_dir, "data")
        
        repo = EntryRepository(db_path)
        storage = ImageStorageManager(base_data_dir=data_dir)
        
        yield {
            "root": temp_dir,
            "db_path": db_path,
            "data_dir": data_dir,
            "repo": repo,
            "storage": storage
        }
        
        shutil.rmtree(temp_dir)

    @patch("chronicle_ai.visual_prompts._make_request")
    @patch("chronicle_ai.image_client.ImageGenerator.check_health")
    @patch("chronicle_ai.image_client.ImageGenerator.generate")
    def test_full_cover_generation_pipeline(self, mock_gen, mock_health, mock_llm, mock_env):
        """Test the complete flow from entry to saved images and thumbnails."""
        repo = mock_env["repo"]
        storage = mock_env["storage"]
        
        # 1. Create a test entry
        entry = repo.create_entry(Entry(
            date="2024-02-17",
            narrative_text="A peaceful morning in the forest.",
            season_id=1
        ))
        
        # 2. Setup mocks
        mock_health.return_value = True
        # Create a tiny 1x1 black PNG as mock bytes
        mock_image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00:~\x9bU\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n2\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        mock_gen.return_value = mock_image_bytes
        mock_llm.side_effect = ["peaceful", "trees, sunlight"]
        
        # 3. Initialize generator with mocks
        image_gen = ImageGenerator(base_url="http://mock")
        # Monkey patch repository and storage into the generator or its dependencies
        with patch("chronicle_ai.cover_gen.get_repository", return_value=repo), \
             patch("chronicle_ai.cover_gen.storage_manager", storage), \
             patch("chronicle_ai.storage.get_repository", return_value=repo):
            
            generator = EpisodeCoverGenerator(image_gen=image_gen, base_data_dir=mock_env["data_dir"])
            paths = generator.generate_cover(entry.id, style_name="cinematic")
            
            # 4. Verify results
            assert len(paths) > 0
            main_path = Path(paths[0])
            assert main_path.exists()
            assert main_path.suffix == ".webp"
            
            # Verify DB links
            updated_entry = repo.get_entry_by_id(entry.id)
            assert updated_entry.cover_art_path == str(main_path)
            assert not updated_entry.is_placeholder
            
            # Verify all thumbnail sizes
            assert "medium" in updated_entry.image_variants
            assert "small" in updated_entry.image_variants
            assert "poster" in updated_entry.image_variants
            
            assert Path(updated_entry.image_variants["medium"]).exists()
            assert Path(updated_entry.image_variants["small"]).exists()
            assert Path(updated_entry.image_variants["poster"]).exists()
            
            # Verify storage organization
            # Expected: data/images/2024/1/{entry_id}/cover.webp
            expected_dir = Path(mock_env["data_dir"]) / "images" / "2024" / "1" / str(entry.id)
            assert main_path.parent == expected_dir
            assert (expected_dir / "metadata.json").exists()

    @patch("chronicle_ai.visual_prompts._make_request")
    @patch("chronicle_ai.image_client.ImageGenerator.check_health")
    def test_fallback_system(self, mock_health, mock_llm, mock_env):
        """Test fallback to gradient when SD is unavailable."""
        repo = mock_env["repo"]
        storage = mock_env["storage"]
        
        entry = repo.create_entry(Entry(date="2024-02-17", narrative_text="Stressful day."))
        
        mock_health.return_value = False
        mock_llm.return_value = "anxious"
        
        with patch("chronicle_ai.cover_gen.get_repository", return_value=repo), \
             patch("chronicle_ai.cover_gen.storage_manager", storage), \
             patch("chronicle_ai.storage.get_repository", return_value=repo):
            
            generator = EpisodeCoverGenerator(base_data_dir=mock_env["data_dir"])
            paths = generator.generate_cover(entry.id)
            
            updated_entry = repo.get_entry_by_id(entry.id)
            assert updated_entry.is_placeholder
            assert updated_entry.needs_image_retry
            assert Path(paths[0]).exists()
            
            # Check metadata
            meta_path = Path(paths[0]).parent / "metadata.json"
            with open(meta_path, 'r') as f:
                meta = json.load(f)
                assert meta["is_placeholder"] is True

    @patch("chronicle_ai.visual_prompts._make_request")
    @patch("chronicle_ai.image_client.ImageGenerator.check_health")
    @patch("chronicle_ai.image_client.ImageGenerator.generate")
    def test_regeneration_and_history(self, mock_gen, mock_health, mock_llm, mock_env):
        """Test cover regeneration and history preservation."""
        repo = mock_env["repo"]
        storage = mock_env["storage"]
        
        entry = repo.create_entry(Entry(date="2024-02-17", narrative_text="History test."))
        
        mock_health.return_value = True
        mock_image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x00\x00\x00\x00:~\x9bU\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n2\xb4\x00\x00\x00\x00IEND\xaeB`\x82'
        mock_gen.return_value = mock_image_bytes
        mock_llm.return_value = "joyful"
        
        with patch("chronicle_ai.cover_gen.get_repository", return_value=repo), \
             patch("chronicle_ai.cover_gen.storage_manager", storage), \
             patch("chronicle_ai.storage.get_repository", return_value=repo):
            
            generator = EpisodeCoverGenerator(base_data_dir=mock_env["data_dir"])
            
            # 1st generation
            generator.generate_cover(entry.id)
            first_path = repo.get_entry_by_id(entry.id).cover_art_path
            
            # 2nd generation (regenerate=True)
            generator.generate_cover(entry.id, regenerate=True)
            second_path = repo.get_entry_by_id(entry.id).cover_art_path
            
            # Verify history
            updated_entry = repo.get_entry_by_id(entry.id)
            assert len(updated_entry.cover_history) == 1
            assert updated_entry.cover_history[0]["path"] == first_path
            assert updated_entry.cover_art_path == second_path
            assert first_path != second_path

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
