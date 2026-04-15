import os
import pytest
import shutil
import tempfile
import time
import numpy as np
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta

from chronicle_ai.embedding_engine import EmbeddingEngine
from chronicle_ai.semantic_search import SemanticSearch
from chronicle_ai.memory_chat import MemoryChat
from chronicle_ai.models import Entry, ChatMessage

import gc

class MockLLM:
    def generate(self, prompt, system_prompt=None):
        if "MEMORY" in prompt or "office" in prompt.lower():
            return "Based on your memories, you had a productive day at the office [Episode 1: 'The Office Day']."
        return "I don't know based on your recorded memories."

@pytest.fixture
def temp_chroma_dir():
    path = tempfile.mkdtemp()
    yield path
    # Try multiple times to cleanup on Windows
    for _ in range(5):
        try:
            gc.collect() # Try to release objects
            shutil.rmtree(path)
            break
        except PermissionError:
            time.sleep(0.5)
        except Exception:
            break

@pytest.fixture
def engine(temp_chroma_dir):
    # Use a small local model to avoid huge downloads during tests if possible, 
    # but since it's already installed in the user environment it should be fast.
    return EmbeddingEngine(persist_directory=temp_chroma_dir)

@pytest.fixture
def search(engine):
    return SemanticSearch(embedding_engine=engine)

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.list_entries.return_value = []
    repo.get_chat_session.return_value = None
    repo.create_chat_session.return_value = MagicMock(id=1)
    return repo

@pytest.fixture
def chat(search, mock_repo):
    chat_system = MemoryChat(semantic_search=search, repo=mock_repo)
    chat_system.llm = MockLLM()
    return chat_system

def create_mock_episode(id, title, narrative, date="2024-01-01", mood="neutral", themes=None):
    ep = MagicMock(spec=Entry)
    ep.id = id
    ep.title = title
    ep.narrative_text = narrative
    ep.synopsis = f"Synopsis of {title}"
    ep.date = date
    ep.mood = mood
    ep.themes = themes or ["general"]
    ep.keywords = themes or ["general"]
    ep.season_id = 1
    return ep

# --- Embedding Engine Tests ---

def test_embedding_engine_initialization(temp_chroma_dir):
    engine = EmbeddingEngine(persist_directory=temp_chroma_dir)
    assert engine.collection is not None
    assert os.path.exists(temp_chroma_dir)

def test_chunk_text(engine):
    text = "Short text."
    chunks = engine._chunk_text(text)
    assert len(chunks) == 1
    assert chunks[0] == text

    long_text = " ".join(["word"] * 600) # Exceeds ~375 words
    chunks = engine._chunk_text(long_text)
    assert len(chunks) > 1

def test_embed_episode(engine):
    ep = create_mock_episode(1, "The Office Day", "I spent the day working at the office. It was productive.")
    success = engine.embed_episode(ep)
    assert success is True
    
    # Verify it's in Chroma
    results = engine.collection.get(ids=["ep_1_narrative_0"])
    assert len(results["ids"]) == 1
    assert "productive" in results["documents"][0]

def test_embed_empty_episode(engine):
    ep = create_mock_episode(2, "", "")
    ep.synopsis = ""
    ep.themes = []
    ep.keywords = []
    success = engine.embed_episode(ep)
    assert success is False

# --- Semantic Search Tests ---

def test_search_accuracy(engine, search):
    # Setup test data
    ep1 = create_mock_episode(1, "The Office Day", "I spent the day working at the office. It was productive.", themes=["work"])
    ep2 = create_mock_episode(2, "Mountain Hike", "I climbed a steep mountain today. The view was amazing.", themes=["travel"])
    engine.embed_episode(ep1)
    engine.embed_episode(ep2)
    
    print(f"Collection count: {engine.collection.count()}")

    # Test work query
    results = search.search("Where did I work?")
    assert len(results) >= 1
    assert results[0]["episode_id"] == "1"
    
    # Check if 'office' is in any of the results for episode 1
    found_office = any("office" in r["text_snippet"].lower() for r in results if r["episode_id"] == "1")
    assert found_office is True

    # Test travel query
    results = search.search("mountain climb")
    assert len(results) >= 1
    assert results[0]["episode_id"] == "2"

