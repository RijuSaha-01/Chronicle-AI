"""
Chronicle AI - Semantic Search

Search engine for finding relevant diary chunks using vector embeddings.
"""

import logging
from typing import List, Dict, Any, Optional
import json
import re
from .embedding_engine import get_embedding_engine

logger = logging.getLogger(__name__)

class SemanticSearch:
    """
    Search engine for semantic retrieval of episodes and chunks.
    """
    
    def __init__(self, embedding_engine=None):
        """
        Initialize the search engine.
        
        Args:
            embedding_engine: An instance of EmbeddingEngine. If None, one will be created.
        """
        self.engine = embedding_engine or get_embedding_engine()
        self.collection = self.engine.collection

    def _highlight_concepts(self, text: str, query: str) -> str:
        """Highlights matching words from the query in the text."""
        # Simple highlighting: find words from query in text
        words = re.findall(r'\w+', query.lower())
        highlighted = text
        for word in set(words):
            if len(word) < 3: continue  # Skip short words
            
            # Use regex for case-insensitive replacement with formatting
            # This is naive but works for demonstration
            pattern = re.compile(re.escape(word), re.IGNORECASE)
            highlighted = pattern.sub(lambda m: f"**{m.group(0)}**", highlighted)
            
        return highlighted

    def search(self, query: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Search for relevant chunks based on a natural language query.
        
        Args:
            query: The search string.
            limit: Maximum number of results to return.
            filters: Dictionary of filters (date_range: [start, end], season, mood, themes).
            
        Returns:
            List of dicts containing episode_id, section, text_snippet, similarity_score, metadata.
        """
        where = {}
        
        # Build ChromaDB 'where' filter
        if filters:
            conditions = []
            
            # Date range filter
            if "date_range" in filters:
                start, end = filters["date_range"]
                if start:
                    conditions.append({"date": {"$gte": start}})
                if end:
                    conditions.append({"date": {"$lte": end}})
            
            # Season filter
            if "season" in filters and filters["season"] is not None:
                conditions.append({"season_id": int(filters["season"])})
                
            # Mood filter
            if "mood" in filters and filters["mood"]:
                conditions.append({"mood": filters["mood"]})
                
            # Themes filter (ChromaDB supports $contains for strings in metadata)
            if "themes" in filters and filters["themes"]:
                theme_val = filters["themes"]
                if isinstance(theme_val, list):
                    for t in theme_val:
                        conditions.append({"themes": {"$contains": t}})
                else:
                    conditions.append({"themes": {"$contains": theme_val}})

            if len(conditions) > 1:
                where["$and"] = conditions
            elif len(conditions) == 1:
                where = conditions[0]

        # Generate query embedding
        try:
            if self.engine.use_ollama:
                query_embedding = self.engine._get_ollama_embeddings([query])[0]
            else:
                query_embedding = self.engine.model.encode([query])[0].tolist()
        except Exception as e:
            logger.error(f"Failed to generate embedding for query: {e}")
            return []

        # Query ChromaDB
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=limit,
                where=where if where else None,
                include=["documents", "metadatas", "distances"]
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []

        formatted_results = []
        
        if not results or not results["ids"] or not results["ids"][0]:
            return []

        for i in range(len(results["ids"][0])):
            doc = results["documents"][0][i]
            meta = results["metadatas"][0][i]
            dist = results["distances"][0][i]
            
            # Calculate similarity score (cosine distance is normalized for MiniLM)
            # score = 1.0 - dist if distance is normalized (0 to 2 for cosine, but Chroma varies)
            # Actually Chroma's default distance for many models is squared L2.
            # Let's just provide a relative score where smaller distance is better.
            similarity_score = 1.0 / (1.0 + dist)
            
            formatted_results.append({
                "episode_id": meta.get("episode_id"),
                "section": meta.get("section"),
                "text_snippet": doc,
                "highlighted_text": self._highlight_concepts(doc, query),
                "similarity_score": round(similarity_score, 4),
                "date": meta.get("date"),
                "title": meta.get("title", "Untitled Episode"),
                "mood": meta.get("mood"),
                "metadata": meta
            })

        # Rank by score (already ranked by Chroma, but we can re-sort to be sure)
        formatted_results.sort(key=lambda x: x["similarity_score"], reverse=True)
            
        return formatted_results

def get_semantic_search():
    return SemanticSearch()
