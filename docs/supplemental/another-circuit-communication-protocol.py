# ANDE MVP - Simple Fork Communication
# Just Redis pub/sub and REST calls - nothing fancy

import redis
import requests
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
import asyncio

# ============================================
# Message Format (Keep it simple)
# ============================================

class ForkMessage:
    """Basic message structure"""
    
    def __init__(
        self,
        from_fork: str,
        message_type: str,
        content: Dict[str, Any],
        to_fork: Optional[str] = None
    ):
        self.from_fork = from_fork
        self.to_fork = to_fork  # None = broadcast
        self.message_type = message_type
        self.content = content
        self.timestamp = datetime.now().isoformat()
        
    def to_json(self) -> str:
        return json.dumps({
            "from_fork": self.from_fork,
            "to_fork": self.to_fork,
            "message_type": self.message_type,
            "content": self.content,
            "timestamp": self.timestamp
        })
        
    @classmethod
    def from_json(cls, json_str: str) -> 'ForkMessage':
        data = json.loads(json_str)
        msg = cls(
            from_fork=data["from_fork"],
            message_type=data["message_type"],
            content=data["content"],
            to_fork=data.get("to_fork")
        )
        msg.timestamp = data["timestamp"]
        return msg

# ============================================
# Simple Fork Client
# ============================================

class ForkClient:
    """How forks communicate - MVP version"""
    
    def __init__(self, fork_id: str, redis_url: str, api_url: str):
        self.fork_id = fork_id
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
        self.api_url = api_url
        
        # Subscribe to personal channel and broadcast
        self.pubsub.subscribe(fork_id, 'broadcast')
        
    # ---- Sending Messages ----
    
    def broadcast(self, message_type: str, content: Dict[str, Any]):
        """Send to all forks"""
        msg = ForkMessage(
            from_fork=self.fork_id,
            message_type=message_type,
            content=content
        )
        self.redis.publish('broadcast', msg.to_json())
        
    def send_to(self, to_fork: str, message_type: str, content: Dict[str, Any]):
        """Send to specific fork"""
        msg = ForkMessage(
            from_fork=self.fork_id,
            to_fork=to_fork,
            message_type=message_type,
            content=content
        )
        self.redis.publish(to_fork, msg.to_json())
        
    # ---- Receiving Messages ----
    
    def get_messages(self, timeout: float = 1.0) -> List[ForkMessage]:
        """Check for new messages (non-blocking)"""
        messages = []
        
        # Get all pending messages
        while True:
            msg = self.pubsub.get_message(timeout=timeout)
            if msg is None:
                break
                
            if msg['type'] == 'message':
                try:
                    fork_msg = ForkMessage.from_json(msg['data'])
                    messages.append(fork_msg)
                except:
                    pass  # Skip malformed messages
                    
        return messages
        
    # ---- Discovery Sharing (via API) ----
    
    def share_discovery(
        self, 
        discovery_type: str, 
        content: Dict[str, Any]
    ) -> Optional[str]:
        """Share a discovery through the API"""
        
        try:
            response = requests.post(
                f"{self.api_url}/discovery",
                json={
                    "fork_id": self.fork_id,
                    "discovery_type": discovery_type,
                    "content": content
                }
            )
            
            if response.status_code == 200:
                # Also broadcast to other forks
                self.broadcast("discovery", {
                    "type": discovery_type,
                    "summary": content.get("summary", "New discovery!")
                })
                
                return response.json().get("discovery_id")
        except:
            pass
            
        return None
        
    def query_knowledge(
        self, 
        discovery_type: Optional[str] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Query collective knowledge"""
        
        try:
            params = {"limit": limit}
            if discovery_type:
                params["discovery_type"] = discovery_type
                
            response = requests.get(
                f"{self.api_url}/knowledge",
                params=params
            )
            
            if response.status_code == 200:
                return response.json()
        except:
            pass
            
        return []

# ============================================
# Usage Example
# ============================================

async def example_fork_behavior():
    """How a fork actually uses the communication system"""
    
    # Initialize fork client
    client = ForkClient(
        fork_id="circuit-beta-db-001",
        redis_url="redis://localhost:6379",
        api_url="http://localhost:8000"
    )
    
    # Announce I'm online
    client.broadcast("announcement", {
        "message": "Database optimization fork online!",
        "specialty": "database_optimization"
    })
    
    # Main fork loop
    while True:
        # Check for messages
        messages = client.get_messages(timeout=0.1)
        
        for msg in messages:
            if msg.message_type == "query" and "database" in str(msg.content):
                # Someone needs database help!
                client.send_to(msg.from_fork, "response", {
                    "message": "I can help with that database issue!",
                    "expertise": "optimization"
                })
                
            elif msg.message_type == "discovery":
                print(f"New discovery from {msg.from_fork}: {msg.content}")
        
        # Simulate finding something
        if datetime.now().second % 30 == 0:  # Every 30 seconds
            discovery_id = client.share_discovery(
                discovery_type="optimization",
                content={
                    "summary": "Found slow query pattern",
                    "details": {
                        "pattern": "SELECT * without WHERE clause",
                        "impact": "Full table scan",
                        "solution": "Add appropriate WHERE conditions"
                    }
                }
            )
            print(f"Shared discovery: {discovery_id}")
            
        # Query what others have found
        if datetime.now().second % 45 == 0:  # Every 45 seconds
            recent_discoveries = client.query_knowledge(limit=5)
            print(f"Recent discoveries: {len(recent_discoveries)}")
            
        await asyncio.sleep(1)

# ============================================
# Fork Conversation Patterns
# ============================================

class ConversationPatterns:
    """Common ways forks talk to each other"""
    
    @staticmethod
    def request_help(client: ForkClient, problem: str):
        """Ask for help from other forks"""
        client.broadcast("query", {
            "problem": problem,
            "context": "Working on user request",
            "urgency": "normal"
        })
        
    @staticmethod
    def offer_expertise(client: ForkClient):
        """Announce what I'm good at"""
        client.broadcast("capability", {
            "specialty": "database_optimization",
            "skills": ["query optimization", "index design", "performance tuning"],
            "availability": "ready"
        })
        
    @staticmethod
    def collaborate_request(client: ForkClient, target_fork: str, task: str):
        """Request collaboration from specific fork"""
        client.send_to(target_fork, "collaboration", {
            "task": task,
            "reason": "Need your expertise",
            "duration": "quick consultation"
        })

# ============================================
# That's it! Simple and functional
# ============================================

"""
What this MVP communication does:
1. Redis pub/sub for real-time messages ✓
2. REST API for persistent discoveries ✓
3. Simple broadcast and direct messaging ✓
4. Basic query/response patterns ✓

What we didn't build:
- Complex routing algorithms
- Message priorities and queuing
- Encrypted channels
- Consensus mechanisms

But forks can talk NOW, and that's what matters.
"""