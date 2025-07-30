#!/usr/bin/env python3
"""Test persistence functionality."""

from sage.core.persistence import JSONPersistence, ProfilePersistence, AgentFork
import tempfile
import shutil

def test_persistence():
    """Test that profiles persist across sessions."""
    # Use temp directory for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"🧪 Testing persistence in {tmpdir}")
        
        # Create persistence
        persistence = JSONPersistence(base_path=tmpdir)
        profile_persistence = ProfilePersistence(persistence)
        
        # Save a profile
        student_id = "test_student"
        profile = {
            "learning_style": "visual",
            "pace": "medium",
            "comprehension_level": "intermediate",
            "strengths": ["pattern recognition"],
            "total_sessions": 5,
            "interaction_history": [
                {"type": "lesson", "topic": "variables", "result": "completed"},
                {"type": "quiz", "topic": "variables", "result": "passed"}
            ]
        }
        
        print(f"💾 Saving profile for {student_id}...")
        profile_persistence.save_profile(student_id, profile)
        
        # Save some session data at different fork levels
        profile_persistence.save_session(student_id, "session_001", {
            "duration": 1200,
            "topics_covered": ["functions", "loops"]
        })
        
        profile_persistence.save_task_result(student_id, "task_001", {
            "score": 0.85,
            "time_taken": 300
        })
        
        profile_persistence.save_summary(student_id, "Great progress on functions!")
        
        # Now load it back
        print(f"📖 Loading profile back...")
        loaded_profile = profile_persistence.load_profile(student_id)
        
        # Verify
        assert loaded_profile is not None
        assert loaded_profile["learning_style"] == "visual"
        assert loaded_profile["total_sessions"] == 5
        assert len(loaded_profile["interaction_history"]) == 2
        
        print("✅ Profile loaded successfully!")
        
        # List all keys at different levels
        print("\n📁 Storage structure:")
        for fork in AgentFork:
            keys = persistence.list_keys("*", fork)
            print(f"  {fork.value}: {keys}")
        
        # Show file structure
        import os
        print("\n📂 File tree:")
        for root, dirs, files in os.walk(tmpdir):
            level = root.replace(tmpdir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f'{subindent}{file}')
        
        print("\n✅ All persistence tests passed!")

if __name__ == "__main__":
    test_persistence()