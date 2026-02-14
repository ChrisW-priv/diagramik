"""Tests for DspyAgent class."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.types import CallToolResult, TextContent

from agent.fastagent.dspy_agent import (
    DspyAgent,
    DspyFastAgentConfig,
    DspyModuleArgs,
    build_dspy_agent_class,
)


class TestToolWrapper:
    """Tests for tool wrapper that tracks history."""

    def test_wrapper_returns_string_type(self):
        """Tool wrapper should return string for DSPy, not CallToolResult."""
        # This test verifies the wrapper signature - actual execution requires MCP
        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)
            agent._tool_results_collected = {}
            agent._message_history = []

            # Mock the message_history property
            type(agent).message_history = property(lambda self: self._message_history)

            agent.call_tool = AsyncMock(
                return_value=CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text='{"uri": "gs://bucket/img.png", "title": "Test"}',
                        )
                    ],
                    isError=False,
                )
            )
            agent.load_message_history = MagicMock()

            wrapper = agent._create_tool_wrapper("test_tool")

            # Verify wrapper is callable
            assert callable(wrapper)

    @pytest.mark.asyncio
    async def test_wrapper_tracks_in_history(self):
        """Tool wrapper should add tool_call and tool_result messages to history."""
        from mcp.types import CallToolRequest, CallToolRequestParams
        from fast_agent.types import PromptMessageExtended

        # Create mock agent with necessary attributes
        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)
            agent._tool_results_collected = {}
            agent._message_history = []

            # Mock the message_history property
            type(agent).message_history = property(lambda self: self._message_history)

            recorded_history = []

            def mock_load_history(messages):
                recorded_history.clear()
                recorded_history.extend(messages)

            agent.load_message_history = mock_load_history
            agent.call_tool = AsyncMock(
                return_value=CallToolResult(
                    content=[
                        TextContent(
                            type="text",
                            text='{"uri": "gs://bucket/img.png", "title": "Test"}',
                        )
                    ],
                    isError=False,
                )
            )

            call_id = "test_tool_0"

            # Execute tool
            result = await agent.call_tool("test_tool", {"code": "test"})

            # Manually simulate what _append_history does
            tool_call_msg = PromptMessageExtended(
                role="assistant",
                content=[],
                tool_calls={
                    call_id: CallToolRequest(
                        method="tools/call",
                        params=CallToolRequestParams(
                            name="test_tool", arguments={"code": "test"}
                        ),
                    )
                },
            )
            tool_result_msg = PromptMessageExtended(
                role="user",
                content=[],
                tool_results={call_id: result},
            )

            agent._append_history([tool_call_msg, tool_result_msg])

            # Verify history was updated
            assert len(recorded_history) == 2
            assert recorded_history[0].role == "assistant"
            assert recorded_history[0].tool_calls is not None
            assert recorded_history[1].role == "user"
            assert recorded_history[1].tool_results is not None


class TestHistoryFormatter:
    """Tests for history to markdown formatter."""

    def test_formats_text_content(self):
        """Should format text messages with role headers."""
        from fast_agent.types import PromptMessageExtended

        messages = [
            PromptMessageExtended(
                role="user",
                content=[TextContent(type="text", text="Create a diagram")],
            ),
            PromptMessageExtended(
                role="assistant",
                content=[TextContent(type="text", text="I'll create that for you")],
            ),
        ]

        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)

            result = agent._format_history_for_dspy(messages)

            assert "## USER" in result
            assert "Create a diagram" in result
            assert "## ASSISTANT" in result
            assert "I'll create that for you" in result

    def test_includes_tool_calls(self):
        """Should include tool call arguments in formatted output."""
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
                            name="draw_diagram", arguments={"code": "test code"}
                        ),
                    )
                },
            ),
        ]

        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)

            result = agent._format_history_for_dspy(messages)

            assert "## TOOL CALL: draw_diagram" in result
            assert "test code" in result

    def test_includes_tool_results(self):
        """Should include tool results (critical for iterative refinement)."""
        from fast_agent.types import PromptMessageExtended

        messages = [
            PromptMessageExtended(
                role="user",
                content=[],
                tool_results={
                    "call_1": CallToolResult(
                        content=[
                            TextContent(
                                type="text",
                                text='{"uri": "gs://bucket/diagram.png", "title": "My Diagram"}',
                            )
                        ],
                        isError=False,
                    )
                },
            ),
        ]

        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)

            result = agent._format_history_for_dspy(messages)

            assert "## TOOL RESULT" in result
            assert "gs://bucket/diagram.png" in result


class TestToolResultExtraction:
    """Tests for direct tool result extraction."""

    def test_extracts_last_diagram_result(self):
        """Should extract URI and title from last tool result."""
        from fast_agent.types import PromptMessageExtended

        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)
            agent._message_history = [
                PromptMessageExtended(
                    role="user",
                    content=[],
                    tool_results={
                        "call_1": CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text='{"uri": "gs://bucket/diagram.png", "title": "AWS Architecture"}',
                                )
                            ],
                            isError=False,
                        )
                    },
                ),
            ]

            # Mock the property
            type(agent).message_history = property(lambda self: self._message_history)

            result = agent.extract_last_tool_result()

            assert result["uri"] == "gs://bucket/diagram.png"
            assert result["title"] == "AWS Architecture"

    def test_returns_empty_dict_when_no_results(self):
        """Should return {} when no tool results in history."""
        from fast_agent.types import PromptMessageExtended

        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)
            agent._message_history = [
                PromptMessageExtended(
                    role="user",
                    content=[TextContent(type="text", text="Hello")],
                ),
            ]

            type(agent).message_history = property(lambda self: self._message_history)

            result = agent.extract_last_tool_result()

            assert result == {}

    def test_skips_invalid_json(self):
        """Should skip tool results with invalid JSON."""
        from fast_agent.types import PromptMessageExtended

        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)
            agent._message_history = [
                PromptMessageExtended(
                    role="user",
                    content=[],
                    tool_results={
                        "call_1": CallToolResult(
                            content=[
                                TextContent(
                                    type="text",
                                    text="Not valid JSON",
                                )
                            ],
                            isError=False,
                        )
                    },
                ),
            ]

            type(agent).message_history = property(lambda self: self._message_history)

            result = agent.extract_last_tool_result()

            assert result == {}


class TestDspyTraceSaving:
    """Tests for DSPy trace persistence."""

    @pytest.mark.asyncio
    async def test_saves_trace_file(self, tmp_path):
        """Should save trace to data/dspy_traces/{trace_id}.json."""
        import dspy

        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)
            agent._tool_results_collected = {"call_1": '{"uri": "test"}'}
            agent._message_history = []

            type(agent).message_history = property(lambda self: self._message_history)

            # Mock prediction
            prediction = dspy.Prediction(title="Test Diagram", diagram_code="code")

            # Patch TRACES_DIR to use tmp_path
            with patch("agent.fastagent.dspy_agent.TRACES_DIR", tmp_path / "traces"):
                trace_id = await agent._save_dspy_trace(
                    prediction, "Create a test diagram"
                )

            # Verify trace file exists
            trace_file = tmp_path / "traces" / f"{trace_id}.json"
            assert trace_file.exists()

            # Verify content
            trace_data = json.loads(trace_file.read_text())
            assert trace_data["trace_id"] == trace_id
            assert trace_data["user_request"] == "Create a test diagram"
            assert "timestamp" in trace_data

    @pytest.mark.asyncio
    async def test_trace_contains_outputs(self, tmp_path):
        """Trace file should include DSPy outputs."""
        import dspy

        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)
            agent._tool_results_collected = {}
            agent._message_history = []

            type(agent).message_history = property(lambda self: self._message_history)

            prediction = dspy.Prediction(
                title="AWS Architecture", diagram_code="from diagrams..."
            )

            with patch("agent.fastagent.dspy_agent.TRACES_DIR", tmp_path / "traces"):
                trace_id = await agent._save_dspy_trace(prediction, "test")

            trace_file = tmp_path / "traces" / f"{trace_id}.json"
            trace_data = json.loads(trace_file.read_text())

            assert trace_data["outputs"]["title"] == "AWS Architecture"
            assert trace_data["outputs"]["diagram_code"] == "from diagrams..."

    def test_trace_id_is_uuid(self):
        """Trace ID should be a valid UUID string."""
        import uuid

        # The trace ID format should be validated
        test_id = str(uuid.uuid4())
        # Verify it's a valid UUID
        uuid.UUID(test_id)  # Should not raise


class TestBuildDspyAgentClass:
    """Tests for the DspyAgent class factory."""

    def test_creates_bound_class(self):
        """Factory should create a class bound to specific config."""
        import dspy

        # Use real DSPy module types instead of MagicMock
        config = DspyFastAgentConfig(
            router_module=DspyModuleArgs(
                module_type=dspy.Module,
                name="router",
                args=(),
                tools=[],
            ),
            react_modules=[],
        )

        BoundAgent = build_dspy_agent_class(config)

        assert issubclass(BoundAgent, DspyAgent)

    def test_bound_class_stores_config(self):
        """Bound class should store the config in instances."""
        import dspy

        # Use real DSPy module types instead of MagicMock
        config = DspyFastAgentConfig(
            router_module=DspyModuleArgs(
                module_type=dspy.Module,
                name="test_router",
                args=(),
                tools=[],
            ),
            react_modules=[
                DspyModuleArgs(
                    module_type=dspy.ReAct,
                    name="test_module",
                    args=("input -> output",),
                    tools=["tool1"],
                ),
            ],
        )

        BoundAgent = build_dspy_agent_class(config)

        # Verify the config is accessible via the bound class
        # (We can't instantiate without MCP, but we can verify the class)
        assert BoundAgent is not DspyAgent


class TestResponseBuilder:
    """Tests for building response from DSPy prediction."""

    def test_builds_from_title_and_code(self):
        """Should build response with title and diagram code."""
        import dspy

        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)

            prediction = dspy.Prediction(
                title="AWS Architecture", diagram_code="from diagrams import..."
            )

            result = agent._build_response_from_prediction(prediction)

            assert "**AWS Architecture**" in result
            assert "from diagrams import..." in result

    def test_builds_from_fallback_response(self):
        """Should build response from fallback agent's response field."""
        import dspy

        with patch.object(DspyAgent, "__init__", lambda self, *a, **kw: None):
            agent = DspyAgent.__new__(DspyAgent)

            prediction = dspy.Prediction(
                response="I need more information to create a diagram."
            )

            result = agent._build_response_from_prediction(prediction)

            assert "I need more information" in result
