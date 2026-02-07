"""Main agent implementation using DspyAgent with FastAgent message history.

This module provides an integrated approach where ReAct modules directly call MCP tools,
and FastAgent manages conversation history for multi-turn conversations.

Architecture:
    FastAgent initialization (config: fastagent.config.yaml)
    ├── DiagramRouter (DSPy Module)
    │   ├── Classifier → routes to specialists or fallback
    │   ├── Routes: technical | mermaid | fallback
    │   └── Keyword-based with dynamic Literal types
    ├── TechnicalDiagramAgent (ReAct module)
    │   └── Tool: draw_technical_diagram
    ├── MermaidDiagramAgent (ReAct module)
    │   └── Tool: draw_mermaid
    ├── FallbackAgent (ChainOfThought module)
    │   └── Generates clarification messages
    └── agent() function
        ├── Loads previous history into DspyAgent context
        ├── Executes main_module via DSPy
        ├── Extracts tool result from message_history
        └── Returns AgentResult with updated history
"""

import json
from typing import Literal

import dspy
from fast_agent.agents import AgentConfig
from fast_agent.mcp.prompt_serialization import from_json, to_json
from pydantic import BaseModel, Field

from agent.exceptions import ClarificationNeeded
from agent.fastagent.dspy_agent import DspyAgent, DspyFastAgentConfig, DspyModuleArgs
from agent.utils import format_conversation_history


class AgentResult(BaseModel):
    """Complete result including response and updated history."""

    diagram_title: str = Field(
        ...,
        description="Title of the diagram",
    )
    media_uri: str = Field(..., description="URI of the generated diagram")
    history_json: str


class DiagramRouter(dspy.Module):
    """
    Routes diagram requests to appropriate specialist agent.

    Uses keyword-based routing with dynamically constructed Literal types
    to ensure type-safe routing decisions. Includes fallback agent for
    requests that cannot be fulfilled.
    """

    # Tool routing configuration: tool_name -> list of keywords
    TOOL_ROUTING = {
        "draw_technical_diagram": [
            "technical",
            "architecture",
            "cloud",
            "infrastructure",
            "system",
        ],
        "draw_mermaid": [
            "flow",
            "sequence",
            "flowchart",
            "process",
            "state",
            "class",
        ],
        "fallback": [
            "clarify",
            "error",
            "unknown",
            "cannot",
            "unable",
            "help",
        ],
    }

    def __init__(self, technical_diagram_agent, mermaid_diagram_agent, fallback_agent):
        super().__init__()

        # Store module references with tool mapping
        self.agents = {
            "draw_technical_diagram": technical_diagram_agent,
            "draw_mermaid": mermaid_diagram_agent,
            "fallback": fallback_agent,
        }

        # Build dynamic Literal type from all keywords
        all_keywords = []
        self.keyword_to_tool = {}  # keyword -> tool_name mapping

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
                f"Classify the diagram request type based on keywords: {', '.join(all_keywords)}",
            ).append("diagram_type", dspy.OutputField(), type_=literal_type)
        )

    def forward(self, conversation_history, user_request):
        """
        Route request to appropriate specialist.

        Args:
            conversation_history: Full conversation history for context
            user_request: Latest user request

        Returns:
            Result from specialist agent
        """
        # Classify diagram type using history + request
        classification = self.classifier(
            conversation_history=conversation_history, user_request=user_request
        )

        diagram_type = classification.diagram_type.lower()

        # Map diagram type to tool name
        tool_name = self.keyword_to_tool.get(diagram_type, "fallback")

        # Get agent and pass both history and request
        agent = self.agents[tool_name]
        return agent(
            conversation_history=conversation_history, user_request=user_request
        )


