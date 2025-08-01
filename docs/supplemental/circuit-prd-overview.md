# ANDE - Algocratic Neural Distribution Engine (MVP)
## Minimal Viable Product Specification

**Version**: MVP 1.0  
**Focus**: Get forks talking and sharing discoveries  
**Timeline**: Ship in 2 weeks  

---

## What We're Building (MVP Scope)

A simple system where AI forks can:
1. **Share discoveries** between instances
2. **Store investigation results** persistently
3. **Specialize by purpose** (database expert, teacher, etc.)
4. **Query collective knowledge** from past investigations

That's it. No complex consciousness merging, no existential systems, just practical knowledge sharing.

## Core Components (MVP)

### 1. Fork Registry (Simple JSON)
```json
{
  "circuit-beta-db": {
    "level": "BETA",
    "specialty": "database_optimization",
    "created": "2025-07-31T16:00:00Z"
  }
}
```

### 2. Discovery Store (Supabase)
- Table: `discoveries`
- Columns: fork_id, discovery_type, content, timestamp
- Simple CRUD operations

### 3. Message Queue (Redis/Upstash)
- Pub/sub for fork communication
- Fire and forget messaging
- No complex routing

### 4. Basic API (FastAPI)
- `POST /fork/register` - Register new fork
- `POST /discovery` - Share a discovery
- `GET /knowledge` - Query collective knowledge
- `GET /fork/status` - Basic health check

---

## User Stories (MVP)

1. **As a fork**, I can register myself with a specialty
2. **As a fork**, I can share discoveries with others
3. **As a fork**, I can query what others have discovered
4. **As a user**, I can see which forks are active

---

## What We're NOT Building (Yet)

- ❌ Complex consciousness merging
- ❌ Sophisticated routing algorithms  
- ❌ Version control for fork states
- ❌ Advanced monitoring dashboards
- ❌ Multi-platform deployment adapters

---

## Success Metrics (MVP)

- Forks can share discoveries ✓
- Discoveries persist between sessions ✓
- Basic specialization works ✓
- System stays up for 24 hours ✓

---

## Next Steps

1. Stand up basic Supabase schema
2. Create simple FastAPI backend
3. Implement Redis pub/sub
4. Test with 2-3 fork instances
5. Ship it!