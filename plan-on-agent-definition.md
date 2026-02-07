# Implementation Plan: FastAgent-Powered DspyAgent Interface

## Overview

Create a new `agent.py` file that wraps `DspyAgent` with FastAgent's `fast.custom()` decorator, providing a simple interface for diagram generation with conversation history management.

## Goals

1. Create a new FastAgent app that uses DspyAgent as the agent runner
1. Define an `agent` function with the interface: `agent(user_instruction, previous_history_json) -> AgentResult`
1. Implement logic: load history → run DspyAgent → extract results from internal state → return history
1. Add interactive mode for CLI testing with `if __name__ == "__main__"`
1. Replace the old `agent_orchestrator.py` approach

## Architecture

```
FastAgent App
  └── fast.custom(DspyAgent, config)
      └── DspyAgent (McpAgent) [with custom run() method]
          ├── DiagramRouter (main_module)
          │   ├── Classifier (ChainOfThought)
          │   ├── Routes to specialists
          │   └── Fallback module (for unhandleable requests)
          ├── TechnicalDiagramAgent (ReAct)
          │   └── Uses draw_technical_diagram tool
          ├── MermaidDiagramAgent (ReAct)
          │   └── Uses draw_mermaid tool
          └── FallbackAgent
              └── Returns error/clarification message
```

## Key Design Changes (Per User Feedback)

1. **Load history into DspyAgent** if available
1. **Custom `run()` method** on DspyAgent that:
   - Formats input to DSPy-compatible format
   - Runs the main_module
   - Returns the output
1. **Agent function inspects history** to:
   - Get latest function call result (if NEW one exists)
   - Return tool result OR string response
1. **Fallback module** for requests that cannot be fulfilled

## Critical Files

### To Create

- **`/home/chris/projects/text-diagrams/backend/agent/src/agent/agent.py`** - New main agent file with FastAgent wrapper

### To Modify

- **`/home/chris/projects/text-diagrams/backend/agent/src/agent/__init__.py`** - Update imports to use new agent.py

### To Reference/Copy From

- **`/home/chris/projects/text-diagrams/backend/agent/src/agent/fastagent/dspy_agent.py`** - Copy DiagramRouter class (lines 296-382) and module configs (lines 384-409)
- **`/home/chris/projects/text-diagrams/backend/agent/src/agent/core/agent_orchestrator.py`** - Reference for AgentResult model and interface pattern

### To Remove (Later)

- **`/home/chris/projects/text-diagrams/backend/agent/src/agent/core/agent_orchestrator.py`** - Old orchestrator (remove after migration)

## Implementation Steps

### 1. Create New agent.py File

**Location**: `/home/chris/projects/text-diagrams/backend/agent/src/agent/agent.py`

**Structure**:

```python
"""FastAgent-powered diagram generation using DspyAgent.

This module provides a simple interface for diagram generation:
- Loads conversation history
- Routes requests through DspyAgent's intelligent router
- Extracts results from tool execution
- Returns updated history for multi-turn conversations
"""

import json
import uuid
from pathlib import Path
from typing import Optional

import dspy
from fast_agent import FastAgent
from fast_agent.agents import AgentConfig
from fast_agent.mcp.prompt_serialization import from_json, to_json
from pydantic import BaseModel, Field

from agent.exceptions import ClarificationNeeded, CodeGenerationError, MCPToolError
from agent.fastagent.dspy_agent import DspyAgent, DspyFastAgentConfig, DspyModuleArgs


# Configuration paths
CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / "fastagent.config.yaml"

# Initialize FastAgent
fast = FastAgent(
    "Diagramming Agent",
    config_path=CONFIG_PATH,
)


# AgentResult model (keep compatible with Django views)
class AgentResult(BaseModel):
    """Complete result including response and updated history."""

    diagram_title: str = Field(
        ...,
        description="Title of the diagram (5-8 words)",
    )
    media_uri: str = Field(
        ...,
        description="GCS URI of the generated diagram"
    )
    history_json: str = Field(
        ...,
        description="Serialized conversation history for multi-turn"
    )


# Copy DiagramRouter class from dspy_agent.py (lines 296-382)
class DiagramRouter(dspy.Module):
    # ... [full implementation]
    pass


# DspyAgent configuration builder
def _create_dspy_config() -> DspyFastAgentConfig:
    # ... [module configs like in dspy_agent.py main()]
    pass


# Main agent function with fast.custom decorator
@fast.custom(
    DspyAgent,
    name="diagram_generator",
    servers=["diagramming"],
    default=True,
    dspy_fast_agent_config=_create_dspy_config(),
)
async def agent(
    user_instruction: str,
    previous_history_json: Optional[str] = None
) -> AgentResult:
    # ... [implementation]
    pass


# Interactive mode
def main():
    async def run_interactive():
        async with fast.run() as fast_agent:
            await fast_agent.interactive()

    import asyncio
    asyncio.run(run_interactive())


if __name__ == "__main__":
    main()
```

