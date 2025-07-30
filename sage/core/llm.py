"""LLM integration layer - Simple code, rich models."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from enum import Enum
import json

from sage.core.persistence import AgentFork


class LLMProvider(ABC):
    """Abstract interface for LLM providers."""
    
    @abstractmethod
    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Generate text from prompt."""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if provider is available."""
        pass


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""
    
    # Model mapping for fork levels (using available models)
    FORK_MODELS = {
        AgentFork.ALPHA: "llama2:13b",           # Highest quality (13B)
        AgentFork.BETA: "deepseek-r1:latest",    # Good balance (7.6B) 
        AgentFork.GAMMA: "llama3.2:latest",      # Fast, focused (3.2B)
        AgentFork.DELTA: "llama3.2:latest"       # Tiny, quick (3.2B)
    }
    
    # Timeout configuration by model
    TIMEOUTS = {
        "llama2:13b": 60,
        "deepseek-r1:latest": 60,
        "llama3.2:latest": 30,
        # Default timeout
        "default": 30
    }
    
    def __init__(self, model: Optional[str] = None, base_url: str = "http://localhost:11434"):
        self.model = model or "llama3.2:latest"
        self.base_url = base_url
        
    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Generate using Ollama API."""
        try:
            import requests
        except ImportError:
            raise ImportError("requests required for Ollama. Install with: pip install requests")
        
        # Build the payload
        payload = {
            "model": kwargs.get("model", self.model),
            "prompt": prompt,
            "stream": False
        }
        
        # Add system prompt if provided
        if system:
            payload["system"] = system
            
        # Add any additional parameters
        if "temperature" in kwargs:
            payload["temperature"] = kwargs["temperature"]
        if "max_tokens" in kwargs:
            payload["max_tokens"] = kwargs["max_tokens"]
            
        try:
            # Get timeout based on model
            model_name = kwargs.get("model", self.model)
            timeout = self.TIMEOUTS.get(model_name, self.TIMEOUTS["default"])
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=timeout
            )
            response.raise_for_status()
            
            result = response.json()
            text = result.get("response", "")
            
            # Clean up thinking tags if present (some models add these)
            import re
            text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
            
            return text.strip()
            
        except Exception:
            # Fallback to mock for development - don't expose internal errors
            return f"[Ollama Error] Mock response for: {prompt[:50]}..."
    
    def is_available(self) -> bool:
        """Check if Ollama is running."""
        try:
            import requests
            response = requests.get(f"{self.base_url}/api/tags", timeout=2)
            return response.status_code == 200
        except:
            return False
    
    @classmethod
    def for_fork(cls, fork: AgentFork) -> "OllamaProvider":
        """Create provider configured for specific fork level."""
        model = cls.FORK_MODELS.get(fork, "llama3.2:latest")  # Use actual default
        return cls(model=model)


class MockProvider(LLMProvider):
    """Mock LLM for testing."""
    
    def __init__(self):
        self.responses = {
            "hello": "Hello! I'm SAGE, your adaptive learning assistant.",
            "python": "Python is a great language! Let's explore functions today.",
            "test": "I'd be happy to test your knowledge. Ready?",
            "default": "I understand. Let me help you with that."
        }
    
    def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Generate mock response."""
        prompt_lower = prompt.lower()
        
        for key, response in self.responses.items():
            if key in prompt_lower:
                return response
                
        return self.responses["default"]
    
    def is_available(self) -> bool:
        """Always available."""
        return True


class LLMManager:
    """Manages LLM providers with fallback support."""
    
    def __init__(self):
        self.providers: Dict[str, LLMProvider] = {}
        self.default_provider = "mock"
        self._ollama_available = None  # Cache availability check
        
        # Register default providers
        self.register("mock", MockProvider())
        self.register("ollama", OllamaProvider())
        
    def register(self, name: str, provider: LLMProvider):
        """Register a new provider."""
        self.providers[name] = provider
        
    def get_provider(self, name: Optional[str] = None) -> LLMProvider:
        """Get provider by name with fallback."""
        if name and name in self.providers:
            provider = self.providers[name]
            if provider.is_available():
                return provider
                
        # Try Ollama first
        if "ollama" in self.providers and self.providers["ollama"].is_available():
            return self.providers["ollama"]
            
        # Fallback to mock
        return self.providers["mock"]
    
    def generate(self, prompt: str, fork: AgentFork = AgentFork.BETA, **kwargs) -> str:
        """Generate with appropriate provider for fork level."""
        # Check Ollama availability (cached)
        if self._ollama_available is None:
            self._ollama_available = self.providers["ollama"].is_available()
            
        # For Ollama, use fork-specific model
        if self._ollama_available:
            provider = OllamaProvider.for_fork(fork)
        else:
            provider = self.get_provider()
            
        return provider.generate(prompt, **kwargs)


# Global LLM manager instance
llm_manager = LLMManager()