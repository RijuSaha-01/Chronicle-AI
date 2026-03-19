"""
Chronicle AI - Embedding Engine

Generates and stores semantic embeddings for diary entries using local models.
"""

import os
import chromadb
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
from datetime import datetime
import json
import logging
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingEngine:
    """
    Engine for generating and storing embeddings for episodes.
    Uses sentence-transformers locally or Ollama's embedding endpoint, and ChromaDB for storage.
    """
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2", persist_directory: str = "data/chroma", use_ollama: bool = False):
        """
        Initialize the embedding engine.
        
        Args:
            model_name: The name of the sentence-transformers model to use (if use_ollama=False).
            persist_directory: Directory to persist ChromaDB data.
            use_ollama: If True, use Ollama's embedding endpoint instead of sentence-transformers.
        """
        self.model_name = model_name
        self.persist_directory = persist_directory
        self.use_ollama = use_ollama
        
        # Ensure directory exists
        if not os.path.exists(self.persist_directory):
            try:
                os.makedirs(self.persist_directory)
                logger.info(f"Created ChromaDB directory: {self.persist_directory}")
            except Exception as e:
                logger.error(f"Failed to create ChromaDB directory: {e}")
            
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(name="chronicle_episodes")
        
        # Load model locally if not using Ollama
        self.model = None
        if not self.use_ollama:
            try:
                logger.info(f"Loading local embedding model: {model_name}...")
                self.model = SentenceTransformer(model_name)
                logger.info("Local embedding model loaded.")
            except Exception as e:
                logger.error(f"Failed to load sentence-transformers model {model_name}: {e}")

    def _chunk_text(self, text: str, max_tokens: int = 500) -> List[str]:
        """
        Chunk long text into semantic paragraphs (max 500 tokens).
        
        Using an approximate word count as a proxy for tokens (1 token ≈ 0.75 words).
        """
        if not text:
            return []
        
        word_limit = int(max_tokens * 0.75)  # ~375 words
        
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for p in paragraphs:
            # If a single paragraph is too large, split it further by sentences
            if len(p.split()) > word_limit:
                # Add current if exists
                if current_chunk:
                    chunks.append(current_chunk)
                    current_chunk = ""
                
                # Split paragraph into sentences
                import re
                sentences = re.split(r'(?<=[.!?])\s+', p)
                
                temp_chunk = ""
                for s in sentences:
                    if len((temp_chunk + " " + s).split()) <= word_limit:
                        temp_chunk = (temp_chunk + " " + s).strip()
                    else:
                        if temp_chunk:
                            chunks.append(temp_chunk)
                        temp_chunk = s
                
                if temp_chunk:
                    current_chunk = temp_chunk
            else:
                # Normal paragraph handling
                if len((current_chunk + "\n\n" + p).strip().split()) <= word_limit:
                    if current_chunk:
                        current_chunk += "\n\n" + p
                    else:
                        current_chunk = p
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = p
        
        if current_chunk:
            chunks.append(current_chunk)
            
        return chunks

    def _get_ollama_embeddings(self, texts: List[str], ollama_model: str = "mxbai-embed-large") -> List[List[float]]:
        """Fetch embeddings from Ollama's endpoint."""
        embeddings = []
        for text in texts:
            try:
                response = httpx.post(
                    "http://localhost:11434/api/embeddings",
                    json={"model": ollama_model, "prompt": text},
                    timeout=30.0
                )
                response.raise_for_status()
                embeddings.append(response.json()["embedding"])
            except Exception as e:
                logger.error(f"Ollama embedding request failed: {e}")
                raise
        return embeddings

    def embed_episode(self, episode) -> bool:
        """
        Generates and stores embeddings for a single episode.
        
        Metadata includes: episode_id, section, timestamp, date, chunk_index.
        Fields embedded: narrative, synopsis, title, themes (keywords).
        """
        if not self.use_ollama and not self.model:
            logger.error("Embedding engine not initialized (model missing).")
            return False
            
        episode_id = str(episode.id)
        timestamp = datetime.now().isoformat()
        
        # Components to embed
        parts = {
            "narrative": episode.narrative_text,
            "synopsis": episode.synopsis,
            "title": episode.title,
            "themes": ", ".join(episode.keywords) if episode.keywords else ""
        }
        
        # Prepare storage lists
        documents = []
        metadatas = []
        ids = []
        
        for section, content in parts.items():
            if not content:
                continue
                
            chunks = self._chunk_text(content)
            for i, chunk in enumerate(chunks):
                documents.append(chunk)
                metadatas.append({
                    "episode_id": episode_id,
                    "section": section,
                    "timestamp": timestamp,
                    "date": episode.date,
                    "chunk_index": i
                })
                ids.append(f"ep_{episode_id}_{section}_{i}")
        
        if not documents:
            logger.info(f"No content to embed for Episode {episode_id}")
            return False
            
        try:
            # Generate embeddings
            if self.use_ollama:
                # Use mxbai-embed-large or similar if using Ollama
                embeddings = self._get_ollama_embeddings(documents)
            else:
                embeddings = self.model.encode(documents).tolist()
            
            # Store in ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Successfully embedded Episode {episode_id} ({len(documents)} chunks).")
            return True
        except Exception as e:
            logger.error(f"Failed to store embeddings for Episode {episode_id}: {e}")
            return False

    def batch_process_all(self, repository) -> int:
        """Processes all existing episodes in the repository."""
        episodes = repository.list_entries()
        logger.info(f"Starting batch embedding for {len(episodes)} episodes...")
        
        count = 0
        for episode in episodes:
            if self.embed_episode(episode):
                count += 1
        
        logger.info(f"Batch embedding complete: {count}/{len(episodes)} episodes processed.")
        return count

# Default instance helper
def get_embedding_engine(model_name: str = "all-MiniLM-L6-v2", use_ollama: bool = False):
    return EmbeddingEngine(model_name=model_name, use_ollama=use_ollama)
