# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SAGE (Scholar's Adaptive Growth Engine) is a **framework** for building adaptive learning systems. The core insight: learning is a graph traversal problem, and pedagogical strategies can be implemented as autonomous agents.

### Framework Philosophy
- **Learning paths** are directed graphs with nodes and edges
- **Agents** implement teaching strategies (Socratic method, scaffolding, etc.)
- **Adaptation** happens through graph traversal decisions
- **Composability** allows mixing pedagogical approaches

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

#### Creating New Node Types
```python
class YourNode(Node):
    """Represents a specific learning activity."""
    def prep(self, shared): # Gather needed data
    def exec(self, data): # Perform the activity
    def post(self, shared, prep_res, exec_res): # Update state & decide next
```

#### Creating New Agents
```python
class YourAgent(Node):
    """Implements a pedagogical strategy."""
    # Agents are just specialized nodes that make decisions
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