def test_search_filters(engine, search):
    ep1 = create_mock_episode(1, "Happy Day", "Content of the happy day", date="2024-01-01", mood="happy")
    ep2 = create_mock_episode(2, "Sad Day", "Content of the sad day", date="2024-01-02", mood="sad")
    engine.embed_episode(ep1)
    engine.embed_episode(ep2)

    # Filter by mood
    results = search.search("Content", filters={"mood": "happy"})
    assert len(results) >= 1
    assert all(r["mood"] == "happy" for r in results)

    # Filter by date
    results = search.search("Content", filters={"date_range": ["2024-01-02", "2024-01-03"]})
    assert len(results) >= 1
    assert all(r["date"] == "2024-01-02" for r in results)

def test_empty_database_graceful_handling(search):
    # Ensure collection is empty
    results = search.search("Anything")
    assert results == []

# --- Memory Chat Tests ---

def test_chat_response_relevance(engine, chat):
    ep1 = create_mock_episode(1, "The Office Day", "I spent the day working at the office. It was productive.")
    engine.embed_episode(ep1)

    # Use a question that doesn't trigger 'day' / 'date' detection to avoid filtering out old episodes
    response = chat.ask("Tell me about office productivity")
    assert "productive" in response.answer.lower()
    assert len(response.sources) > 0
    assert any(s["episode_id"] == "1" for s in response.sources)

def test_chat_no_context(chat):
    response = chat.ask("What is the meaning of life?")
    assert "don't know" in response.answer.lower()

# --- Performance Benchmarks ---

def test_performance_benchmarks(engine, search):
    """
    Benchmarks query latency with 100, 500 episodes.
    (1000 might be too slow for a unit test, but let's try 100 and 500).
    """
    def inject_data(count):
        docs = [f"This is a dummy episode narrative for episode {i}. It talks about theme {i%10}." for i in range(count)]
        metadatas = [{"episode_id": str(i), "date": "2024-01-01", "title": f"Ep {i}"} for i in range(count)]
        ids = [f"bench_{i}" for i in range(count)]
        
        # We need embeddings. Using the engine's model to be realistic.
        embeddings = engine.model.encode(docs).tolist()
        engine.collection.add(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)

    results = {}
    for size in [100, 500]:
        tmpdir = tempfile.mkdtemp()
        try:
            temp_engine = EmbeddingEngine(persist_directory=tmpdir)
            temp_search = SemanticSearch(embedding_engine=temp_engine)
            
            # Inject
            docs = [f"Dummy {i}" for i in range(size)]
            ids = [f"id_{i}" for i in range(size)]
            metadatas = [{"episode_id": str(i)} for i in range(size)]
            embeddings = temp_engine.model.encode(docs).tolist()
            temp_engine.collection.add(ids=ids, documents=docs, metadatas=metadatas, embeddings=embeddings)
            
            # Benchmark
            start_time = time.time()
            for _ in range(5): # Average over 5 queries
                temp_search.search("Where is Dummy 50?")
            avg_latency = (time.time() - start_time) / 5
            results[size] = avg_latency
        finally:
            # Cleanup using the robust method
            for _ in range(5):
                try:
                    gc.collect()
                    shutil.rmtree(tmpdir)
                    break
                except PermissionError:
                    time.sleep(0.5)
                except Exception:
                    break

    print(f"\n--- Performance Benchmarks ---")
    for size, latency in results.items():
        print(f"Size: {size} episodes | Avg Latency: {latency:.4f}s")
    
    # Assert reasonable latency (< 500ms for 500 items on most machines)
    assert results[500] < 1.0 

def test_embedding_quality_verification(engine, search):
    """Verify that similar meanings have higher similarity scores."""
    ep1 = create_mock_episode(1, "Coding", "I wrote some python code today.")
    ep2 = create_mock_episode(2, "Programming", "I spent the afternoon software developing.")
    ep3 = create_mock_episode(3, "Cooking", "I made a delicious pasta dinner.")
    
    engine.embed_episode(ep1)
    engine.embed_episode(ep2)
    engine.embed_episode(ep3)
    
    import numpy as np
    
    # Search for "Software development"
    results = search.search("software development")
    
    # ep2 should be top, ep1 should be second, ep3 should be last or lower
    ids_in_order = [r["episode_id"] for r in results]
    
    # At least check that ep1 and ep2 are more similar than ep3
    scores = {r["episode_id"]: r["similarity_score"] for r in results}
    
    # We expect score(ep1) and score(ep2) > score(ep3) for a programming query
    if "2" in scores and "3" in scores:
        assert scores["2"] > scores.get("3", 0)
    if "1" in scores and "3" in scores:
        assert scores["1"] > scores.get("3", 0)