### 2. Extended DspyAgent Class

**Create**: A subclass of `DspyAgent` that adds custom `run()` method

```python
from agent.fastagent.dspy_agent import DspyAgent as BaseDspyAgent

class DiagramDspyAgent(BaseDspyAgent):
    """Extended DspyAgent with custom run method for diagram generation."""

    async def run(
        self,
        user_instruction: str,
        previous_history_json: Optional[str] = None
    ) -> AgentResult:
        """
        Custom run method that handles full workflow.

        Steps:
        1. Load previous history into agent if available
        2. Format user instruction for DSPy
        3. Execute main_module (router)
        4. Inspect message history for latest tool call or string response
        5. Return AgentResult
        """
        # Load history if available
        if previous_history_json:
            try:
                previous_messages = from_json(previous_history_json)
                self.load_message_history(previous_messages)
            except Exception:
                # Start fresh if history loading fails
                pass

        # Format conversation history for DSPy
        conversation_context = self._format_history_for_dspy()

        # Execute main module (router)
        try:
            result = self.main_module(
                conversation_history=conversation_context,
                user_request=user_instruction
            )
        except Exception as e:
            # If execution fails, return error via fallback
            return self._create_fallback_result(str(e))

        # Inspect message history for NEW tool call result
        tool_result = self._extract_latest_tool_result()

        if tool_result:
            # Got a tool call result (diagram generated)
            return AgentResult(
                diagram_title=tool_result.get("title", "Diagram"),
                media_uri=tool_result.get("uri"),
                history_json=to_json(self.message_history),
            )
        else:
            # Got a string response (clarification or fallback)
            response_text = getattr(result, 'response', str(result))
            return AgentResult(
                diagram_title="Error",
                media_uri="",
                history_json=to_json(self.message_history),
            )

    def _format_history_for_dspy(self) -> str:
        """Convert message history to DSPy-compatible text format."""
        if not hasattr(self, 'message_history') or not self.message_history:
            return ""

        lines = []
        for msg in self.message_history:
            if hasattr(msg, 'role') and hasattr(msg, 'content'):
                lines.append(f"{msg.role}: {msg.content}")
        return "\n".join(lines)

    def _extract_latest_tool_result(self) -> Optional[dict]:
        """Extract latest tool call result from message history."""
        if not hasattr(self, 'message_history'):
            return None

        # Search for latest tool result
        for msg in reversed(self.message_history):
            if hasattr(msg, 'tool_results') and msg.tool_results:
                tool_result_obj = next(iter(msg.tool_results.values()))
                result_text = "".join(
                    block.text if hasattr(block, "text") else str(block)
                    for block in tool_result_obj.content
                )
                try:
                    return json.loads(result_text)
                except:
                    return None
        return None

    def _create_fallback_result(self, error_message: str) -> AgentResult:
        """Create a fallback result for errors."""
        return AgentResult(
            diagram_title="Error",
            media_uri="",
            history_json=to_json(self.message_history) if hasattr(self, 'message_history') else "[]",
        )
```

