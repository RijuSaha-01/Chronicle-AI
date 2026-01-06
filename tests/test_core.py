"""
Chronicle AI - Basic Tests

Test suite for core functionality.
"""

import pytest
import os
import tempfile
from datetime import date

# Add src to path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from chronicle_ai.models import Entry
from chronicle_ai.repository import EntryRepository


class TestEntry:
    """Tests for the Entry model."""
    
    def test_entry_creation(self):
        """Test basic entry creation."""
        entry = Entry(
            date="2024-01-15",
            raw_text="Test entry content"
        )
        assert entry.date == "2024-01-15"
        assert entry.raw_text == "Test entry content"
        assert entry.narrative_text is None
        assert entry.title is None
        assert entry.id is None
    
    def test_entry_to_dict(self):
        """Test entry serialization."""
        entry = Entry(
            id=1,
            date="2024-01-15",
            raw_text="Test",
            narrative_text="Narrative",
            title="Title"
        )
        data = entry.to_dict()
        assert data["id"] == 1
        assert data["date"] == "2024-01-15"
        assert data["raw_text"] == "Test"
        assert data["narrative_text"] == "Narrative"
        assert data["title"] == "Title"
    
    def test_entry_from_dict(self):
        """Test entry deserialization."""
        data = {
            "id": 1,
            "date": "2024-01-15",
            "raw_text": "Test",
            "narrative_text": "Narrative",
            "title": "Title"
        }
        entry = Entry.from_dict(data)
        assert entry.id == 1
        assert entry.date == "2024-01-15"
        assert entry.raw_text == "Test"
    
    def test_entry_snippet(self):
        """Test snippet generation."""
        entry = Entry(raw_text="A" * 200)
        snippet = entry.snippet(50)
        assert len(snippet) == 50
        assert snippet.endswith("...")
    
    def test_display_title_with_title(self):
        """Test display title when title is set."""
        entry = Entry(title="My Title", date="2024-01-15")
        assert entry.display_title() == "My Title"
    
    def test_display_title_without_title(self):
        """Test display title fallback."""
        entry = Entry(date="2024-01-15")
        assert entry.display_title() == "Entry from 2024-01-15"


class TestRepository:
    """Tests for the EntryRepository."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        fd, path = tempfile.mkstemp(suffix=".db")
        os.close(fd)
        yield path
        os.unlink(path)
    
    def test_create_entry(self, temp_db):
        """Test creating an entry."""
        repo = EntryRepository(temp_db)
        entry = Entry(
            date="2024-01-15",
            raw_text="Test content"
        )
        result = repo.create_entry(entry)
        
        assert result.id is not None
        assert result.id > 0
    
    def test_get_entry_by_id(self, temp_db):
        """Test retrieving an entry by ID."""
        repo = EntryRepository(temp_db)
        entry = Entry(date="2024-01-15", raw_text="Test")
        created = repo.create_entry(entry)
        
        retrieved = repo.get_entry_by_id(created.id)
        
        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.raw_text == "Test"
    
    def test_get_nonexistent_entry(self, temp_db):
        """Test retrieving a non-existent entry."""
        repo = EntryRepository(temp_db)
        result = repo.get_entry_by_id(9999)
        assert result is None
    
    def test_list_entries(self, temp_db):
        """Test listing entries."""
        repo = EntryRepository(temp_db)
        
        for i in range(5):
            repo.create_entry(Entry(date=f"2024-01-{15+i:02d}", raw_text=f"Entry {i}"))
        
        entries = repo.list_entries()
        assert len(entries) == 5
    
    def test_list_entries_with_limit(self, temp_db):
        """Test listing entries with limit."""
        repo = EntryRepository(temp_db)
        
        for i in range(10):
            repo.create_entry(Entry(date=f"2024-01-{i+1:02d}", raw_text=f"Entry {i}"))
        
        entries = repo.list_entries(limit=5)
        assert len(entries) == 5
    
    def test_list_entries_between_dates(self, temp_db):
        """Test date range filtering."""
        repo = EntryRepository(temp_db)
        
        repo.create_entry(Entry(date="2024-01-10", raw_text="Before"))
        repo.create_entry(Entry(date="2024-01-15", raw_text="In range"))
        repo.create_entry(Entry(date="2024-01-20", raw_text="After"))
        
        entries = repo.list_entries_between_dates("2024-01-14", "2024-01-16")
        
        assert len(entries) == 1
        assert entries[0].raw_text == "In range"
    
    def test_update_entry(self, temp_db):
        """Test updating an entry."""
        repo = EntryRepository(temp_db)
        entry = Entry(date="2024-01-15", raw_text="Original")
        created = repo.create_entry(entry)
        
        created.raw_text = "Updated"
        created.narrative_text = "New narrative"
        repo.update_entry(created)
        
        retrieved = repo.get_entry_by_id(created.id)
        assert retrieved.raw_text == "Updated"
        assert retrieved.narrative_text == "New narrative"
    
    def test_delete_entry(self, temp_db):
        """Test deleting an entry."""
        repo = EntryRepository(temp_db)
        entry = Entry(date="2024-01-15", raw_text="To delete")
        created = repo.create_entry(entry)
        
        deleted = repo.delete_entry(created.id)
        
        assert deleted is True
        assert repo.get_entry_by_id(created.id) is None
    
    def test_delete_nonexistent_entry(self, temp_db):
        """Test deleting a non-existent entry."""
        repo = EntryRepository(temp_db)
        deleted = repo.delete_entry(9999)
        assert deleted is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
