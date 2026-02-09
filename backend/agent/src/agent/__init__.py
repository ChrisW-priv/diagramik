"""
Text Diagrams Agent - Hybrid DSPy + FastAgent diagram generation.

This module provides an intelligent diagram generation system that combines:
- DSPy for structured LLM prompting and optimization
- FastAgent for MCP tool access (Python diagrams and Mermaid rendering)

Public API:
    agent(user_instruction, previous_history_json) -> AgentResult

Example:
    >>> from agent import agent
    >>> import asyncio
    >>>
    >>> result = asyncio.run(agent("Create a 3-tier web app on AWS"))
    >>> print(result.diagram_title)
    >>> print(result.media_uri)
"""

from agent.agent import AgentResult, agent

__all__ = [
    "agent",
    "AgentResult",
]
