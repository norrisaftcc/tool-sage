"""Content Adaptation Agent - Adjusts content based on student state and sentiment."""

from typing import Dict, Any, List, Tuple
from sage.core.base import Node, SharedStore
from sage.core.llm import llm_manager
from sage.core.persistence import AgentFork


class ContentAdaptationNode(Node):
    """Adapts learning content based on student profile, progress, and emotional state."""
    
    # Sentiment keywords for basic analysis
    POSITIVE_SIGNALS = [
        "great", "awesome", "understand", "got it", "makes sense", "cool",
        "interesting", "fun", "easy", "clear", "thanks", "helpful", "yes"
    ]
    
    NEGATIVE_SIGNALS = [
        "confused", "lost", "hard", "difficult", "don't understand", "help",
        "frustrat", "stuck", "overwhelm", "complicated", "tired", "bored",
        "don't", "can't", "unable", "struggling"
    ]
    
    NEUTRAL_SIGNALS = [
        "ok", "okay", "sure", "alright", "continue", "next", "go on"
    ]
    
    # System prompt for adaptation decisions
    SYSTEM_PROMPT = """You are an expert learning content adapter. Based on the student's emotional state, 
    profile, and recent interactions, determine how to adjust the content delivery. Be highly responsive 
    to frustration or confusion, and celebrate successes."""
    
    def prep(self, shared: SharedStore) -> Dict[str, Any]:
        """Gather context for content adaptation."""
        student_id = shared.get("current_student", "default_student")
        profiles = shared.get("student_profiles", {})
        
        # Get recent conversation for sentiment analysis
        conversation = shared.get("conversation", [])
        recent_messages = conversation[-5:] if len(conversation) > 5 else conversation
        
        return {
            "student_id": student_id,
            "profile": profiles.get(student_id, {}),
            "recent_messages": recent_messages,
            "current_topic": shared.get("topic", "general"),
            "last_input": shared.get("student_input", ""),
            "assessment_results": shared.get("last_assessment_result", None)
        }
    
    def exec(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze sentiment and determine content adaptations."""
        # First, do basic sentiment analysis
        sentiment = self._analyze_sentiment(data["last_input"])
        recent_sentiment = self._analyze_conversation_sentiment(data["recent_messages"])
        
        # Build adaptation context
        profile = data["profile"]
        learning_style = profile.get("learning_style", "general")
        comprehension_level = profile.get("comprehension_level", "intermediate")
        
        # Create adaptation prompt
        adaptation_prompt = f"""
        Student Profile:
        - Learning Style: {learning_style}
        - Comprehension Level: {comprehension_level}
        - Current Topic: {data["current_topic"]}
        
        Emotional Context:
        - Current Sentiment: {sentiment}
        - Recent Trend: {recent_sentiment}
        - Last Message: "{data["last_input"]}"
        
        Based on this context, provide specific adaptations in the following format:
        
        pace: [slower/maintain/faster]
        complexity: [decrease/maintain/increase]
        style: [more_visual/more_examples/more_practice/maintain]
        emotional_support: [high/medium/low]
        next_action: [review/continue/challenge/break]
        message_tone: [encouraging/neutral/celebratory]
        
        Also provide a brief explanation of your reasoning.
        """
        
        # Use Beta-level model for adaptation decisions
        response = llm_manager.generate(
            prompt=adaptation_prompt,
            system=self.SYSTEM_PROMPT,
            fork=AgentFork.BETA,
            temperature=0.5
        )
        
        # Parse the response into structured adaptations
        adaptations = self._parse_adaptations(response)
        adaptations["sentiment"] = sentiment
        adaptations["sentiment_trend"] = recent_sentiment
        
        return adaptations
    
    def post(self, shared: SharedStore, prep_res: Dict[str, Any], exec_res: Dict[str, Any]) -> str:
        """Apply adaptations to shared store."""
        # Store adaptation decisions
        shared["current_adaptations"] = exec_res
        
        # Log the adaptation
        if "logs" not in shared._store:
            shared["logs"] = []
        
        shared["logs"].append({
            "agent": "ContentAdapter",
            "sentiment": exec_res["sentiment"],
            "adaptations": exec_res
        })
        
        # Generate adapted content based on decisions
        self._generate_adapted_content(shared, exec_res)
        
        # After adaptation, go to responder
        return "respond"
    
    def _analyze_sentiment(self, text: str) -> str:
        """Basic sentiment analysis of a single message."""
        if not text:
            return "neutral"
            
        text_lower = text.lower()
        
        # Count sentiment signals with special handling for phrases
        positive_count = sum(1 for word in self.POSITIVE_SIGNALS if word in text_lower)
        negative_count = sum(1 for word in self.NEGATIVE_SIGNALS if word in text_lower)
        
        # Special case: "don't understand" is strongly negative
        if "don't understand" in text_lower or "do not understand" in text_lower:
            negative_count += 2
            
        # Determine sentiment
        if negative_count > positive_count:
            return "negative"
        elif positive_count > negative_count:
            return "positive"
        else:
            return "neutral"
    
    def _analyze_conversation_sentiment(self, messages: List[Dict]) -> str:
        """Analyze sentiment trend over recent messages."""
        if not messages:
            return "neutral"
            
        sentiments = []
        for msg in messages:
            if msg.get("role") == "student":
                sentiment = self._analyze_sentiment(msg.get("content", ""))
                sentiments.append(sentiment)
        
        if not sentiments:
            return "neutral"
            
        # Simple trend analysis - look at the progression
        if len(sentiments) >= 2:
            # Check if sentiment is getting worse
            if sentiments[-1] == "negative" and sentiments[-2] != "negative":
                return "declining"
            # Check if sentiment is improving  
            elif sentiments[-1] == "positive" and sentiments[-2] != "positive":
                return "improving"
        
        # Otherwise check overall balance
        negative_count = sentiments.count("negative")
        positive_count = sentiments.count("positive")
        
        if negative_count > positive_count:
            return "declining"
        elif positive_count > negative_count:
            return "improving"
        else:
            return "stable"
    
    def _parse_adaptations(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into structured adaptations."""
        # Default adaptations
        adaptations = {
            "pace": "maintain",
            "complexity": "maintain",
            "style": "maintain",
            "emotional_support": "medium",
            "next_action": "continue",
            "message_tone": "neutral",
            "reasoning": response
        }
        
        # Try to extract structured values from response
        response_lower = response.lower()
        
        # Extract pace
        if "slower" in response_lower:
            adaptations["pace"] = "slower"
        elif "faster" in response_lower:
            adaptations["pace"] = "faster"
            
        # Extract complexity
        if "decrease" in response_lower or "simpl" in response_lower:
            adaptations["complexity"] = "decrease"
        elif "increase" in response_lower or "challeng" in response_lower:
            adaptations["complexity"] = "increase"
            
        # Extract emotional support
        if "high" in response_lower and "support" in response_lower:
            adaptations["emotional_support"] = "high"
        elif "low" in response_lower and "support" in response_lower:
            adaptations["emotional_support"] = "low"
            
        # Extract next action
        if "review" in response_lower:
            adaptations["next_action"] = "review"
        elif "break" in response_lower:
            adaptations["next_action"] = "break"
        elif "challenge" in response_lower:
            adaptations["next_action"] = "challenge"
            
        # Extract tone
        if "encourag" in response_lower:
            adaptations["message_tone"] = "encouraging"
        elif "celebrat" in response_lower:
            adaptations["message_tone"] = "celebratory"
            
        return adaptations
    
    def _generate_adapted_content(self, shared: SharedStore, adaptations: Dict[str, Any]):
        """Generate content based on adaptation decisions."""
        # This will be expanded later, for now just set a flag
        shared["content_adapted"] = True
        
        # Create a simple adapted message based on sentiment
        if adaptations["sentiment"] == "negative":
            if adaptations["emotional_support"] == "high":
                shared["adapted_content"] = """I can see this might be challenging. Let's take a step back 
and approach it differently. Remember, everyone learns at their own pace, and it's perfectly 
okay to find things difficult at first. What specific part would you like me to clarify?"""
            else:
                shared["adapted_content"] = "Let me explain this in a different way."
        
        elif adaptations["sentiment"] == "positive":
            if adaptations["message_tone"] == "celebratory":
                shared["adapted_content"] = "Fantastic work! You're really getting the hang of this. Ready for the next challenge?"
            else:
                shared["adapted_content"] = "Great! Let's keep going."
        
        else:
            shared["adapted_content"] = ""