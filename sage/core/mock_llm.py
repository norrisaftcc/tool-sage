"""Mock LLM for testing agent behaviors without real API calls."""

import random
import yaml
from typing import Dict, Any, List


class MockLLM:
    """Simulates LLM responses for testing."""
    
    def __init__(self):
        self.response_templates = {
            "profile_analysis": [
                {
                    "learning_style": "visual",
                    "pace": "medium",
                    "comprehension_level": "intermediate",
                    "strengths": ["pattern recognition", "spatial reasoning"],
                    "areas_for_improvement": ["abstract concepts", "long-form reading"]
                },
                {
                    "learning_style": "kinesthetic",
                    "pace": "fast",
                    "comprehension_level": "beginner",
                    "strengths": ["hands-on practice", "experimentation"],
                    "areas_for_improvement": ["theory", "patience with details"]
                }
            ],
            "content_adaptation": [
                "Let's visualize this concept with a diagram: [Mock Diagram]. Try tracing through each step with your finger.",
                "Here's a hands-on exercise: Build a simple model using everyday objects to represent the concept.",
                "Breaking this down into smaller chunks: Step 1... Step 2... Step 3..."
            ],
            "questions": [
                {
                    "question": "What is the main purpose of this concept?",
                    "options": ["A) To solve problems", "B) To create patterns", "C) To analyze data", "D) To build models"],
                    "correct_answer": "A",
                    "explanation": "This concept primarily helps in problem-solving by providing a structured approach."
                },
                {
                    "question": "Which example best demonstrates this principle?",
                    "options": ["A) Example 1", "B) Example 2", "C) Example 3", "D) Example 4"],
                    "correct_answer": "B",
                    "explanation": "Example 2 shows the clearest application of the principle in action."
                }
            ],
            "progress_decision": ["continue", "review", "advance", "assist"],
            "orchestrator_decision": ["profile", "adapt", "question", "progress", "respond"]
        }
    
    def call(self, prompt: str) -> str:
        """Simulate LLM call based on prompt content."""
        prompt_lower = prompt.lower()
        
        # Detect intent from prompt
        if "analyze" in prompt_lower and "learning patterns" in prompt_lower:
            response = random.choice(self.response_templates["profile_analysis"])
            return yaml.dump(response)
        
        elif "adapt" in prompt_lower and "content" in prompt_lower:
            return random.choice(self.response_templates["content_adaptation"])
        
        elif "generate" in prompt_lower and "question" in prompt_lower:
            question = random.choice(self.response_templates["questions"])
            return yaml.dump(question)
        
        elif "progress analysis" in prompt_lower:
            return random.choice(self.response_templates["progress_decision"])
        
        elif "determine next agent" in prompt_lower:
            return random.choice(self.response_templates["orchestrator_decision"])
        
        else:
            # Generic response
            return "I understand. Let me help you with that concept."
    
    async def call_async(self, prompt: str) -> str:
        """Async version of call for testing async nodes."""
        # Simulate some async delay
        import asyncio
        await asyncio.sleep(0.1)
        return self.call(prompt)


# Global instance for easy access
mock_llm = MockLLM()


def call_llm(prompt: str) -> str:
    """Mock function to replace real LLM calls."""
    return mock_llm.call(prompt)


async def call_llm_async(prompt: str) -> str:
    """Mock async function to replace real LLM calls."""
    return await mock_llm.call_async(prompt)