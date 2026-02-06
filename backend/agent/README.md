# Text Diagrams Agent

Hybrid DSPy + FastAgent diagram generation system for creating technical diagrams from natural language.

## Overview

This agent module combines:

- **DSPy** for structured LLM prompting and optimization
- **FastAgent** for MCP tool access (Python diagrams and Mermaid rendering)

The result is a more reliable, consistent, and optimizable diagram generation system compared to pure prompt engineering.

## Architecture

```
User Request
    ↓
DiagramRouterModule (DSPy)  ← Decides: Python diagrams or Mermaid?
    ↓
┌───────────────┬───────────────┐
│ PythonGenerator│ MermaidGenerator│ (DSPy + Validation)
└───────────────┴───────────────┘
    ↓
MCP Tool Call (FastAgent)  ← Renders diagram, saves to GCS
    ↓
AgentResult (title, URI, history)
```

## Installation

From the `backend` directory:

```bash
# Install in editable mode
uv pip install -e agent

# Or use task command
task agent:sync
```

## Usage

### Basic Usage

```python
from agent import agent
import asyncio

# Generate a diagram
result = asyncio.run(agent("Create a 3-tier web app architecture on AWS"))

print(result.diagram_title)  # "Three-Tier Web Application Architecture"
print(result.media_uri)      # "gs://bucket/diagrams/abc123.png"
print(result.history_json)   # Conversation history as JSON
```

### With Conversation History

```python
# First request
result1 = asyncio.run(agent("Create AWS architecture"))

# Follow-up request with history
result2 = asyncio.run(
    agent(
        "Add a caching layer",
        previous_history_json=result1.history_json
    )
)
```

### Error Handling

```python
from agent import agent, ClarificationNeeded, CodeGenerationError

try:
    result = await agent("Create a diagram")
except ClarificationNeeded as e:
    # Ask user for clarification
    print(f"Please clarify: {e.clarification_question}")
except CodeGenerationError as e:
    # Code generation failed after retries
    print(f"Error: {e}")
    print(f"Validation errors: {e.validation_errors}")
```

## Module Structure

```
src/agent/
├── __init__.py              # Public API
├── config.py                # LM provider configuration
├── utils.py                 # Utility functions
├── exceptions.py            # Error classes
├── core/
│   ├── router.py            # DiagramRouterModule (DSPy)
│   ├── python_gen.py        # PythonDiagramsGenerator (DSPy)
│   ├── mermaid_gen.py       # MermaidGenerator (DSPy)
│   ├── validators.py        # Code validation
│   └── agent_orchestrator.py # Main orchestration logic
├── signatures/
│   ├── router_sig.py        # DSPy signature for router
│   ├── python_sig.py        # DSPy signature for Python generator
│   └── mermaid_sig.py       # DSPy signature for Mermaid generator
└── optimization/            # Future: DSPy optimization
```

## Development

### Running Tests

```bash
# All tests
task agent:test

# Unit tests only (fast, mocked LM)
task agent:test:unit

# Integration tests (requires live MCP server)
task agent:test:integration

# Watch mode
task agent:test:watch
```

### Code Quality

```bash
# Format code
task agent:fmt

# Check code quality
task agent:check
```

### LM Provider Configuration

The agent uses configurable LM providers defined in `config/lm_providers.yaml`:

```yaml
providers:
  gemini-flash:  # Default
    model: "gemini/gemini-2.0-flash-exp"
    max_tokens: 2000
    temperature: 0.7
    default: true

  gemini-pro:
    model: "gemini/gemini-2.5-pro-latest"
    max_tokens: 2000
    temperature: 0.7
```

To use a different provider in code:

```python
from agent.core import DiagramRouterModule

# Use default (gemini-flash)
router = DiagramRouterModule()

# Use specific provider
router = DiagramRouterModule(lm_provider="gemini-pro")
```

## Optimization (Future)

The agent is designed to be optimized with DSPy's compilation features:

```bash
# After collecting 100+ production examples
task agent:optimize

# Optimize specific modules
task agent:optimize:router
```

Optimization workflow:

1. **Collect data**: Production examples stored in `data/collected_examples/`
1. **Define metrics**: Quality metrics in `optimization/metrics.py`
1. **Compile**: Run DSPy optimizers (BootstrapFewShot, MIPROv2)
1. **Deploy**: Optimized prompts saved to `data/optimized_prompts/`

## Key Design Decisions

### 1. Why DSPy?

- **Structured prompting**: Signatures enforce consistent input/output
- **Optimization**: Automatically improve prompts with production data
- **Validation**: Built-in retry logic with feedback
- **Testing**: Easy to mock and test

### 2. Why Keep FastAgent?

- **MCP connectivity**: Maintains access to diagram rendering tools
- **Message history**: Preserves conversation context
- **Infrastructure**: Proven deployment setup

### 3. Hybrid Approach

- **DSPy handles intelligence**: Routing, code generation, validation
- **FastAgent handles execution**: MCP tool calls, history management
- **Best of both worlds**: Structured AI + proven infrastructure

## Comparison to Old Agent

| Aspect         | Old Agent                        | New Agent                     |
| -------------- | -------------------------------- | ----------------------------- |
| Prompts        | 418-line manual instruction      | Structured DSPy signatures    |
| Validation     | None (exec with no checks)       | AST + forbidden ops checks    |
| Error handling | Silent failures (`except: pass`) | Explicit exceptions           |
| Optimization   | Manual prompt tuning             | Automated DSPy compilation    |
| Testing        | Hard to test (live LM calls)     | Easy to test (mocked modules) |
| Consistency    | "Vibe coding"                    | Structured predictions        |

## Troubleshooting

### Import Error: `No module named 'agent'`

```bash
# Install in editable mode
cd backend
uv pip install -e agent
```

### DSPy LM Connection Error

Ensure `GOOGLE_API_KEY` environment variable is set:

```bash
export GOOGLE_API_KEY="your-key-here"
```

### MCP Connection Error

Ensure `MCP_SERVICE_URL` environment variable points to the MCP service:

```bash
export MCP_SERVICE_URL="http://localhost:8080"
```

## Contributing

1. Make changes to modules in `src/agent/`
1. Add tests in `tests/unit/` or `tests/integration/`
1. Run `task agent:fmt` to format code
1. Run `task agent:test` to verify tests pass
1. Update this README if adding new features

## License

Same as parent project.
