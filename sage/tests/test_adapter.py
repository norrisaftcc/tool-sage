"""Unit tests for content adaptation agent."""

import pytest
from sage.agents.adapter import ContentAdaptationNode
from sage.core.base import SharedStore


class TestContentAdaptationNode:
    """Test ContentAdaptationNode functionality."""
    
    @pytest.fixture
    def adapter(self):
        """Create adapter instance."""
        return ContentAdaptationNode(name="adapter")
    
    @pytest.fixture
    def shared_store(self):
        """Create shared store with test data."""
        store = SharedStore()
        store.update({
            "current_student": "test_student",
            "student_profiles": {
                "test_student": {
                    "learning_style": "visual",
                    "comprehension_level": "beginner"
                }
            },
            "conversation": [
                {"role": "student", "content": "Hello"},
                {"role": "assistant", "content": "Welcome!"},
                {"role": "student", "content": "This is confusing"}
            ],
            "student_input": "I'm really frustrated and don't understand",
            "topic": "Python basics"
        })
        return store
    
    def test_sentiment_analysis_positive(self, adapter):
        """Test positive sentiment detection."""
        positive_texts = [
            "This is great!",
            "I understand now, thanks!",
            "That makes sense, awesome explanation",
            "Cool, got it!"
        ]
        
        for text in positive_texts:
            sentiment = adapter._analyze_sentiment(text)
            assert sentiment == "positive", f"Failed for: {text}"
    
    def test_sentiment_analysis_negative(self, adapter):
        """Test negative sentiment detection."""
        negative_texts = [
            "I'm confused",
            "This is too hard",
            "I don't understand anything",
            "I'm frustrated and stuck"
        ]
        
        for text in negative_texts:
            sentiment = adapter._analyze_sentiment(text)
            assert sentiment == "negative", f"Failed for: {text}"
    
    def test_sentiment_analysis_neutral(self, adapter):
        """Test neutral sentiment detection."""
        neutral_texts = [
            "Okay",
            "Continue please",
            "Next",
            "Go on"
        ]
        
        for text in neutral_texts:
            sentiment = adapter._analyze_sentiment(text)
            assert sentiment == "neutral", f"Failed for: {text}"
    
    def test_conversation_sentiment_trend(self, adapter):
        """Test sentiment trend analysis."""
        # Declining trend
        declining_messages = [
            {"role": "student", "content": "This is interesting"},
            {"role": "student", "content": "Wait, I'm getting confused"},
            {"role": "student", "content": "I don't understand this at all"}
        ]
        trend = adapter._analyze_conversation_sentiment(declining_messages)
        assert trend == "declining"
        
        # Improving trend
        improving_messages = [
            {"role": "student", "content": "I'm lost"},
            {"role": "student", "content": "Oh, that helps a bit"},
            {"role": "student", "content": "Great, I get it now!"}
        ]
        trend = adapter._analyze_conversation_sentiment(improving_messages)
        assert trend == "improving"
        
        # Stable trend
        stable_messages = [
            {"role": "student", "content": "Okay"},
            {"role": "student", "content": "Continue"},
            {"role": "student", "content": "Next please"}
        ]
        trend = adapter._analyze_conversation_sentiment(stable_messages)
        assert trend == "stable"
    
    def test_prep_gathers_context(self, adapter, shared_store):
        """Test that prep gathers all necessary context."""
        prep_data = adapter.prep(shared_store)
        
        assert prep_data["student_id"] == "test_student"
        assert prep_data["profile"]["learning_style"] == "visual"
        assert len(prep_data["recent_messages"]) == 3
        assert prep_data["current_topic"] == "Python basics"
        assert prep_data["last_input"] == "I'm really frustrated and don't understand"
    
    def test_adaptation_for_frustrated_student(self, adapter, shared_store):
        """Test adaptations for frustrated student."""
        prep_data = adapter.prep(shared_store)
        
        # Mock the exec to test sentiment analysis part
        sentiment = adapter._analyze_sentiment(prep_data["last_input"])
        assert sentiment == "negative"
        
        # Test that high emotional support would be triggered
        # (Full exec test would require mocking LLM)
    
    def test_parse_adaptations(self, adapter):
        """Test parsing of adaptation responses."""
        # Test response with clear indicators
        response = """Based on the student's frustration, I recommend:
        - Slower pace to give them time to process
        - Decrease complexity and use simpler examples
        - Provide high emotional support
        - Take a review approach before continuing
        - Use an encouraging tone
        """
        
        adaptations = adapter._parse_adaptations(response)
        
        assert adaptations["pace"] == "slower"
        assert adaptations["complexity"] == "decrease"
        assert adaptations["emotional_support"] == "high"
        assert adaptations["next_action"] == "review"
        assert adaptations["message_tone"] == "encouraging"
    
    def test_post_updates_shared_store(self, adapter, shared_store):
        """Test that post properly updates shared store."""
        prep_res = adapter.prep(shared_store)
        exec_res = {
            "sentiment": "negative",
            "sentiment_trend": "declining",
            "pace": "slower",
            "complexity": "decrease",
            "emotional_support": "high",
            "next_action": "review",
            "message_tone": "encouraging"
        }
        
        result = adapter.post(shared_store, prep_res, exec_res)
        
        assert result == "orchestrator"
        assert "current_adaptations" in shared_store._store
        assert shared_store["content_adapted"] is True
        assert "adapted_content" in shared_store._store
        assert "logs" in shared_store._store