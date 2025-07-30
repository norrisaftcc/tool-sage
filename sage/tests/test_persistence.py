"""Unit tests for persistence layer."""

import pytest
import tempfile
import shutil
from pathlib import Path

from sage.core.persistence import (
    JSONPersistence, ProfilePersistence, AgentFork, PersistenceProvider
)


class TestJSONPersistence:
    """Test JSONPersistence implementation."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for tests."""
        temp_path = tempfile.mkdtemp()
        yield temp_path
        shutil.rmtree(temp_path)
    
    @pytest.fixture
    def persistence(self, temp_dir):
        """Create JSONPersistence instance with temp directory."""
        return JSONPersistence(base_path=temp_dir)
    
    def test_save_and_load(self, persistence):
        """Test basic save and load functionality."""
        test_data = {"name": "Alice", "level": "intermediate"}
        key = "test_key"
        
        # Save data
        persistence.save(key, test_data)
        
        # Load data
        loaded = persistence.load(key)
        assert loaded == test_data
    
    def test_fork_level_isolation(self, persistence):
        """Test that different fork levels have isolated storage."""
        key = "shared_key"
        alpha_data = {"type": "alpha", "value": 1}
        delta_data = {"type": "delta", "value": 2}
        
        # Save to different fork levels
        persistence.save(key, alpha_data, AgentFork.ALPHA)
        persistence.save(key, delta_data, AgentFork.DELTA)
        
        # Load from different fork levels
        assert persistence.load(key, AgentFork.ALPHA) == alpha_data
        assert persistence.load(key, AgentFork.DELTA) == delta_data
    
    def test_exists(self, persistence):
        """Test exists functionality."""
        key = "exists_test"
        
        # Should not exist initially
        assert not persistence.exists(key)
        
        # Save data
        persistence.save(key, {"data": "test"})
        
        # Should exist now
        assert persistence.exists(key)
    
    def test_list_keys(self, persistence):
        """Test listing keys functionality."""
        # Save multiple keys
        persistence.save("profiles/alice", {"name": "Alice"})
        persistence.save("profiles/bob", {"name": "Bob"})
        persistence.save("sessions/123", {"id": "123"})
        
        # List all keys
        all_keys = persistence.list_keys("*")
        assert len(all_keys) == 3
        
        # List with pattern
        profile_keys = persistence.list_keys("profiles/*")
        assert len(profile_keys) == 2
        assert "profiles/alice" in profile_keys
        assert "profiles/bob" in profile_keys
    
    def test_metadata_included(self, persistence, temp_dir):
        """Test that metadata is saved with data."""
        key = "metadata_test"
        data = {"value": "test"}
        
        persistence.save(key, data)
        
        # Read raw file to check metadata
        file_path = Path(temp_dir) / "alpha" / f"{key}.json"
        import json
        with open(file_path) as f:
            saved = json.load(f)
        
        assert "timestamp" in saved
        assert saved["fork"] == "alpha"
        assert saved["key"] == key
        assert saved["data"] == data


class TestProfilePersistence:
    """Test ProfilePersistence wrapper."""
    
    @pytest.fixture
    def profile_persistence(self):
        """Create ProfilePersistence with temp storage."""
        temp_dir = tempfile.mkdtemp()
        provider = JSONPersistence(base_path=temp_dir)
        yield ProfilePersistence(provider)
        shutil.rmtree(temp_dir)
    
    def test_save_and_load_profile(self, profile_persistence):
        """Test profile save/load functionality."""
        student_id = "alice"
        profile = {
            "learning_style": "visual",
            "pace": "medium",
            "comprehension_level": "intermediate",
            "strengths": ["pattern recognition"],
            "total_sessions": 5
        }
        
        # Save profile
        profile_persistence.save_profile(student_id, profile)
        
        # Load profile
        loaded = profile_persistence.load_profile(student_id)
        assert loaded == profile
    
    def test_save_session(self, profile_persistence):
        """Test session saving at beta level."""
        student_id = "bob"
        session_id = "session_001"
        session_data = {
            "duration": 1200,
            "topics": ["functions", "loops"]
        }
        
        # Save session
        profile_persistence.save_session(student_id, session_id, session_data)
        
        # Verify it's saved at beta level
        provider = profile_persistence.provider
        key = f"sessions/{student_id}/{session_id}"
        loaded = provider.load(key, AgentFork.BETA)
        assert loaded == session_data
    
    def test_save_task_result(self, profile_persistence):
        """Test task result saving at gamma level."""
        student_id = "charlie"
        task_id = "task_001"
        result = {"score": 0.85, "time_taken": 300}
        
        # Save task result
        profile_persistence.save_task_result(student_id, task_id, result)
        
        # Verify it's saved at gamma level
        provider = profile_persistence.provider
        key = f"tasks/{student_id}/{task_id}"
        loaded = provider.load(key, AgentFork.GAMMA)
        assert loaded == result
    
    def test_save_summary(self, profile_persistence):
        """Test summary saving at delta level."""
        student_id = "diana"
        summary = "Great progress on functions!"
        
        # Save summary
        profile_persistence.save_summary(student_id, summary)
        
        # Verify it's saved at delta level (with timestamp in key)
        provider = profile_persistence.provider
        keys = provider.list_keys(f"summaries/{student_id}/*", AgentFork.DELTA)
        assert len(keys) == 1
        
        loaded = provider.load(keys[0], AgentFork.DELTA)
        assert loaded["summary"] == summary


class TestPersistenceIntegration:
    """Integration tests with SharedStore."""
    
    def test_shared_store_persistence(self):
        """Test SharedStore with persistence integration."""
        from sage.core.base import SharedStore
        
        temp_dir = tempfile.mkdtemp()
        persistence = JSONPersistence(base_path=temp_dir)
        store = SharedStore(persistence=persistence)
        
        # Verify persistence is attached
        assert store.persistence is not None
        assert isinstance(store.persistence, JSONPersistence)
        
        shutil.rmtree(temp_dir)