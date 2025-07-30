"""Response Generator Agent - Creates responses for student interaction."""

from typing import Dict, Any
from sage.core.base import Node, SharedStore
from sage.core.llm import llm_manager
from sage.core.persistence import AgentFork


class ResponseGeneratorNode(Node):
    """Generates appropriate responses to students."""
    
    # System prompt for educational responses
    SYSTEM_PROMPT = """You are SAGE, an adaptive learning assistant. You adjust your teaching style based on the student's profile.
Be encouraging, clear, and pedagogically sound. Keep responses concise and focused."""
    
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
        profile = data.get("profile", {})
        
        # Build context for LLM
        context_parts = []
        
        if profile:
            context_parts.append(f"Student profile: learning style={profile.get('learning_style', 'unknown')}, level={profile.get('comprehension_level', 'unknown')}")
            
        if data["topic"]:
            context_parts.append(f"Current topic: {data['topic']}")
            
        if data["adapted_content"]:
            context_parts.append(f"Adapted content ready: {data['adapted_content']}")
            
        if data["assessment_results"]:
            result = data["assessment_results"]
            context_parts.append(f"Assessment result: score={result.get('score', 0)}%, feedback={result.get('feedback', '')}")
        
        # Use class-level system prompt
        system_prompt = self.SYSTEM_PROMPT
        
        # Build the prompt
        prompt = f"""Context: {' | '.join(context_parts)}
        
Student says: {data['student_input']}
        
Provide an appropriate educational response:"""
        
        # Use Beta fork level for standard responses
        response = llm_manager.generate(
            prompt=prompt,
            system=system_prompt,
            fork=AgentFork.BETA,
            temperature=0.7
        )
        
        # Fallback if LLM fails
        if not response.strip():
            if profile:
                style = profile.get("learning_style", "general")
                level = profile.get("comprehension_level", "intermediate")
                return f"Welcome back! Based on your {style} learning style and {level} level, let's continue learning."
            else:
                return "Hello! I'm SAGE, your adaptive learning assistant. How can I help you learn today?"
                
        return response
    
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
        
        return "completed"