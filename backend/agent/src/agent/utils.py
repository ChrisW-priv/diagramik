"""Utility functions for the agent module."""

import json
from typing import Any


def format_conversation_history(history_json: str | None) -> str:
    """Format conversation history JSON into readable text for LM context.

    Args:
        history_json: JSON string containing conversation history

    Returns:
        Formatted string representation of history, or empty string if None
    """
    if not history_json:
        return ""

    try:
        history = json.loads(history_json)
        if not history:
            return ""

        # Format as readable conversation
        lines = []
        for entry in history:
            role = entry.get("role", "unknown")
            content = entry.get("content", "")
            lines.append(f"{role}: {content}")

        return "\n".join(lines)
    except (json.JSONDecodeError, TypeError):
        return ""


def build_conversation_history(
    previous_history: str | None,
    user_request: str,
    agent_response: dict[str, Any],
) -> str:
    """Build updated conversation history JSON.

    Args:
        previous_history: Previous history JSON string
        user_request: Current user request
        agent_response: Agent response dict with generated content

    Returns:
        JSON string with updated conversation history
    """
    # Load previous history
    try:
        history = json.loads(previous_history) if previous_history else []
    except (json.JSONDecodeError, TypeError):
        history = []

    # Add user request
    history.append({"role": "user", "content": user_request})

    # Add agent response
    history.append(
        {
            "role": "assistant",
            "content": agent_response.get("summary", "Generated diagram"),
            "metadata": {
                "diagram_title": agent_response.get("title"),
                "tool_used": agent_response.get("tool_used"),
            },
        }
    )

    return json.dumps(history, indent=2)
