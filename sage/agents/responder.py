"""Response Generator Agent - Creates responses for student interaction."""

from typing import Dict, Any
from sage.core.base import Node, SharedStore
from sage.core.mock_llm import call_llm


class ResponseGeneratorNode(Node):
    """Generates appropriate responses to students."""
    
    def prep(self, shared: SharedStore) -> Dict[str, Any]:
        """Gather context for response generation."""
        student_id = shared.get("current_student", "default_student")
        profiles = shared.get("student_profiles", {})
        
        return {
            "student_input": shared.get("student_input", ""),
            "profile": profiles.get(student_id, {}),
            "adapted_content": shared.get("adapted_content", ""),
            "recent_action": shared.get("next_agent", ""),
            "topic": shared.get("topic", "general"),
            "assessment_results": shared.get("last_assessment_result", None)
        }
    
    def exec(self, data: Dict[str, Any]) -> str:
        """Generate response based on context."""
        # For MVP, use simple templated responses
        profile = data.get("profile", {})
        
        if data["adapted_content"]:
            # We have adapted content to deliver
            return data["adapted_content"]
        
        elif data["assessment_results"]:
            # Provide assessment feedback
            result = data["assessment_results"]
            return f"You scored {result.get('score', 0)}%. {result.get('feedback', 'Keep practicing!')}"
        
        elif profile:
            # Personalized greeting based on profile
            style = profile.get("learning_style", "general")
            level = profile.get("comprehension_level", "intermediate")
            
            return f"""Welcome back! Based on your {style} learning style and {level} level, 
I've prepared some materials for you. What would you like to work on today?"""
        
        else:
            # Generic response
            return "Hello! I'm SAGE, your adaptive learning assistant. Let's start by understanding how you learn best."
    
    def post(self, shared: SharedStore, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Store response and update state."""
        # Add to conversation history
        if "conversation" not in shared._store:
            shared["conversation"] = []
        
        shared["conversation"].append({
            "role": "assistant",
            "content": exec_res
        })
        
        # Set the response for CLI to display
        shared["current_response"] = exec_res
        
        # Clear the student input
        shared["student_input"] = ""
        
        return "response_delivered"