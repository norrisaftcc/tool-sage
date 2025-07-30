# tool-sage
Scholar's Adaptive Growth Engine

An adaptive learning assistant system built with a minimalist multi-agent architecture.

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/norrisaftcc/tool-sage.git
cd tool-sage

# Install in development mode
pip install -e ".[dev]"
```

### Usage

Start an interactive learning session:

```bash
sage learn
```

Run with specific student ID and topic:

```bash
sage learn -s student123 -t mathematics
```

Test the system:

```bash
sage test
```

## Architecture

SAGE uses a multi-agent system where specialized agents collaborate:

- **Orchestrator Agent**: Coordinates all other agents
- **Learning Profile Agent**: Analyzes student learning patterns
- **Response Generator**: Creates personalized responses
- More agents coming soon!

## Development

The system is built on a minimalist framework inspired by PocketFlow, with three core abstractions:

- `Node`: Individual agent logic
- `SharedStore`: Central state management
- `Flow`: Agent coordination and execution

See `sage_design_doc.md` for detailed architecture information.