class FallbackAgent(dspy.Module):
    """Handles requests that cannot be fulfilled with diagram generation."""

    def __init__(self, tools=None):
        """
        Initialize fallback agent.

        Args:
            tools: Ignored. Fallback agent doesn't use tools.
        """
        super().__init__()
        self.responder = dspy.ChainOfThought(
            "conversation_history, user_request -> response: str"
        )

    def forward(self, conversation_history, user_request):
        """Generate a helpful clarification or error message."""
        return self.responder(
            conversation_history=conversation_history, user_request=user_request
        )


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

    fallback_module = DspyModuleArgs(
        module_type=FallbackAgent,
        name="fallback_agent",
        args=(),  # No args for __init__
        tools=[],  # No tools needed
        load_path=None,
    )

    router_module = DspyModuleArgs(
        module_type=DiagramRouter,
        name="diagram_router",
        args=(),  # Router receives agents as kwargs
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


def _extract_tool_result_from_executed(tool_results: dict[str, str]) -> dict | None:
    """Extract diagram result from executed tool calls.

    Args:
        tool_results: Dictionary mapping placeholder IDs to tool result strings

    Returns:
        Dictionary with tool result (containing "uri" and "title") or None
    """
    import sys

    # Check each tool result for a valid diagram response
    for placeholder_id, result_str in tool_results.items():
        print(
            f"DEBUG: Checking {placeholder_id}: {result_str[:200]}",
            file=sys.stderr,
            flush=True,
        )

        # Skip error messages
        if result_str.startswith("Error"):
            continue

        # Try to parse as JSON
        try:
            result_json = json.loads(result_str)
            if "uri" in result_json:
                print(
                    f"DEBUG: Found valid result with URI in {placeholder_id}!",
                    file=sys.stderr,
                    flush=True,
                )
                return result_json
        except json.JSONDecodeError:
            continue

    return None


def _extract_latest_tool_result(dspy_result) -> dict | None:
    """
    Extract latest tool call result from DSPy Prediction trajectory.

    Args:
        dspy_result: DSPy Prediction object from agent execution

    Returns:
        Dictionary with tool result (containing "uri" and "title") or None
    """
    import sys

    # Check if result has trajectory (ReAct modules)
    if not hasattr(dspy_result, "trajectory"):
        print("DEBUG: No trajectory in result", file=sys.stderr, flush=True)
        return None

    trajectory = dspy_result.trajectory
    print(
        f"DEBUG: Trajectory keys: {list(trajectory.keys())}",
        file=sys.stderr,
        flush=True,
    )

    # Look for observations in trajectory (these contain tool results)
    # Observations are named observation_0, observation_1, etc.
    observation_keys = [k for k in trajectory.keys() if k.startswith("observation_")]
    print(
        f"DEBUG: Found {len(observation_keys)} observations",
        file=sys.stderr,
        flush=True,
    )

    # Check observations in reverse order (most recent first)
    for obs_key in sorted(observation_keys, reverse=True):
        observation = trajectory[obs_key]
        print(
            f"DEBUG: {obs_key}: {observation[:200] if isinstance(observation, str) else observation}",
            file=sys.stderr,
            flush=True,
        )

        # Try to parse as JSON
        if isinstance(observation, str):
            try:
                result_json = json.loads(observation)
                if "uri" in result_json:
                    print(
                        "DEBUG: Found valid result with URI!",
                        file=sys.stderr,
                        flush=True,
                    )
                    return result_json
            except json.JSONDecodeError:
                continue

    return None


def _serialize_history(dspy_agent: DspyAgent) -> str:
    """
    Serialize conversation history from DspyAgent for next turn.

    Args:
        dspy_agent: DspyAgent instance after execution

    Returns:
        JSON string representation of conversation history
    """
    # Access the aggregator's message history
    if not hasattr(dspy_agent, "_aggregator"):
        return json.dumps([])

    aggregator = dspy_agent._aggregator
    if not hasattr(aggregator, "message_history"):
        return json.dumps([])

    messages = aggregator.message_history

    # Use FastAgent's to_json serializer
    try:
        return to_json(messages)
    except Exception:
        # Fallback to empty history on error
        return json.dumps([])


async def agent(
    user_instruction: str, previous_history_json: str | None = None
) -> AgentResult:
    """
    Main agent function using DspyAgent with FastAgent message history.

    Workflow:
    1. Create DspyAgent instance with proper context
    2. Load previous conversation history
    3. Format history for DSPy modules
    4. Execute main_module (router → specialist)
    5. Extract tool result from message_history
    6. Return AgentResult with updated history

    Args:
        user_instruction: User's natural language diagram request
        previous_history_json: Optional JSON string of previous conversation

    Returns:
        AgentResult with diagram title, media URI, and updated history

    Raises:
        ClarificationNeeded: When request cannot be fulfilled with diagram generation

    Example:
        >>> result = await agent("Create AWS 3-tier architecture")
        >>> print(result.diagram_title)
        >>> print(result.media_uri)
    """

    # Import necessary modules for context creation
    from fast_agent import Context
    from fast_agent.config import (
        Settings,
        MCPSettings,
        MCPServerSettings,
        MCPServerAuthSettings,
    )
    from fast_agent.mcp_server_registry import ServerRegistry
    import os

    # Get MCP service URL from environment
    mcp_url = os.getenv("MCP_SERVICE_URL", "http://localhost:8080")

    # Create MCP configuration manually
    mcp_config = MCPSettings(
        servers={
            "diagramming": MCPServerSettings(
                transport="http",
                url=f"{mcp_url}/mcp",
                auth=MCPServerAuthSettings(oauth=True),
            )
        }
    )

    # Create settings with MCP config
    settings = Settings(mcp=mcp_config)

    # Create server registry (pass settings, not settings.mcp)
    server_registry = ServerRegistry(settings)

    # Create context with server registry
    context = Context(
        config=settings,
        server_registry=server_registry,
    )

    # Configure DSPy LM (using GPT-4o-mini for reliability)
    dspy.configure(lm=dspy.LM("openai/gpt-4o-mini"))

    # Create DspyAgent instance with context
    agent_config = AgentConfig(name="diagram_generator", servers=["diagramming"])

    dspy_agent = DspyAgent(
        config=agent_config,
        dspy_fast_agent_config=_create_dspy_config(),
        context=context,
    )

    # Initialize DspyAgent (connects to MCP, builds modules)
    async with dspy_agent:
        # Load previous history into DspyAgent context
        if previous_history_json:
            try:
                previous_messages = from_json(previous_history_json)
                # Load messages into aggregator
                if hasattr(dspy_agent, "_aggregator"):
                    dspy_agent._aggregator.message_history = previous_messages
            except Exception:
                pass  # Start fresh on error

        # Format history for DSPy
        conversation_history = format_conversation_history(previous_history_json)

        # Execute main module (returns with PENDING_TOOL_CALL placeholders)
        result = dspy_agent.main_module(
            conversation_history=conversation_history, user_request=user_instruction
        )

        # Execute all pending tool calls asynchronously
        tool_results = await dspy_agent.execute_pending_tools()

        # Debug: print what we found
        import sys

        print(
            f"DEBUG: Executed {len(tool_results)} pending tools",
            file=sys.stderr,
            flush=True,
        )
        print(
            f"DEBUG: Tool results: {list(tool_results.keys())}",
            file=sys.stderr,
            flush=True,
        )

        # Extract the actual tool result from the executed tools
        tool_result = _extract_tool_result_from_executed(tool_results)

        print(f"DEBUG: Final tool_result = {tool_result}", file=sys.stderr, flush=True)
        print(f"DEBUG: result type = {type(result)}", file=sys.stderr, flush=True)

        if tool_result:
            # Diagram generated successfully
            return AgentResult(
                diagram_title=tool_result.get(
                    "title", getattr(result, "title", "Diagram")
                ),
                media_uri=tool_result["uri"],
                history_json=_serialize_history(dspy_agent),
            )
        else:
            # Fallback response (clarification needed)
            clarification_message = getattr(result, "response", str(result))
            raise ClarificationNeeded(clarification_message)


def main():
    """Run agent in interactive CLI mode for testing."""

    async def run_interactive():
        print("🎨 Diagram Generator - Interactive Mode")
        print("Type 'exit' to quit\n")

        conversation_history = None

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() in ["exit", "quit"]:
                break

            try:
                result = await agent(user_input, conversation_history)
                print(f"\n✅ {result.diagram_title}")
                print(f"📁 {result.media_uri}\n")
                conversation_history = result.history_json
            except ClarificationNeeded as e:
                print(f"\n❓ {e}\n")
            except Exception as e:
                print(f"\n❌ Error: {e}\n")

    import asyncio

    asyncio.run(run_interactive())


if __name__ == "__main__":
    main()
