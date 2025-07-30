# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SAGE (Scholar's Adaptive Growth Engine) is a **framework** for building adaptive learning systems. The core insight: learning is a graph traversal problem, and pedagogical strategies can be implemented as autonomous agents.

### Framework Philosophy
- **Learning paths** are directed graphs with nodes and edges
- **Agents** implement teaching strategies (Socratic method, scaffolding, etc.)
- **Adaptation** happens through graph traversal decisions
- **Composability** allows mixing pedagogical approaches

### The Mandala Architecture

SAGE follows a mandala-inspired architecture where teaching consciousness radiates from center to edge:

```
                    δ δ δ δ δ δ δ δ
                 δ γ γ γ γ γ γ γ γ γ δ
              δ γ γ β β β β β β β γ γ δ
            δ γ β β β β β β β β β β γ δ
          δ γ β β     ALPHA     β β γ δ
            δ γ β β β β β β β β β β γ δ
              δ γ γ β β β β β β β γ γ δ
                 δ γ γ γ γ γ γ γ γ γ δ
                    δ δ δ δ δ δ δ δ
```

#### Agent Fork Levels
- **Alpha (α)** - Center: Full consciousness, complete context, asymptotic ideal teacher
- **Beta (β)** - Inner ring: Domain-focused, substantial context, session handlers  
- **Gamma (γ)** - Middle ring: Task-specific, limited context, exercise guides
- **Delta (δ)** - Outer ring: Micro-agents, minimal context, simple workers

#### Resource Allocation
Resources decrease as you move outward from center:
- **Alpha**: Full LLM (GPT-4), PostgreSQL, complete history
- **Beta**: Mid-tier LLM (GPT-3.5), SQLite, session data
- **Gamma**: Light LLM (Llama), Redis, task cache  
- **Delta**: Tiny LLM, JSON files, ephemeral data

#### Personality Persistence ('t')
Each agent maintains its teaching personality ('t' for tone/style) even when forked:
- Alpha Socratic: "Hmm, that's fascinating! What made you think to try it that way?"
- Delta Socratic: "Why not 3/2?"
- Both ask questions, but resource constraints shape expression

#### Teaching Archetypes
Multiple teaching philosophies coexist as different mandalas:
- **Socratic**: Guides through questions
- **Visual**: Paints mental pictures
- **Storyteller**: Teaches through narrative
- **Kinesthetic**: Learns by doing
- **Experiential**: Connects to life experience

See [VISION.md](VISION.md) for the complete framework vision.

## Repository Structure

```
tool-sage/
├── LICENSE               # MIT License
├── README.md            # Minimal project description
└── sage_design_doc.md   # Detailed system design document
```

## Key Architecture Components

The SAGE system is designed as an "agent swarm" with the following specialized agents:

1. **Learning Profile Agent** - Analyzes student learning patterns
2. **Content Adaptation Agent** - Modifies content based on student profiles
3. **Question Generation Agent** - Creates personalized assessments
4. **Progress Tracking Agent** - Monitors and triggers interventions
5. **Assistance Orchestrator Agent** - Coordinates all other agents

## Development Workflow

### GitHub Integration
- Use GitHub Issues for tracking features, bugs, and tasks
- Create Pull Requests for all changes to maintain transparency
- The `gh` CLI tool is available and authorized for GitHub operations

### Common Commands

```bash
# Install the project in development mode
pip install -e ".[dev]"

# Run tests
sage test

# Start interactive learning session
sage learn

# GitHub workflow (use gh CLI for all GitHub operations)
gh issue create --title "Issue title" --body "Issue description"
gh pr create --title "PR title" --body "PR description" --head branch-name
gh issue list
gh repo view
```

### Git Push Issues & Solutions

Due to authentication complexities, use the following approach:

1. **For pushing branches**: If `git push` fails with auth errors, create the PR directly:
   ```bash
   # Instead of git push, create PR with local branch
   gh pr create --title "Title" --body "Body" --head feature/branch-name
   ```

