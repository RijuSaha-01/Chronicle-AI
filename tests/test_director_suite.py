"""
Chronicle AI - Director Engine Test Suite
Tests for EpisodeStructure, ConflictDetector, RecapGenerator, and SeasonManager.
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chronicle_ai.models import Entry, ConflictAnalysis, Recap, Season
from chronicle_ai.director import EpisodeStructure, DirectorEngine
from chronicle_ai.conflict import ConflictDetector
from chronicle_ai.recap import RecapGenerator
from chronicle_ai.season_manager import SeasonManager

class TestEpisodeStructure:
    def test_validate_valid_narrative(self):
        validator = EpisodeStructure(min_length=20, min_sentences=2)
        narrative = "The sun rose over the quiet town. Every shadow stretched long and thin."
        result = validator.validate(narrative)
        assert result["valid"] is True
        assert not result["issues"]

    def test_validate_too_short(self):
        validator = EpisodeStructure(min_length=100)
        result = validator.validate("Too short.")
        assert result["valid"] is False
        assert any("too short" in issue.lower() for issue in result["issues"])

    def test_validate_repetition(self):
        validator = EpisodeStructure()
        narrative = "The sun rose. The sun rose. The sun rose."
        result = validator.validate(narrative)
        assert result["valid"] is False
        assert any("repetition" in issue.lower() for issue in result["issues"])

class TestConflictDetector:
    @patch("chronicle_ai.conflict._make_request")
    def test_analyze_entry(self, mock_request):
        mock_request.return_value = '{"internal": ["doubt"], "external": ["deadline"], "tension": 7, "archetype": "person vs time", "central_conflict": "Running out of time."}'
        detector = ConflictDetector()
        result = detector.analyze_entry("I am worried about my deadline.")
        
        assert isinstance(result, ConflictAnalysis)
        assert result.tension_level == 7
        assert "doubt" in result.internal_conflicts
        assert result.archetype == "person vs time"

class TestRecapGenerator:
    @patch("chronicle_ai.recap._make_request")
    def test_generate_recap(self, mock_request):
        mock_request.return_value = "Previously on Chronicle... Things happened."
        repo = MagicMock()
        generator = RecapGenerator(repo)
        
        entries = [
            Entry(id=1, date="2024-01-01", title="Day 1", narrative_text="Start"),
            Entry(id=2, date="2024-01-02", title="Day 2", narrative_text="Middle")
        ]
        
        recap = generator.generate_recap(entries)
        assert isinstance(recap, Recap)
        assert "Previously on Chronicle..." in recap.content
        assert 1 in recap.entry_ids
        assert 2 in recap.entry_ids

class TestSeasonManager:
    def test_organize_by_month(self):
        repo = MagicMock()
        manager = SeasonManager(repo)
        
        entries = [
            Entry(date="2024-01-05", raw_text="Jan 1"),
            Entry(date="2024-01-15", raw_text="Jan 2"),
            Entry(date="2024-02-05", raw_text="Feb 1")
        ]
        
        # We don't want to actually call the LLM for title generation here
        with patch.object(manager, "_enhance_season_metadata") as mock_enhance:
            manager._organize_by_month(entries)
            
            # Should call create_season twice (Jan and Feb)
            assert repo.create_season.call_count == 2
            
            # Check first call (Jan)
            args, _ = repo.create_season.call_args_list[0]
            season_jan = args[0]
            assert season_jan.start_date == "2024-01-05"
            assert season_jan.end_date == "2024-01-15"
            assert season_jan.episode_count == 2

class TestSynopsisGeneration:
    @patch("chronicle_ai.llm_client._make_request")
    def test_generate_synopsis(self, mock_request):
        from chronicle_ai.llm_client import generate_synopsis
        mock_request.return_value = '{"logline": "A secret meeting reveals a truth that changes everything for the team.", "synopsis": "The protagonist attends a mysterious late-night meeting. They discover a hidden agenda.", "keywords": ["secret", "truth", "team", "mystery", "revelation"]}'
        
        result = generate_synopsis("Some long narrative about a secret meeting.")
        
        assert result["logline"] == "A secret meeting reveals a truth that changes everything for the team."
        assert "hidden agenda" in result["synopsis"]
        assert len(result["keywords"]) == 5
        assert "secret" in result["keywords"]

    @patch("chronicle_ai.llm_client._make_request")
    def test_generate_synopsis_enforcement(self, mock_request):
        from chronicle_ai.llm_client import generate_synopsis
        # Logline with more than 15 words
        long_logline = "This is a very long logline that definitely has way more than fifteen words in it to test if the trimming logic works as expected."
        mock_request.return_value = f'{{"logline": "{long_logline}", "synopsis": "Short summary.", "keywords": ["a", "b", "c", "d", "e", "f", "g"]}}'
        
        result = generate_synopsis("Context")
        
        # Should be trimmed to 15 words
        logline_words = result["logline"].replace("...", "").split()
        assert len(logline_words) <= 15
        assert len(result["keywords"]) == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
