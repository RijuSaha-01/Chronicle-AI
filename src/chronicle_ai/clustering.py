"""
Chronicle AI - Memory Clustering Engine

Uses embedding similarity to cluster related episodes and auto-name them using LLM.
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Any
from .embedding_engine import get_embedding_engine
from .llm_client import get_llm_client
from .repository import get_repository
from .models import Entry

# Check if sklearn is available
try:
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

class MemoryClusterer:
    """
    Handles clustering of episodes based on semantic embeddings.
    """
    
    def __init__(self, repo=None, engine=None):
        self.repo = repo or get_repository()
        self.engine = engine or get_embedding_engine()
        self.llm = get_llm_client()
        
    def cluster_episodes(self, k: int = 12) -> Dict[str, List[Entry]]:
        """
        Retrieves all embeddings, clusters them into k groups, and names them.
        """
        if not SKLEARN_AVAILABLE:
            logger.error("scikit-learn not installed. Cannot perform clustering.")
            return {}
            
        # 1. Get all embeddings from ChromaDB
        data = self.engine.collection.get(include=['embeddings', 'metadatas'])
        if not data or not data['embeddings']:
            logger.warning("No embeddings found in ChromaDB.")
            return {}
            
        embeddings = np.array(data['embeddings'])
        metadatas = data['metadatas']
        
        # Mapping from chunk embeddings to episode IDs
        episode_map = {} # episode_id -> list of embedding indices
        for i, meta in enumerate(metadatas):
            ep_id = int(meta['episode_id'])
            if ep_id not in episode_map:
                episode_map[ep_id] = []
            episode_map[ep_id].append(i)
            
        # Average embeddings per episode to get one vector per episode
        episode_ids = sorted(episode_map.keys())
        ep_embeddings = []
        for ep_id in episode_ids:
            indices = episode_map[ep_id]
            avg_emb = np.mean(embeddings[indices], axis=0)
            ep_embeddings.append(avg_emb)
            
        ep_embeddings = np.array(ep_embeddings)
        
        # 2. Perform clustering
        num_clusters = min(k, len(ep_embeddings))
        if num_clusters < 2:
            logger.warning("Not enough episodes to cluster.")
            # Assign all to a single default cluster if needed
            cluster_labels = [0] * len(ep_embeddings)
        else:
            kmeans = KMeans(n_clusters=num_clusters, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(ep_embeddings)
            
        # 3. Group episodes by cluster
        clusters = {} # cluster_index -> list of entries
        for i, label in enumerate(cluster_labels):
            ep_id = episode_ids[i]
            entry = self.repo.get_entry_by_id(ep_id)
            if entry:
                if label not in clusters:
                    clusters[label] = []
                clusters[label].append(entry)
                
        # 4. Name clusters using LLM
        named_clusters = {}
        for label, entries in clusters.items():
            cluster_name = self._generate_cluster_name(entries)
            named_clusters[cluster_name] = entries
            
            # Update entries in repo with cluster label
            for entry in entries:
                entry.cluster_label = cluster_name
                self.repo.update_entry(entry)
                
        return named_clusters

    def _generate_cluster_name(self, entries: List[Entry]) -> str:
        """Use LLM to generate a name for the cluster based on episode titles/keywords."""
        # Selection of representative info
        titles = [e.title for e in entries if e.title]
        keywords = []
        for e in entries:
            keywords.extend(e.keywords or [])
            
        # De-duplicate keywords
        keywords = list(set(keywords))[:15]
        
        context = f"Titles: {', '.join(titles[:15])}\nKeywords: {', '.join(keywords)}"
        
        prompt = f"""You are an expert at identifying narrative themes in personal life stories.
Based on the following list of episode titles and keywords from a cluster of related memories, generate a punchy 2-3 word name for this cluster.

The name should be evocative and represent the common thread. 
Examples: 'Work Challenges', 'Weekend Adventures', 'Late Nights', 'Gym Progress', 'Creative Bursts', 'Quiet Moments'.

Data:
{context}

Cluster Name:"""

        name = self.llm.generate(prompt).strip().strip('"').strip("'")
        # Cleanup
        if len(name.split()) > 5:
            name = " ".join(name.split()[:3])
            
        return name or f"Cluster {len(titles)} Memories"

    def get_cluster_map(self) -> Dict[str, int]:
        """Returns a map of cluster name to count of episodes."""
        entries = self.repo.list_entries()
        counts = {}
        for e in entries:
            if e.cluster_label:
                counts[e.cluster_label] = counts.get(e.cluster_label, 0) + 1
        return counts

    def visualize_clusters(self):
        """Prints a text-based cluster map."""
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel
        
        console = Console()
        counts = self.get_cluster_map()
        
        if not counts:
            console.print("[yellow]📭 No clusters found. Run 'chronicle clusters --refresh' to generate.[/yellow]")
            return
            
        console.print(Panel("[bold cyan]🎬 Chronicle Memories: Cluster Map[/bold cyan]", border_style="cyan"))
        
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Cluster Name", width=30)
        table.add_column("Episodes", justify="center", width=10)
        table.add_column("Density", width=25)
        
        max_count = max(counts.values()) if counts else 1
        
        for name, count in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            bar_len = int((count / max_count) * 20)
            density = "█" * bar_len
            table.add_row(name, str(count), f"[cyan]{density}[/]")
            
        console.print(table)
        console.print(f"\n[dim]Total of {len(counts)} major clusters identified.[/dim]")

    def assign_entry_to_cluster(self, entry: Entry):
        """Assigns a single entry to the most appropriate existing cluster."""
        counts = self.get_cluster_map()
        if not counts:
            return
            
        cluster_names = list(counts.keys())
        
        prompt = f"""You are an expert at organizing memories.
Assign the following diary episode to one of the existing memory clusters.

Existing Clusters:
{', '.join(cluster_names)}

Episode Title: {entry.display_title()}
Keywords: {', '.join(entry.keywords)}
Synopsis: {entry.synopsis}

Identify the best matching cluster from the list above. If none match well, pick the closest one.
Only output the cluster name, nothing else.

Cluster Name:"""

        name = self.llm.generate(prompt).strip().strip('"').strip("'")
        
        # Verify the name matches an existing cluster (fuzzy)
        best_match = None
        for cn in cluster_names:
            if cn.lower() in name.lower() or name.lower() in cn.lower():
                best_match = cn
                break
        
        if best_match:
            entry.cluster_label = best_match
            self.repo.update_entry(entry)
            logger.info(f"Assigned episode {entry.id} to cluster: {best_match}")

memory_clusterer = MemoryClusterer()
