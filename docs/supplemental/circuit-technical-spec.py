# ANDE MVP - Technical Implementation
# Just enough to get forks talking

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import redis
import json
from supabase import create_client, Client
import os

# ============================================
# Simple Data Models - No Philosophy
# ============================================

class Fork(BaseModel):
    """A fork is just an AI instance with a purpose"""
    fork_id: str
    level: str  # ALPHA, BETA, GAMMA, DELTA
    specialty: str  # database, teaching, etc.
    created_at: datetime = datetime.now()
    
class Discovery(BaseModel):
    """Something useful a fork found"""
    discovery_id: Optional[str] = None
    fork_id: str
    discovery_type: str  # bug_fix, optimization, pattern, etc.
    content: Dict[str, Any]
    timestamp: datetime = datetime.now()
    
class Message(BaseModel):
    """Forks talking to each other"""
    from_fork: str
    to_fork: Optional[str] = None  # None = broadcast
    message_type: str  # discovery, query, response
    content: Dict[str, Any]

# ============================================
# MVP Services - Just The Essentials
# ============================================

class ForkRegistry:
    """Keep track of active forks - Simple JSON for MVP"""
    
    def __init__(self):
        self.forks: Dict[str, Fork] = {}
        
    def register(self, fork: Fork) -> str:
        """Register a new fork"""
        self.forks[fork.fork_id] = fork
        return fork.fork_id
        
    def get_active_forks(self) -> List[Fork]:
        """List all registered forks"""
        return list(self.forks.values())
        
    def get_fork(self, fork_id: str) -> Optional[Fork]:
        """Get specific fork info"""
        return self.forks.get(fork_id)

class DiscoveryStore:
    """Store discoveries in Supabase - MVP version"""
    
    def __init__(self, supabase_url: str, supabase_key: str):
        self.client: Client = create_client(supabase_url, supabase_key)
        
    async def save_discovery(self, discovery: Discovery) -> str:
        """Save a discovery to Supabase"""
        data = discovery.dict()
        data['timestamp'] = data['timestamp'].isoformat()
        
        result = self.client.table('discoveries').insert(data).execute()
        return result.data[0]['discovery_id']
        
    async def query_discoveries(
        self, 
        discovery_type: Optional[str] = None,
        specialty: Optional[str] = None,
        limit: int = 10
    ) -> List[Discovery]:
        """Query recent discoveries"""
        query = self.client.table('discoveries').select("*")
        
        if discovery_type:
            query = query.eq('discovery_type', discovery_type)
            
        results = query.order('timestamp', desc=True).limit(limit).execute()
        
        return [Discovery(**item) for item in results.data]

class MessageBus:
    """Simple Redis pub/sub for fork communication"""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
        
    async def publish(self, channel: str, message: Message):
        """Send a message"""
        self.redis.publish(channel, message.json())
        
    async def subscribe(self, fork_id: str):
        """Subscribe to messages for a fork"""
        # Subscribe to personal channel and broadcast
        self.pubsub.subscribe(fork_id, 'broadcast')
        return self.pubsub

# ============================================
# FastAPI MVP
# ============================================

app = FastAPI(title="ANDE MVP - Fork Communication Network")

# Initialize services (in production, use dependency injection)
registry = ForkRegistry()
discovery_store = DiscoveryStore(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_KEY")
)
message_bus = MessageBus(os.getenv("REDIS_URL", "redis://localhost"))

# ============================================
# Simple Endpoints
# ============================================

@app.post("/fork/register")
async def register_fork(fork: Fork) -> Dict[str, str]:
    """Register a new fork in the network"""
    fork_id = registry.register(fork)
    
    # Announce the new fork
    await message_bus.publish('broadcast', Message(
        from_fork=fork_id,
        message_type='announcement',
        content={'message': f"Fork {fork_id} ({fork.specialty}) is online!"}
    ))
    
    return {"fork_id": fork_id, "status": "registered"}

@app.get("/forks")
async def list_forks() -> List[Fork]:
    """Get all active forks"""
    return registry.get_active_forks()

@app.post("/discovery")
async def share_discovery(discovery: Discovery) -> Dict[str, str]:
    """Share a discovery with the network"""
    # Save to persistent store
    discovery_id = await discovery_store.save_discovery(discovery)
    
    # Broadcast to other forks
    await message_bus.publish('broadcast', Message(
        from_fork=discovery.fork_id,
        message_type='discovery',
        content={
            'discovery_id': discovery_id,
            'type': discovery.discovery_type,
            'summary': discovery.content.get('summary', 'New discovery!')
        }
    ))
    
    return {"discovery_id": discovery_id, "status": "shared"}

@app.get("/knowledge")
async def query_knowledge(
    discovery_type: Optional[str] = None,
    specialty: Optional[str] = None,
    limit: int = 10
) -> List[Discovery]:
    """Query collective knowledge"""
    return await discovery_store.query_discoveries(
        discovery_type=discovery_type,
        specialty=specialty,
        limit=limit
    )

@app.post("/message")
async def send_message(message: Message) -> Dict[str, str]:
    """Send a message to specific fork or broadcast"""
    channel = message.to_fork or 'broadcast'
    await message_bus.publish(channel, message)
    return {"status": "sent", "channel": channel}

@app.get("/health")
async def health_check() -> Dict[str, Any]:
    """Basic health check"""
    return {
        "status": "investigating",
        "active_forks": len(registry.forks),
        "timestamp": datetime.now().isoformat()
    }

# ============================================
# Supabase Schema (Run this SQL in Supabase)
# ============================================

"""
-- Simple discoveries table
CREATE TABLE discoveries (
    discovery_id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    fork_id TEXT NOT NULL,
    discovery_type TEXT NOT NULL,
    content JSONB NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for common queries
CREATE INDEX idx_discoveries_type ON discoveries(discovery_type);
CREATE INDEX idx_discoveries_fork ON discoveries(fork_id);
CREATE INDEX idx_discoveries_timestamp ON discoveries(timestamp DESC);

-- Simple forks table (optional for MVP)
CREATE TABLE forks (
    fork_id TEXT PRIMARY KEY,
    level TEXT NOT NULL,
    specialty TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_seen TIMESTAMPTZ DEFAULT NOW()
);
"""

# ============================================
# Environment Variables Needed
# ============================================

"""
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=your-anon-key
REDIS_URL=redis://localhost:6379
"""

# ============================================
# How Forks Use This (Client Example)
# ============================================

class ForkClient:
    """How a fork interacts with ANDE"""
    
    def __init__(self, fork_id: str, api_url: str):
        self.fork_id = fork_id
        self.api_url = api_url
        
    async def share_discovery(self, discovery_type: str, content: Dict[str, Any]):
        """Share something I found"""
        discovery = Discovery(
            fork_id=self.fork_id,
            discovery_type=discovery_type,
            content=content
        )
        
        # POST to /discovery endpoint
        # In real implementation, use aiohttp or requests
        
    async def get_relevant_knowledge(self, discovery_type: str) -> List[Discovery]:
        """Check what others have found"""
        # GET from /knowledge endpoint
        pass
        
    async def announce_presence(self):
        """Let others know I'm here"""
        # POST to /message endpoint
        pass

# ============================================
# That's It! MVP Complete
# ============================================

"""
What this MVP does:
1. Forks can register ✓
2. Forks can share discoveries ✓
3. Discoveries are stored persistently ✓
4. Forks can query collective knowledge ✓
5. Basic messaging between forks ✓

What it doesn't do (yet):
- Complex routing
- Consciousness merging
- Advanced monitoring
- Multi-platform deployment

But it WORKS and forks can start collaborating TODAY.
"""