"""Utilities for diagram source code extraction from agent history."""

import json
import logging

logger = logging.getLogger(__name__)

# Tool names that produce diagram source code
TECHNICAL_TOOL = "draw_technical_diagram"
MERMAID_TOOL = "draw_mermaid"


def extract_diagram_source(agent_history_json: str) -> dict | None:
    """Extract source code and type from agent history.

    Walks messages in reverse to find the last tool call with a `code` argument
    from either `draw_technical_diagram` or `draw_mermaid`.

    Args:
        agent_history_json: JSON string of serialized fast-agent conversation history

    Returns:
        {"source_code": str, "diagram_type": "technical"|"mermaid", "title": str}
        or None if no tool call found.
    """
    if not agent_history_json:
        return None

    try:
        from fast_agent.mcp.prompt_serialization import from_json

        messages = from_json(agent_history_json)
    except Exception:
        logger.warning("Failed to deserialize agent history", exc_info=True)
        return None

    # Walk messages in reverse to find the last tool call
    for msg in reversed(messages):
        if not hasattr(msg, "tool_calls") or not msg.tool_calls:
            continue

        for tool_call in msg.tool_calls:
            tool_name = getattr(tool_call, "name", "")

            if tool_name not in (TECHNICAL_TOOL, MERMAID_TOOL):
                continue

            # Extract the arguments
            args_str = getattr(tool_call, "arguments", None)
            if not args_str:
                continue

            try:
                args = json.loads(args_str) if isinstance(args_str, str) else args_str
            except (json.JSONDecodeError, TypeError):
                continue

            code = args.get("code", "")
            title = args.get("title", "")

            if not code:
                continue

            diagram_type = "technical" if tool_name == TECHNICAL_TOOL else "mermaid"

            return {
                "source_code": code,
                "diagram_type": diagram_type,
                "title": title,
            }

    return None
