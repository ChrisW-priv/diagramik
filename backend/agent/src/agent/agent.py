"""Main agent entry point for diagram generation.

This module provides the public API for the diagram generation agent.
It handles:
1. History persistence between sessions
2. Direct tool result extraction
"""

import asyncio
import json
from pathlib import Path

from fast_agent import FastAgent
from fast_agent.mcp.prompt_serialization import from_json, to_json
from pydantic import BaseModel, Field

THIS_FILE_DIR = Path(__file__).parent
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
    history_json: str = Field(
        ...,
        description="Serialized conversation history for next turn",
    )


def _extract_last_tool_result(message_history) -> dict:
    """Extract the last diagram tool result from message history."""
    for msg in reversed(message_history):
        if msg.tool_results:
            for _call_id, result in msg.tool_results.items():
                for content in result.content:
                    if hasattr(content, "text"):
                        try:
                            parsed = json.loads(content.text)
                            if "uri" in parsed:
                                return parsed
                        except json.JSONDecodeError:
                            continue
    return {}


@fast.agent(
    instruction=(
        "You are a diagram generation assistant. "
        "Use the MCP tools to generate diagrams for the user. "
        "When generating Mermaid diagrams, consult your available skills for correct syntax.\n\n"
        "{{agentSkills}}"
    ),
    servers=["diagramming"],
)
async def agent(
    user_instruction: str, previous_history_json: str | None = None
) -> AgentResult:
    """Main entry point for diagram generation.

    Handles history persistence and tool result extraction.

    Args:
        user_instruction: The user's request for diagram generation
        previous_history_json: Optional JSON string of previous conversation history

    Returns:
        AgentResult with diagram info, updated history, and trace ID
    """
    async with fast.run() as agents:
        diagramming_agent = agents.default

        # 1. Load previous history if continuing conversation
        if previous_history_json:
            restored_messages = from_json(previous_history_json)
            diagramming_agent.load_message_history(restored_messages)

        # 2. Call agent
        await diagramming_agent.send(user_instruction)

        # 3. Extract last tool result directly (no AI rewriting)
        tool_result = _extract_last_tool_result(diagramming_agent.message_history)

        # 4. Serialize updated history
        history_json = to_json(diagramming_agent.message_history)

        return AgentResult(
            diagram_title=tool_result.get("title", "Untitled"),
            media_uri=tool_result.get("uri", ""),
            history_json=history_json,
        )


async def main():
    """Run the agent in interactive mode."""
    async with fast.run() as agents:
        result = await agents.interactive()
    return result


if __name__ == "__main__":
    asyncio.run(main())
