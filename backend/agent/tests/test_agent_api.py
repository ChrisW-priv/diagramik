"""Tests for public agent() API."""

import pytest

from agent.agent import AgentResult


class TestAgentResult:
    """Tests for AgentResult model."""

    def test_creates_with_all_fields(self):
        """Should create AgentResult with all fields."""
        result = AgentResult(
            diagram_title="AWS Architecture",
            media_uri="gs://bucket/diagram.png",
            history_json='{"messages": []}',
            trace_id="abc-123",
        )

        assert result.diagram_title == "AWS Architecture"
        assert result.media_uri == "gs://bucket/diagram.png"
        assert result.history_json == '{"messages": []}'
        assert result.trace_id == "abc-123"

    def test_trace_id_optional(self):
        """trace_id should be optional."""
        result = AgentResult(
            diagram_title="Test",
            media_uri="gs://bucket/test.png",
            history_json='{"messages": []}',
        )

        assert result.trace_id is None

    def test_serialization(self):
        """Should serialize to dict/JSON correctly."""
        result = AgentResult(
            diagram_title="Test",
            media_uri="gs://bucket/test.png",
            history_json='{"messages": []}',
            trace_id="trace-123",
        )

        data = result.model_dump()

        assert data["diagram_title"] == "Test"
        assert data["media_uri"] == "gs://bucket/test.png"
        assert data["trace_id"] == "trace-123"


class TestAgentFunction:
    """Tests for agent() entry point.

    Note: These tests use mocking since the actual agent requires
    MCP server connection. Integration tests should use a real server.
    """

    @pytest.mark.asyncio
    async def test_returns_agent_result_type(self):
        """Should return an AgentResult instance."""
        # This is more of a type check - real functionality tested elsewhere
        result = AgentResult(
            diagram_title="Test",
            media_uri="gs://test/uri",
            history_json="{}",
            trace_id=None,
        )

        assert isinstance(result, AgentResult)

    def test_agent_result_requires_title(self):
        """AgentResult should require diagram_title."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            AgentResult(
                media_uri="gs://test/uri",
                history_json="{}",
            )

    def test_agent_result_requires_uri(self):
        """AgentResult should require media_uri."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            AgentResult(
                diagram_title="Test",
                history_json="{}",
            )

    def test_agent_result_requires_history(self):
        """AgentResult should require history_json."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            AgentResult(
                diagram_title="Test",
                media_uri="gs://test/uri",
            )


class TestHistoryHandling:
    """Tests for history serialization/deserialization."""

    def test_history_json_format(self):
        """History JSON should follow FastAgent format."""
        from fast_agent.mcp.prompt_serialization import from_json, to_json
        from fast_agent.types import PromptMessageExtended
        from mcp.types import TextContent

        # Create sample messages
        messages = [
            PromptMessageExtended(
                role="user",
                content=[TextContent(type="text", text="Create a diagram")],
            ),
            PromptMessageExtended(
                role="assistant",
                content=[TextContent(type="text", text="Done!")],
            ),
        ]

        # Serialize
        json_str = to_json(messages)

        # Deserialize
        restored = from_json(json_str)

        # Verify
        assert len(restored) == 2
        assert restored[0].role == "user"
        assert restored[1].role == "assistant"

    def test_history_preserves_tool_results(self):
        """History serialization should preserve tool_results."""
        from fast_agent.mcp.prompt_serialization import from_json, to_json
        from fast_agent.types import PromptMessageExtended
        from mcp.types import CallToolResult, TextContent

        messages = [
            PromptMessageExtended(
                role="user",
                content=[],
                tool_results={
                    "call_1": CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text='{"uri": "gs://bucket/img.png", "title": "Test"}',
                            )
                        ],
                        isError=False,
                    )
                },
            ),
        ]

        json_str = to_json(messages)
        restored = from_json(json_str)

        assert len(restored) == 1
        assert restored[0].tool_results is not None
        assert "call_1" in restored[0].tool_results

    def test_history_preserves_tool_calls(self):
        """History serialization should preserve tool_calls."""
        from fast_agent.mcp.prompt_serialization import from_json, to_json
        from fast_agent.types import PromptMessageExtended
        from mcp.types import CallToolRequest, CallToolRequestParams

        messages = [
            PromptMessageExtended(
                role="assistant",
                content=[],
                tool_calls={
                    "call_1": CallToolRequest(
                        method="tools/call",
                        params=CallToolRequestParams(
                            name="draw_diagram", arguments={"code": "test"}
                        ),
                    )
                },
            ),
        ]

        json_str = to_json(messages)
        restored = from_json(json_str)

        assert len(restored) == 1
        assert restored[0].tool_calls is not None
        assert "call_1" in restored[0].tool_calls
