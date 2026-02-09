import asyncio
import json
from pathlib import Path

import dspy
from fast_agent import FastAgent
from fast_agent.agents import McpAgent
from fast_agent.mcp.prompt_serialization import to_json
from pydantic import BaseModel, Field

from agent.dspy_modules import DiagramRouter, FallbackAgent
from agent.fastagent.dspy_agent import (
    DspyFastAgentConfig,
    DspyModuleArgs,
    build_dspy_agent_class,
)

THIS_FILE_DIR = Path(__name__).parent
CONF_FILE = THIS_FILE_DIR.parent.parent / "config" / "fastagent.config.yaml"

fast = FastAgent(
    "Diagramming Agent",
    config_path=str(CONF_FILE),
)


class AgentResult(BaseModel):
    """Complete result including response and updated history."""

    diagram_title: str = Field(
        ...,
        description="Title of the diagram",
    )
    media_uri: str = Field(..., description="URI of the generated diagram")
    history_json: str


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


DspyAgent = build_dspy_agent_class(_create_dspy_config())


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


def _serialize_history(dspy_agent: McpAgent) -> str:
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


@fast.custom(
    DspyAgent,
    servers=["diagramming"],
)
async def agent(
    user_instruction: str, previous_history_json: str | None = None
) -> AgentResult:
    async with fast.run() as agent:
        # TODO: load history from JSON

        # run the agent, agent runs tools and returns the status
        result = await agent.default.send(user_instruction)

        # TODO: retrieve the last tool call since the last message in the history
        # this means: find last message, get it's index
        # iterate over all messages from that index till the end, but in rev. order.

        # TODO: build proper AgentResult
        agent_result = AgentResult(result)
    return agent_result


async def main():
    async with fast.run() as agent:
        result = await agent.interactive()
    return result


if __name__ == "__main__":
    asyncio.run(main())
