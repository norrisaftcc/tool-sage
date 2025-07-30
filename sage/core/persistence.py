"""Persistence layer for SAGE - simple code, rich data."""

import json
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from enum import Enum


class AgentFork(Enum):
    """Resource tiers for agents."""
    ALPHA = "alpha"
    BETA = "beta"
    GAMMA = "gamma"
    DELTA = "delta"


class PersistenceProvider(ABC):
    """Abstract interface for persistence - swap implementations later."""
    
    @abstractmethod
    def save(self, key: str, data: Dict[str, Any], fork: AgentFork = AgentFork.ALPHA) -> None:
        """Save data with appropriate storage for fork level."""
        pass
    
    @abstractmethod
    def load(self, key: str, fork: AgentFork = AgentFork.ALPHA) -> Optional[Dict[str, Any]]:
        """Load data from appropriate storage."""
        pass
    
    @abstractmethod
    def exists(self, key: str, fork: AgentFork = AgentFork.ALPHA) -> bool:
        """Check if data exists."""
        pass
    
    @abstractmethod
    def list_keys(self, pattern: str = "*", fork: AgentFork = AgentFork.ALPHA) -> list:
        """List all keys matching pattern."""
        pass


class JSONPersistence(PersistenceProvider):
    """Simple JSON file storage - perfect for MVP and delta agents."""
    
    def __init__(self, base_path: str = "~/.sage/data"):
        self.base_path = Path(base_path).expanduser()
        
        # Different directories for different fork levels
        self.storage_paths = {
            AgentFork.ALPHA: self.base_path / "alpha",  # Full profiles
            AgentFork.BETA: self.base_path / "beta",    # Session data
            AgentFork.GAMMA: self.base_path / "gamma",  # Task cache
            AgentFork.DELTA: self.base_path / "delta"   # Ephemeral
        }
        
        # Create directories
        for path in self.storage_paths.values():
            path.mkdir(parents=True, exist_ok=True)
    
    def _get_path(self, key: str, fork: AgentFork) -> Path:
        """Get file path for a key at given fork level."""
        # Sanitize key for filesystem
        safe_key = key.replace("/", "_").replace("\\", "_")
        return self.storage_paths[fork] / f"{safe_key}.json"
    
    def save(self, key: str, data: Dict[str, Any], fork: AgentFork = AgentFork.ALPHA) -> None:
        """Save data as JSON with metadata."""
        path = self._get_path(key, fork)
        
        # Add metadata
        wrapped_data = {
            "key": key,
            "fork": fork.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # Pretty print for human readability (remember: data is where magic lives)
        with open(path, 'w') as f:
            json.dump(wrapped_data, f, indent=2, sort_keys=True)
    
    def load(self, key: str, fork: AgentFork = AgentFork.ALPHA) -> Optional[Dict[str, Any]]:
        """Load data from JSON."""
        path = self._get_path(key, fork)
        
        if not path.exists():
            return None
        
        try:
            with open(path, 'r') as f:
                wrapped = json.load(f)
                return wrapped.get("data")
        except Exception:
            return None
    
    def exists(self, key: str, fork: AgentFork = AgentFork.ALPHA) -> bool:
        """Check if data exists."""
        return self._get_path(key, fork).exists()
    
    def list_keys(self, pattern: str = "*", fork: AgentFork = AgentFork.ALPHA) -> list:
        """List all keys in a fork level."""
        import glob
        
        search_pattern = self.storage_paths[fork] / f"{pattern}.json"
        files = glob.glob(str(search_pattern))
        
        keys = []
        for file in files:
            name = Path(file).stem
            # Reverse the sanitization
            key = name.replace("_", "/")
            keys.append(key)
        
        return sorted(keys)


class ProfilePersistence:
    """Specialized persistence for student profiles."""
    
    def __init__(self, provider: PersistenceProvider):
        self.provider = provider
    
    def save_profile(self, student_id: str, profile: Dict[str, Any]) -> None:
        """Save a student profile at Alpha level."""
        key = f"profiles/{student_id}"
        self.provider.save(key, profile, AgentFork.ALPHA)
    
    def load_profile(self, student_id: str) -> Optional[Dict[str, Any]]:
        """Load a student profile."""
        key = f"profiles/{student_id}"
        return self.provider.load(key, AgentFork.ALPHA)
    
    def save_session(self, student_id: str, session_id: str, data: Dict[str, Any]) -> None:
        """Save session data at Beta level."""
        key = f"sessions/{student_id}/{session_id}"
        self.provider.save(key, data, AgentFork.BETA)
    
    def save_task_result(self, student_id: str, task_id: str, result: Dict[str, Any]) -> None:
        """Save task result at Gamma level."""
        key = f"tasks/{student_id}/{task_id}"
        self.provider.save(key, result, AgentFork.GAMMA)
    
    def save_summary(self, student_id: str, summary: str) -> None:
        """Save a quick summary at Delta level."""
        key = f"summaries/{student_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.provider.save(key, {"summary": summary}, AgentFork.DELTA)