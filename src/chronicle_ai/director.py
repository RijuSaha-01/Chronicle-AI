"""
Chronicle AI - Director Engine
Optimization, benchmarking, and quality control for narrative generation.
"""

import time
import json
import logging
from typing import Dict, List, Optional, Any
from .models import Entry

logger = logging.getLogger(__name__)

class EpisodeStructure:
    """
    Validates the quality and structure of generated narratives.
    """
    def __init__(self, min_length: int = 50, min_sentences: int = 2):
        self.min_length = min_length
        self.min_sentences = min_sentences

    def validate(self, narrative: str) -> Dict[str, Any]:
        """
        Perform quality checks on a narrative string.
        """
        if not narrative:
            return {"valid": False, "issues": ["Narrative is empty"]}

        issues = []
        
        # Check length
        if len(narrative) < self.min_length:
            issues.append(f"Narrative too short ({len(narrative)} characters)")

        # Check sentence count
        sentences = [s.strip() for s in narrative.replace('!', '.').replace('?', '.').split('.') if s.strip()]
        if len(sentences) < self.min_sentences:
            issues.append(f"Insufficient sentences ({len(sentences)})")

        # Check for repetition
        if self._has_repetition(sentences):
            issues.append("Repetition detected in sentences")

        # Check for proper structure (heuristic: look for pronouns/verbs)
        # For simplicity, we'll check if it looks like third person (he/she/they or name)
        # This is a bit complex for a simple validator, so we'll keep it basic.
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "sentence_count": len(sentences),
            "char_count": len(narrative)
        }

    def _has_repetition(self, sentences: List[str]) -> bool:
        """Check for identical or highly similar sentences."""
        if not sentences:
            return False
            
        seen = set()
        for s in sentences:
            s_clean = s.lower().strip()
            if s_clean in seen:
                return True
            seen.add(s_clean)
            
        # Also check for repeating phrases (basic check)
        words = " ".join(sentences).lower().split()
        for i in range(len(words) - 5):
            phrase = " ".join(words[i:i+4])
            if " ".join(words).count(phrase) > 2:
                # Basic check for repeated 4-word phrases
                return True
                
        return False

class PerformanceLogger:
    """
    Tracks and logs generation times for various components.
    """
    def __init__(self):
        self.logs = []

    def log_event(self, component: str, duration: float, metadata: Optional[Dict] = None):
        entry = {
            "timestamp": time.time(),
            "component": component,
            "duration": duration,
            "metadata": metadata or {}
        }
        self.logs.append(entry)
        logger.info(f"Performance: {component} took {duration:.2f}s")

    def get_stats(self) -> Dict[str, Any]:
        if not self.logs:
            return {}
            
        stats = {}
        components = set(log["component"] for log in self.logs)
        
        for comp in components:
            durations = [log["duration"] for log in self.logs if log["component"] == comp]
            stats[comp] = {
                "avg": sum(durations) / len(durations),
                "max": max(durations),
                "min": min(durations),
                "count": len(durations)
            }
        return stats

class ComponentCache:
    """
    Simple caching layer for episode components.
    """
    def __init__(self):
        self.cache = {}

    def get(self, key: str) -> Optional[Any]:
        return self.cache.get(key)

    def set(self, key: str, value: Any):
        self.cache[key] = value

    def invalidate(self, key: str):
        if key in self.cache:
            del self.cache[key]

    def clear(self):
        self.cache.clear()

class DirectorEngine:
    """
    The orchestrator for quality, benchmarking, and optimization.
    """
    def __init__(self, repo=None):
        self.repo = repo
        self.structure_validator = EpisodeStructure()
        self.perf_logger = PerformanceLogger()
        self.cache = ComponentCache()

    def run_benchmark(self, sample_entries: List[Entry]) -> Dict[str, Any]:
        """
        Process sample entries and report metrics.
        """
        from .llm_client import process_entry
        results = []
        total_start = time.time()
        
        for i, entry in enumerate(sample_entries):
            start_time = time.time()
            
            # Use process_entry
            process_entry(entry)
            
            duration = time.time() - start_time
            self.perf_logger.log_event("full_pipeline", duration, {"entry_id": entry.id or i})
            
            # Validate quality
            quality = self.structure_validator.validate(entry.narrative_text or "")
            
            results.append({
                "entry_id": entry.id or i,
                "duration": duration,
                "quality": quality
            })

        total_duration = time.time() - total_start
        
        return {
            "total_duration": total_duration,
            "avg_duration": total_duration / len(sample_entries) if sample_entries else 0,
            "results": results,
            "stats": self.perf_logger.get_stats()
        }

# Global instance for shared use
director_engine = DirectorEngine()