### 3. DiagramRouter with Fallback

**Enhanced from**: `/home/chris/projects/text-diagrams/backend/agent/src/agent/fastagent/dspy_agent.py` lines 296-382

**Key Changes**:

- Add `fallback_agent` parameter to `__init__`
- Add fallback handling in routing logic
- Route unclassifiable/unhandleable requests to fallback

```python
class DiagramRouter(dspy.Module):
    """Routes diagram requests to appropriate specialist with fallback."""

    TOOL_ROUTING = {
        "draw_technical_diagram": [
            "technical", "architecture", "cloud", "infrastructure", "system",
        ],
        "draw_mermaid": [
            "flow", "sequence", "flowchart", "process", "state", "class",
        ],
        "fallback": [
            "clarify", "error", "unknown", "cannot", "unable",
        ],
    }

    def __init__(self, technical_diagram_agent, mermaid_diagram_agent, fallback_agent):
        super().__init__()

        # Store module references
        self.agents = {
            "draw_technical_diagram": technical_diagram_agent,
            "draw_mermaid": mermaid_diagram_agent,
            "fallback": fallback_agent,
        }

        # Build keyword mapping (including fallback keywords)
        all_keywords = []
        self.keyword_to_tool = {}

        for tool_name, keywords in self.TOOL_ROUTING.items():
            all_keywords.extend(keywords)
            for keyword in keywords:
                self.keyword_to_tool[keyword] = tool_name

        # Create classifier with dynamic Literal type
        literal_type = Literal[tuple(all_keywords)]

        self.classifier = dspy.ChainOfThought(
            dspy.Signature(
                {
                    "conversation_history": dspy.InputField(),
                    "user_request": dspy.InputField(),
                },
                f"Classify the diagram request type. Use 'clarify' if the request is ambiguous or cannot be fulfilled.",
            ).append("diagram_type", dspy.OutputField(), type_=literal_type)
        )

    def forward(self, conversation_history, user_request):
        """Route request to appropriate specialist or fallback."""
        # Classify request
        classification = self.classifier(
            conversation_history=conversation_history,
            user_request=user_request
        )

        diagram_type = classification.diagram_type.lower()

        # Map to tool name
        tool_name = self.keyword_to_tool.get(diagram_type, "fallback")

        # Get agent and execute
        agent = self.agents[tool_name]
        return agent(
            conversation_history=conversation_history,
            user_request=user_request
        )
```

### 4. Fallback Module

**New**: Add a simple fallback module for unhandleable requests

```python
class FallbackAgent(dspy.Module):
    """Fallback agent for requests that cannot be fulfilled."""

    def __init__(self):
        super().__init__()
        self.responder = dspy.ChainOfThought(
            "conversation_history, user_request -> response: str"
        )

    def forward(self, conversation_history, user_request):
        """Generate a clarification or error message."""
        result = self.responder(
            conversation_history=conversation_history,
            user_request=user_request
        )
        return result
```

### 5. Configuration Builder Function (Updated)

**Pattern from**: `dspy_agent.py` main() function (lines 384-426)

**Changes**: Add fallback_module configuration

```python
def _create_dspy_config() -> DspyFastAgentConfig:
    """Create DspyAgent configuration with router, ReAct modules, and fallback."""

    technical_diagram_module = DspyModuleArgs(
        module_type=dspy.ReAct,
        name="technical_diagram_agent",
        args=("conversation_history, user_request -> diagram_code: str, title: str",),
        tools=["draw_technical_diagram"],
        load_path=None,
    )

    mermaid_diagram_module = DspyModuleArgs(
        module_type=dspy.ReAct,
        name="mermaid_diagram_agent",
        args=("conversation_history, user_request -> diagram_code: str, title: str",),
        tools=["draw_mermaid"],
        load_path=None,
    )

    # Add fallback module (no tools, just responds with clarification)
    fallback_module = DspyModuleArgs(
        module_type=FallbackAgent,
        name="fallback_agent",
        args=(),
        tools=[],
        load_path=None,
    )

    router_module = DspyModuleArgs(
        module_type=DiagramRouter,
        name="diagram_router",
        args=(),
        tools=[],
        load_path=None,
    )

    return DspyFastAgentConfig(
        router_module=router_module,
        react_modules=[
            technical_diagram_module,
            mermaid_diagram_module,
            fallback_module,
        ],
    )
```

