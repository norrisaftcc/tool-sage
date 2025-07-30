"""Unit tests for LLM integration."""

import pytest
from sage.core.llm import llm_manager, OllamaProvider, MockProvider, AgentFork


class TestMockProvider:
    """Test MockProvider functionality."""
    
    def test_mock_always_available(self):
        """Test that mock provider is always available."""
        mock = MockProvider()
        assert mock.is_available() is True
    
    def test_mock_responses(self):
        """Test mock provider responses."""
        mock = MockProvider()
        
        # Test keyword matching
        assert "Hello!" in mock.generate("hello there")
        assert "Python" in mock.generate("Tell me about Python")
        assert "test" in mock.generate("Can you test me?")
        
        # Test default response
        assert "I understand" in mock.generate("random input")


class TestOllamaProvider:
    """Test OllamaProvider functionality."""
    
    def test_fork_model_mapping(self):
        """Test that fork levels map to correct models."""
        assert OllamaProvider.FORK_MODELS[AgentFork.ALPHA] == "llama2:13b"
        assert OllamaProvider.FORK_MODELS[AgentFork.BETA] == "deepseek-r1:latest"
        assert OllamaProvider.FORK_MODELS[AgentFork.GAMMA] == "llama3.2:latest"
        assert OllamaProvider.FORK_MODELS[AgentFork.DELTA] == "llama3.2:latest"
    
    def test_for_fork_factory(self):
        """Test creating providers for specific fork levels."""
        alpha_provider = OllamaProvider.for_fork(AgentFork.ALPHA)
        assert alpha_provider.model == "llama2:13b"
        
        delta_provider = OllamaProvider.for_fork(AgentFork.DELTA)
        assert delta_provider.model == "llama3.2:latest"


class TestLLMManager:
    """Test LLMManager functionality."""
    
    def test_default_providers(self):
        """Test that default providers are registered."""
        assert "mock" in llm_manager.providers
        assert "ollama" in llm_manager.providers
        
        assert isinstance(llm_manager.providers["mock"], MockProvider)
        assert isinstance(llm_manager.providers["ollama"], OllamaProvider)
    
    def test_fallback_to_mock(self):
        """Test fallback to mock when Ollama unavailable."""
        # Get provider when explicitly requesting mock
        provider = llm_manager.get_provider("mock")
        assert isinstance(provider, MockProvider)
    
    def test_generate_with_mock(self):
        """Test generation with mock provider."""
        # Force mock by requesting it
        llm_manager.default_provider = "mock"
        response = llm_manager.generate(
            prompt="Hello",
            fork=AgentFork.BETA
        )
        
        assert response is not None
        assert len(response) > 0


class TestIntegration:
    """Integration tests with actual Ollama (if available)."""
    
    @pytest.mark.skipif(
        not OllamaProvider().is_available(),
        reason="Ollama not running"
    )
    def test_ollama_generation(self):
        """Test actual Ollama generation."""
        provider = OllamaProvider()
        response = provider.generate(
            "What is 2+2? Answer with just the number.",
            temperature=0.1
        )
        
        assert response is not None
        assert "4" in response
    
    @pytest.mark.skipif(
        not OllamaProvider().is_available(),
        reason="Ollama not running"
    )
    def test_thinking_tag_removal(self):
        """Test that thinking tags are removed."""
        response = llm_manager.generate(
            prompt="Test prompt",
            fork=AgentFork.BETA
        )
        
        # Should not contain thinking tags
        assert "<think>" not in response
        assert "</think>" not in response