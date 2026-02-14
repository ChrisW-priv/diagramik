"""Main agent entry point for diagram generation.

This module provides the public API for the diagram generation agent.
It handles:
1. History persistence between sessions
2. Direct tool result extraction
3. DSPy-driven generation via DspyAgent
4. OpenTelemetry tracing for monitoring
"""

import asyncio
from pathlib import Path

import dspy
from fast_agent import FastAgent
from fast_agent.mcp.prompt_serialization import from_json, to_json
from pydantic import BaseModel, Field

from agent.cloudrun_auth import patch_fastagent_oauth
from agent.dspy_modules import DiagramRouter, FallbackAgent
from agent.fastagent.dspy_agent import (
    DspyFastAgentConfig,
    DspyModuleArgs,
    build_dspy_agent_class,
)
from agent.telemetry import get_tracer

THIS_FILE_DIR = Path(__name__).parent
CONF_FILE = THIS_FILE_DIR.parent.parent / "config" / "fastagent.config.yaml"

# Patch FastAgent OAuth for CloudRun service-to-service auth
patch_fastagent_oauth()

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
    history_json: str = Field(
        ...,
        description="Serialized conversation history for next turn",
    )
    trace_id: str | None = Field(
        None,
        description="ID linking to DSPy trace file for training data",
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


DspyAgent = build_dspy_agent_class(_create_dspy_config())


@fast.custom(
    DspyAgent,
    servers=["diagramming"],
)
async def agent(
    user_instruction: str, previous_history_json: str | None = None
) -> AgentResult:
    """Main entry point for diagram generation.

    Handles history persistence at this level (not in DspyAgent class).

    Args:
        user_instruction: The user's request for diagram generation
        previous_history_json: Optional JSON string of previous conversation history

    Returns:
        AgentResult with diagram info, updated history, and trace ID
    """
    tracer = get_tracer()
    with tracer.start_as_current_span("agent.generate_diagram") as span:
        span.set_attribute("agent.has_history", previous_history_json is not None)
        span.set_attribute(
            "agent.instruction_length", len(user_instruction) if user_instruction else 0
        )

        async with fast.run() as agents:
            dspy_agent = agents.default

            # 1. Load previous history if continuing conversation
            if previous_history_json:
                restored_messages = from_json(previous_history_json)
                dspy_agent.load_message_history(restored_messages)
                span.set_attribute(
                    "agent.restored_message_count", len(restored_messages)
                )

            # 2. Call agent (uses generate_impl override → DSPy)
            await dspy_agent.send(user_instruction)

            # 3. Extract last tool result directly (no AI rewriting)
            tool_result = dspy_agent.extract_last_tool_result()
            span.set_attribute("agent.has_tool_result", bool(tool_result))

            # 4. Serialize updated history
            history_json = to_json(dspy_agent.message_history)
            span.set_attribute(
                "agent.final_message_count", len(dspy_agent.message_history)
            )

            # 5. Get trace ID from last generation
            trace_id = dspy_agent.last_trace_id
            if trace_id:
                span.set_attribute("agent.dspy_trace_id", trace_id)

            return AgentResult(
                diagram_title=tool_result.get("title", "Untitled"),
                media_uri=tool_result.get("uri", ""),
                history_json=history_json,
                trace_id=trace_id,
            )


async def main():
    """Run the agent in interactive mode."""
    async with fast.run() as agents:
        result = await agents.interactive()
    return result


if __name__ == "__main__":
    asyncio.run(main())