### 6. Agent Function Implementation (Simplified)

**Key Logic**:

1. **Create DiagramDspyAgent instance** with configuration
1. **Call custom run() method** which handles:
   - Loading history
   - Formatting for DSPy
   - Executing main_module
   - Extracting results from history
1. **Return AgentResult** directly from run()

**Implementation**:

```python
@fast.custom(
    DiagramDspyAgent,
    name="diagram_generator",
    servers=["diagramming"],
    default=True,
    dspy_fast_agent_config=_create_dspy_config(),
)
async def agent(
    user_instruction: str,
    previous_history_json: Optional[str] = None
) -> AgentResult:
    """
    Main agent function - uses DspyAgent with custom run method.

    The custom run() method handles:
    - History loading
    - DSPy formatting
    - Module execution
    - Result extraction

    Args:
        user_instruction: User's diagram request
        previous_history_json: Optional previous conversation

    Returns:
        AgentResult with diagram info or error message
    """
    # Get DiagramDspyAgent instance from FastAgent context
    async with fast.run() as fast_agent:
        dspy_agent = fast_agent.diagram_generator

        # Call custom run method which handles everything
        result = await dspy_agent.run(
            user_instruction=user_instruction,
            previous_history_json=previous_history_json
        )

        return result
```

**Note**: The custom `run()` method in `DiagramDspyAgent` encapsulates all the logic:

- Loads history into agent
- Formats for DSPy
- Executes main_module
- Inspects message_history for latest tool call result
- Returns tool result (diagram) OR string response (error/clarification)

### 7. Result Extraction Logic (In DiagramDspyAgent.run())

**Approach**: After executing `main_module`, inspect `message_history` for:

1. **Latest tool call result** (NEW one from current execution) → Return as diagram
1. **String response only** (no tool call) → Return as error/clarification

**Implementation** (part of `DiagramDspyAgent._extract_latest_tool_result()`):

```python
def _extract_latest_tool_result(self) -> Optional[dict]:
    """
    Extract latest NEW tool call result from message history.

    Searches message_history in reverse to find the most recent tool call.
    Only returns if it's a NEW tool call from current execution.

    Returns:
        dict with {"title": ..., "uri": ...} if tool was called, else None
    """
    if not hasattr(self, 'message_history'):
        return None

    # Track previous message count to identify NEW tool calls
    # (This assumes we can differentiate new vs old messages)

    for msg in reversed(self.message_history):
        if hasattr(msg, 'tool_results') and msg.tool_results:
            # Extract tool result
            tool_result_obj = next(iter(msg.tool_results.values()))
            result_text = "".join(
                block.text if hasattr(block, "text") else str(block)
                for block in tool_result_obj.content
            )

            try:
                result_json = json.loads(result_text)
                # Verify it's a diagram result (has 'uri' field)
                if 'uri' in result_json:
                    return result_json
            except json.JSONDecodeError:
                continue

    return None
```

**Fallback Handling**:

- If no tool result found, return error/clarification message
- The fallback module produces string responses
- Extract from DSPy result: `getattr(result, 'response', str(result))`

### 8. Interactive Mode Main Function

```python
def main():
    """Run agent in interactive CLI mode for testing."""
    async def run_interactive():
        async with fast.run() as fast_agent:
            await fast_agent.interactive()

    import asyncio
    asyncio.run(run_interactive())


if __name__ == "__main__":
    main()
```

### 9. Update Package Imports

