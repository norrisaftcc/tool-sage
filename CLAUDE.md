# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Tool-SAGE (Scholar's Adaptive Growth Engine) is an adaptive learning assistant system design project. The repository currently contains design documentation for a multi-agent learning system based on PocketFlow's minimalist architecture.

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

Since this is currently a documentation-only repository with no code implementation yet, there are no build, test, or lint commands. When implementing the system:

```bash
# Create a new issue
gh issue create --title "Issue title" --body "Issue description"

# Create a pull request
gh pr create --title "PR title" --body "PR description"

# List open issues
gh issue list

# View repository status
gh repo view
```

## Design Philosophy

The system follows PocketFlow's minimalist principles:
- Each agent should be simple and focused (aim for ~100 lines)
- Use composition over complexity
- All state is shared through a central store
- Agents communicate via message queues
- Async parallel processing for scalability

## Implementation Notes

When implementing this design:
1. Start with the core Node/Flow/SharedStore abstractions
2. Implement one agent at a time, testing in isolation
3. Build the orchestrator last to coordinate proven agents
4. Use YAML for configuration and inter-agent communication
5. Leverage async/await for parallel operations

## Future Development

The design document outlines potential extensions:
- Peer Learning Agent
- Resource Recommendation Agent
- Parent/Teacher Dashboard Agent
- Gamification Agent

Each new agent should follow the established patterns and integrate through the shared store mechanism.