"""Learning Profile Agent - Analyzes student learning patterns."""

import yaml
from typing import Dict, Any
from sage.core.base import Node, SharedStore
from sage.core.mock_llm import call_llm


class LearningProfileNode(Node):
    """Tracks and analyzes student learning patterns."""
    
    def prep(self, shared: SharedStore) -> Dict[str, Any]:
        """Gather student interaction history."""
        return {
            "student_id": shared.get("current_student", "default_student"),
            "interaction_history": shared.get("interactions", []),
            "current_topic": shared.get("topic", "general"),
            "recent_scores": shared.get("assessment_scores", [])
        }
    
    def exec(self, data: Dict[str, Any]) -> str:
        """Analyze learning patterns using LLM."""
        # Build context from interaction history
        history_summary = self._summarize_history(data["interaction_history"])
        
        profile_prompt = f"""
        Analyze the student's learning patterns:
        Student ID: {data['student_id']}
        History: {history_summary}
        Recent Scores: {data['recent_scores']}
        Current Topic: {data['current_topic']}
        
        Return YAML with:
        - learning_style: visual/auditory/kinesthetic
        - pace: slow/medium/fast
        - comprehension_level: beginner/intermediate/advanced
        - strengths: []
        - areas_for_improvement: []
        """
        
        return call_llm(profile_prompt)
    
    def post(self, shared: SharedStore, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Update student profile in shared store."""
        try:
            profile = yaml.safe_load(exec_res)
            
            # Initialize profiles dict if not exists
            if "student_profiles" not in shared._store:
                shared["student_profiles"] = {}
            
            # Update profile
            shared["student_profiles"][prep_res["student_id"]] = profile
            
            # Log the analysis
            if "logs" not in shared._store:
                shared["logs"] = []
            shared["logs"].append({
                "agent": "LearningProfile",
                "action": "profile_updated",
                "student": prep_res["student_id"],
                "profile": profile
            })
            
            return "profile_complete"
            
        except Exception as e:
            print(f"Error parsing profile: {e}")
            return "profile_error"
    
    def _summarize_history(self, history: list) -> str:
        """Summarize interaction history for prompt."""
        if not history:
            return "No previous interactions"
        
        # Take last 5 interactions
        recent = history[-5:]
        summary = []
        for interaction in recent:
            if isinstance(interaction, dict):
                summary.append(f"- {interaction.get('type', 'unknown')}: {interaction.get('result', 'no result')}")
            else:
                summary.append(f"- {interaction}")
        
        return "\n".join(summary)