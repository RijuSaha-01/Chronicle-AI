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

    def _get_episode_embedding(self, episode_id: int) -> Optional[List[float]]:
        """Retrieve and average all chunk embeddings for a specific episode."""
        try:
            results = self.collection.get(
                where={"episode_id": str(episode_id)},
                include=["embeddings"]
            )
            
            if not results or not results["embeddings"]:
                logger.warning(f"No embeddings found for episode {episode_id}")
                return None
                
            embeddings = results["embeddings"]
            import numpy as np
            avg_embedding = np.mean(embeddings, axis=0).tolist()
            return avg_embedding
        except Exception as e:
            logger.error(f"Failed to get embedding for episode {episode_id}: {e}")
            return None

    def find_similar_episodes(self, episode_id: int, limit: int = 5, exclude_recent_days: int = 7) -> List[Dict[str, Any]]:
        """
        Find episodes most similar to the given one.
        
        Args:
            episode_id: The ID of the reference episode.
            limit: Number of similar episodes to return.
            exclude_recent_days: Exclude episodes within this many days of the reference episode.
            
        Returns:
            List of similar episodes with scores and metadata.
        """
        # 1. Get embedding for the target episode
        target_embedding = self._get_episode_embedding(episode_id)
        if not target_embedding:
            return []
            
        # 2. Get target episode date for "recent" filtering
        from .repository import EntryRepository
        repo = EntryRepository()
        target_episode = repo.get_entry_by_id(episode_id)
        if not target_episode:
            return []
            
        from datetime import datetime, timedelta
        target_date = datetime.strptime(target_episode.date, "%Y-%m-%d")
        
        # 3. Query ChromaDB for similar chunks
        # We query for more than limit because we'll group by episode_id
        try:
            results = self.collection.query(
                query_embeddings=[target_embedding],
                n_results=limit * 10,
                include=["metadatas", "distances"]
            )
        except Exception as e:
            logger.error(f"ChromaDB query failed: {e}")
            return []
            
        if not results or not results["ids"] or not results["ids"][0]:
            return []
            
        # 4. Group and filter
        seen_episodes = {str(episode_id)} # Exclude self
        unique_results = []
        
        for i in range(len(results["ids"][0])):
            meta = results["metadatas"][0][i]
            dist = results["distances"][0][i]
            ep_id = meta.get("episode_id")
            ep_date_str = meta.get("date")
            
            if ep_id in seen_episodes:
                continue
                
            # Filter by "same week" (exclude_recent_days)
            if ep_date_str:
                try:
                    ep_date = datetime.strptime(ep_date_str, "%Y-%m-%d")
                    if abs((ep_date - target_date).days) < exclude_recent_days:
                        continue
                except:
                    pass
            
            similarity_score = 1.0 / (1.0 + dist)
            
            seen_episodes.add(ep_id)
            unique_results.append({
                "episode_id": int(ep_id),
                "title": meta.get("title", "Untitled"),
                "similarity_score": round(similarity_score, 4),
                "date": ep_date_str,
                "themes": meta.get("themes", ""),
                "mood": meta.get("mood", "")
            })
            
            if len(unique_results) >= limit:
                break
                
        return unique_results

    def find_opposite_episodes(self, episode_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Find episodes most different from the given one (most distant in embedding space).
        """
        target_embedding = self._get_episode_embedding(episode_id)
        if not target_embedding:
            return []
            
        # ChromaDB doesn't directly support "maximum distance" queries easily in one call
        # but we can fetch all and sort, or if the collection is large, this is slow.
        # For now, let's fetch a large sample and take the tail, or query all if small.
        
        try:
            # Get everything (not ideal for huge DBs but works for personal diaries)
            all_chunks = self.collection.get(include=["metadatas", "embeddings"])
            if not all_chunks or not all_chunks["embeddings"]:
                return []
                
            import numpy as np
            from sklearn.metrics.pairwise import cosine_similarity
            
            target_vector = np.array(target_embedding).reshape(1, -1)
            all_vectors = np.array(all_chunks["embeddings"])
            
            # Calculate similarities
            similarities = cosine_similarity(target_vector, all_vectors)[0]
            
            # Map back to episodes
            ep_scores = {}
            for i, sim in enumerate(similarities):
                meta = all_chunks["metadatas"][i]
                ep_id = str(meta.get("episode_id"))
                if ep_id == str(episode_id):
                    continue
                    
                if ep_id not in ep_scores or sim < ep_scores[ep_id]["score"]:
                    ep_scores[ep_id] = {
                        "episode_id": int(ep_id),
                        "title": meta.get("title", "Untitled"),
                        "score": sim,
                        "date": meta.get("date"),
                        "themes": meta.get("themes", "")
                    }
                    
            # Sort by score ascending (most different first)
            opposites = list(ep_scores.values())
            opposites.sort(key=lambda x: x["score"])
            
            # Format and limit
            results = []
            for op in opposites[:limit]:
                results.append({
                    "episode_id": op["episode_id"],
                    "title": op["title"],
                    "similarity_score": round(float(op["score"]), 4),
                    "date": op["date"],
                    "themes": op["themes"]
                })
                
            return results
        except Exception as e:
            logger.error(f"Failed to find opposite episodes: {e}")
            return []

def get_semantic_search():
    return SemanticSearch()