**File**: `/home/chris/projects/text-diagrams/backend/agent/src/agent/__init__.py`

**Change**:

```python
# Before
from agent.core.agent_orchestrator import agent, AgentResult

# After
from agent.agent import agent, AgentResult
```

## Migration Strategy

### Phase 1: Create and Test (Current Work)

1. Create `/home/chris/projects/text-diagrams/backend/agent/src/agent/agent.py` with complete implementation
1. Test interactive mode: `python -m agent.agent`
1. Verify DspyAgent initialization and routing work correctly

### Phase 2: Integration Testing

1. Update `__init__.py` imports
1. Test with Django views (keep old orchestrator as backup)
1. Verify URI extraction works correctly
1. Test multi-turn conversations with history

### Phase 3: Cleanup

1. Remove `agent/core/agent_orchestrator.py`
1. Remove old DSPy module files if no longer needed (router.py, python_gen.py, mermaid_gen.py)
1. Update documentation

## Implementation Summary

### New Approach (Per User Feedback)

1. **DiagramDspyAgent** extends DspyAgent with custom `run()` method
1. **Custom run()** handles:
   - Loading history if available
   - Formatting to DSPy-compatible format
   - Executing main_module
   - Inspecting message_history for latest tool call result
   - Returning tool result OR string response
1. **Agent function** simply calls `dspy_agent.run()` and returns result
1. **Fallback module** handles unhandleable requests

### Key Files to Create/Modify

1. **`/home/chris/projects/text-diagrams/backend/agent/src/agent/agent.py`**:

   - DiagramDspyAgent class (extends DspyAgent)
   - DiagramRouter class (with fallback support)
   - FallbackAgent class
   - Configuration builder
   - Agent function
   - Interactive mode

1. **`/home/chris/projects/text-diagrams/backend/agent/src/agent/__init__.py`**:

   - Update imports to use new agent.py

1. **`/home/chris/projects/text-diagrams/backend/agent/src/agent/fastagent/dspy_agent.py`**:

   - May need to update `construct_main_module()` to support fallback_agent parameter

## Known Challenges & Solutions

### Challenge 1: fast.custom() API

**Issue**: The exact API for `fast.custom()` is not fully documented
**Solution**: Follow the pattern from `@fast.agent()` decorator. If `fast.custom()` doesn't work as expected, we can:

- Use `@fast.agent()` instead and instantiate DiagramDspyAgent manually inside
- Register DiagramDspyAgent using a different FastAgent API method

### Challenge 2: Identifying NEW Tool Calls

**Issue**: Need to distinguish new tool calls from previous history
**Solution**: Options:

- Track message count before/after execution
- Use timestamps on messages
- Clear tool results before execution (if possible)

### Challenge 3: Fallback Module Integration

**Issue**: Router needs to pass fallback_agent to initialization
**Solution**: Update `construct_main_module()` in DspyAgent to accept fallback in react_modules list and pass to router `__init__`

## Verification

After implementation, test:

1. **Interactive Mode**:

   ```bash
   cd /home/chris/projects/text-diagrams/backend/agent
   export MCP_SERVICE_URL=http://localhost:8080
   python -m agent.agent
   # Test prompts: "Create AWS architecture diagram", "Make a flowchart"
   ```

1. **Django Integration**:

   ```bash
   task be:monolith:dev
   # Create diagram via API
   # Verify media_uri is correct
   # Test conversation continuation
   ```

1. **History Persistence**:

   - Create diagram
   - Request modification with previous history
   - Verify conversation context maintained

## Success Criteria

- ✅ New `agent.py` file created with FastAgent wrapper
- ✅ `agent()` function uses `fast.custom(DspyAgent, ...)`
- ✅ Interactive mode works: `python -m agent.agent`
- ✅ Agent returns correct AgentResult with diagram_title, media_uri, history_json
- ✅ Multi-turn conversations work with history
- ✅ Django views can use new agent without modifications
- ✅ Old orchestrator.py removed
