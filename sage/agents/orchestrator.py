"""Assistance Orchestrator Agent - Coordinates all other agents."""

import yaml
from typing import Dict, Any
from sage.core.base import Node, SharedStore
from sage.core.llm import llm_manager
from sage.core.persistence import AgentFork


class AssistanceOrchestratorNode(Node):
    """Central coordinator for all agents."""
    
    def prep(self, shared: SharedStore) -> Dict[str, Any]:
        """Gather current state and context."""
        return {
            "student_request": shared.get("student_input", ""),
            "current_state": shared.get("learning_state", "initial"),
            "available_agents": ["profile", "adapt", "question", "progress", "respond"],
            "student_id": shared.get("current_student", "default_student"),
            "has_profile": self._has_profile(shared),
            "topic": shared.get("topic", "general")
        }
    
    def exec(self, data: Dict[str, Any]) -> str:
        """Determine next agent to activate."""
        # Simple logic for MVP - can be enhanced with LLM later
        
        # If no student input and we're in interacting state, end the flow
        if not data["student_request"] and data["current_state"] == "interacting":
            return "end"
        
        # If no profile exists, create one first
        if not data["has_profile"]:
            return "profile"
        
        # If student made a direct request
        if data["student_request"]:
            request_lower = data["student_request"].lower()
            
            # Check for specific intents
            if any(word in request_lower for word in ["test", "quiz", "assess"]):
                return "question"
            elif any(word in request_lower for word in ["explain", "help", "understand"]):
                return "adapt"
            elif any(word in request_lower for word in ["progress", "how am i doing"]):
                return "progress"
            else:
                # For now, respond directly
                return "respond"
        
        # Default flow based on state
        if data["current_state"] == "initial":
            return "profile"
        elif data["current_state"] == "learning":
            return "adapt"
        else:
            return "respond"
    
    def post(self, shared: SharedStore, prep_res: Dict[str, Any], exec_res: str) -> str:
        """Update state and return next agent."""
        shared["next_agent"] = exec_res
        
        # Update learning state based on decision
        state_map = {
            "profile": "profiling",
            "adapt": "learning",
            "question": "assessing",
            "progress": "reviewing",
            "respond": "interacting"
        }
        
        shared["learning_state"] = state_map.get(exec_res, "active")
        
        # Log orchestration decision
        if "logs" not in shared._store:
            shared["logs"] = []
        shared["logs"].append({
            "agent": "Orchestrator",
            "decision": exec_res,
            "reason": f"Based on state: {prep_res['current_state']}, request: {prep_res['student_request'][:50]}..."
        })
        
        return exec_res
    
    def _has_profile(self, shared: SharedStore) -> bool:
        """Check if current student has a profile."""
        profiles = shared.get("student_profiles", {})
        student_id = shared.get("current_student", "default_student")
        return student_id in profiles