from typing import Optional
import json

from pydantic import BaseModel, Field

from pathlib import Path

from fast_agent import FastAgent
from fast_agent.mcp.prompt_serialization import to_json, from_json

THIS_DIR = Path(__file__).parent


fast = FastAgent(
    "Diagramming Agent",
    config_path=THIS_DIR / "fastagent.config.yaml",
)


class AgentResult(BaseModel):
    """Complete result including response and updated history."""

    diagram_title: str = Field(
        ...,
        description="Title of the diagram: reuse if present in history, describe what was generated in 5-8 words max.",
    )
    media_uri: str = Field(..., description="URI of the generated diagram")
    history_json: str


@fast.agent(
    default=True,
    name="diagram_generator",
    instruction=THIS_DIR / "diagram_generator.md",
    servers=["diagramming"],
)
async def agent(
    user_instruction: str, previous_history_json: Optional[str] = None
) -> AgentResult:
    async with fast.run() as fast_agent:
        # Load previous history if provided
        if previous_history_json:
            try:
                previous_messages = from_json(previous_history_json)
                fast_agent.diagram_generator.load_message_history(previous_messages)
            except Exception:
                pass  # Start fresh on error

        # Send the new message
        await fast_agent.diagram_generator.send(user_instruction)

        last_tool_call = fast_agent.diagram_generator.message_history[-2].tool_results
        tool_result = next(iter(last_tool_call.values())).content[0].text
        last_tool_result = json.loads(tool_result)

        # Extract and serialize updated history
        updated_history = fast_agent.diagram_generator.message_history
        history_json = to_json(updated_history)

    return AgentResult(
        diagram_title=last_tool_result.get("title"),
        media_uri=last_tool_result.get("uri"),
        history_json=history_json,
    )


async def main():
    async with fast.run() as fast_agent:
        result = await fast_agent.interactive()
    return result


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