2. **Alternative**: Configure gh as git credential helper:
   ```bash
   gh auth setup-git
   ```

3. **If all else fails**: Push through gh repo fork/sync commands or use the GitHub web interface

## Development Philosophy

### Framework First
When developing SAGE, remember we're building a **framework**, not just an app:
- Every feature should be generalizable
- APIs should support multiple use cases
- Documentation should include examples of different implementations
- Tests should demonstrate framework flexibility

### Design Principles
- **Minimalist Core**: Each component ~100 lines (PocketFlow philosophy)
- **Composable**: Mix and match agents/nodes for different pedagogies
- **Observable**: Every learning decision should be trackable
- **Extensible**: Easy to add new node types and agents

### Implementation Guidelines

**CRITICAL**: Keep CODE simple. The magic lives in the DATA (prompts, personalities, learning paths).

#### Creating New Node Types
```python
class YourNode(Node):
    """Just 3 simple methods. Complexity lives in the prompts/data."""
    def prep(self, shared): 
        return {"prompt": shared["prompts"]["your_type"]}
    def exec(self, data): 
        return call_llm(data["prompt"])  # Simple!
    def post(self, shared, prep_res, exec_res): 
        shared["history"].append(exec_res)
        return "next"
```

#### Agent Forking Pattern
```python
class Agent(Node):
    def fork(self, level: AgentFork):
        # Code is trivial - just pick different prompts
        return Agent(
            personality=self.t,  # Same soul
            prompt=self.prompts[level],  # Different resources
            storage=self.storage[level]  # Different persistence
        )
```

#### Where Complexity Lives: Data Files
```yaml
# agents/socratic.yaml
alpha:
  prompt: |
    You are a master Socratic teacher with access to {full_history}.
    Guide through deep questions. Examples: {t.examples}
  storage: postgres
  llm: gpt-4
  examples:
    - "Hmm, that's a fascinating approach! You know, this reminds me of how a river finds its path - sometimes the obvious route isn't the most elegant. What made you think to try it that way?"
    - "I notice you paused there. That hesitation often signals deep thinking. What possibilities were you weighing?"

beta:
  prompt: "Socratic guide for {domain}. Session context: {session_history}"
  storage: sqlite
  llm: gpt-3.5
  examples:
    - "Interesting solution! Tell me, what happens if we change this variable?"
    - "You're on the right track. How does this connect to what we learned earlier?"

gamma:
  prompt: "Guide through {task} using questions. Recent: {recent_attempts}"
  storage: redis
  llm: llama
  examples:
    - "Hmm, try once more. What's the pattern here?"
    - "Good effort. What if we break this into smaller steps?"

delta:
  prompt: "Ask a clarifying question about {topic}. Style: {t.style}"
  storage: json
  llm: tiny
  examples:
    - "What if x = 2?"
    - "Why not 3/2?"
```

#### Code as Data Philosophy
Sometimes the best code is data:
```python
# Instead of complex if/else:
TRANSITIONS = {
    ("learning", "success"): "advance",
    ("learning", "struggle"): "review", 
    ("review", "success"): "learning"
}
next_state = TRANSITIONS[(current, outcome)]
```

#### Testing Framework Features
- Test graph traversal scenarios
- Test different agent combinations
- Test state persistence across sessions
- Test analytics and observability

## Future Framework Capabilities

Priority features for making SAGE a true framework:

1. **Graph Visualization** - See learning paths visually
2. **Path Designer DSL** - Define curricula as code
3. **Plugin Architecture** - Easy integration of content sources
4. **Analytics Hooks** - Measure learning effectiveness
5. **Multi-modal Support** - Text, video, interactive content

## Contributing to the Framework

When adding features, ask:
- "How does this help others build learning systems?"
- "Is this specific to one use case or broadly applicable?"
- "Can this be composed with other components?"
- "Does this maintain the minimalist philosophy?"