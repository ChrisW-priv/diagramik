import asyncio
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable

import dspy
import nest_asyncio
from fast_agent import Context
from fast_agent.agents import AgentConfig, McpAgent
from mcp.types import CallToolResult, TextContent
from mcp.types import Tool as FastAgentTool
from pydantic import BaseModel

from agent.config import get_configured_lm

nest_asyncio.apply()
if TYPE_CHECKING:
    from fast_agent.types import PromptMessageExtended, RequestParams

# Directory for storing DSPy traces for training data collection
TRACES_DIR = Path(__file__).parent.parent.parent.parent / "data" / "dspy_traces"


class DspyModuleArgs(BaseModel):
    """Configuration for a DSPy module."""

    module_type: type[dspy.Module]
    name: str
    args: tuple
    tools: list[str]
    load_path: str | None = None


class DspyFastAgentConfig(BaseModel):
    """Configuration for DspyAgent's DSPy module hierarchy."""

    router_module: DspyModuleArgs
    react_modules: list[DspyModuleArgs]
    """Configuration for ReAct modules with tool assignments."""


def _fastagent_tool_to_dspy_tool(
    fastagent_tool: FastAgentTool,
    tool_callable: Callable,
) -> dspy.Tool:
    """Convert a FastAgent Tool to a DSPy Tool.

    DSPy will infer properties from the function and provided kwargs.
    We pass all available metadata and let DSPy handle inference.

    Args:
        fastagent_tool: FastAgent Tool with metadata
        tool_callable: Callable that executes the tool

    Returns:
        dspy.Tool instance with full metadata
    """
    return dspy.Tool(
        func=tool_callable,
        name=fastagent_tool.name,
        desc=fastagent_tool.description,
        args=fastagent_tool.inputSchema.get("properties", {})
        if fastagent_tool.inputSchema
        else {},
    )


def build_dspy_agent_class(dspy_config: DspyFastAgentConfig) -> type["DspyAgent"]:
    """Factory that creates a DspyAgent class bound to specific config.

    Args:
        dspy_config: Configuration for DSPy modules

    Returns:
        DspyAgent class bound to the config
    """

    class BoundDspyAgent(DspyAgent):
        def __init__(self, config: AgentConfig, **kwargs) -> None:
            super().__init__(config, dspy_config=dspy_config, **kwargs)

    return BoundDspyAgent


class DspyAgent(McpAgent):
    """FastAgent McpAgent that uses DSPy modules for generation.

    This agent overrides generate_impl() to use DSPy modules instead of the
    standard LLM-based generation loop. This enables:
    1. DSPy-driven routing between specialist agents
    2. Automatic tool call tracking in message history
    3. DSPy trace saving for training data collection
    """

    def __init__(
        self,
        config: AgentConfig,
        dspy_config: DspyFastAgentConfig,
        connection_persistence: bool = True,
        context: "Context | None" = None,
        **kwargs,
    ) -> None:
        super().__init__(config, connection_persistence, context, **kwargs)

        self._dspy_config = dspy_config
        self._main_module: dspy.Module | None = None
        self._tools_initialized = False
        self._last_trace_id: str | None = None
        self._tool_results_collected: dict[str, str] = {}

    async def generate_impl(
        self,
        messages: list["PromptMessageExtended"],
        request_params: "RequestParams | None" = None,
        tools: list[FastAgentTool] | None = None,
    ) -> "PromptMessageExtended":
        """Override to use DSPy module instead of LLM.

        This is called by send(), generate(), and interactive() - ensuring
        ALL entry points use DSPy-based generation.

        Args:
            messages: List of prompt messages (normalized input)
            request_params: Optional request parameters
            tools: Optional list of tools (ignored, we use DSPy modules)

        Returns:
            PromptMessageExtended with the assistant's response
        """
        from fast_agent.types import LlmStopReason, PromptMessageExtended

        # 1. Ensure main module initialized (lazy, after MCP ready)
        main_module = await self._ensure_main_module()

        # 2. Extract user request from last message
        user_request = messages[-1].all_text() if messages else ""

        # 3. Format existing history for DSPy input (everything except current request)
        history_for_dspy = self._format_history_for_dspy(self.message_history)

        # 4. Reset tool results collector for this turn
        self._tool_results_collected = {}

        # 5. Configure DSPy LM and call module
        lm = get_configured_lm()
        with dspy.context(lm=lm):
            prediction = main_module(
                conversation_history=history_for_dspy,
                user_request=user_request,
            )

        # 6. Save DSPy trace (stores trace_id in instance for later retrieval)
        self._last_trace_id = await self._save_dspy_trace(prediction, user_request)

        # 7. Build response message from DSPy result
        response_text = self._build_response_from_prediction(prediction)

        response = PromptMessageExtended(
            role="assistant",
            content=[TextContent(type="text", text=response_text)],
            stop_reason=LlmStopReason.END_TURN,
        )

        return response

    async def initialize(self) -> None:
        """Initialize agent and build DSPy modules after MCP connection.

        Overrides McpAgent.initialize() to ensure DSPy modules are constructed
        after MCP connections are established (so tools are available).
        """
        await super().initialize()
        self._ensure_main_module

    async def _ensure_main_module(self) -> dspy.Module:
        """Lazily construct main_module after MCP connection is ready.

        Must be called after initialize() has connected to MCP servers.

        Returns:
            Initialized DSPy router module

        Raises:
            RuntimeError: If called before MCP connection is ready
        """
        if self._main_module is None:
            self._main_module = await self._construct_main_module()
        return self._main_module

    async def _construct_main_module(self) -> dspy.Module:
        """Build the DSPy module hierarchy with tools from MCP.

        Returns:
            Initialized router module (main entry point)
        """
        react_modules_dict = {}

        for module_args in self._dspy_config.react_modules:
            # Create DSPy-compatible tools for this module
            dspy_tools = await self._create_callable_tools(module_args.tools)

            # Initialize module with tools
            module = module_args.module_type(*module_args.args, tools=dspy_tools)

            # Load optimized state if available
            if module_args.load_path:
                module.load(module_args.load_path)

            react_modules_dict[module_args.name] = module

        # Initialize router module with all specialist modules
        router = self._dspy_config.router_module.module_type(
            *self._dspy_config.router_module.args,
            **react_modules_dict,
        )

        if self._dspy_config.router_module.load_path:
            router.load(self._dspy_config.router_module.load_path)

        return router

    async def _create_callable_tools(self, tool_names: list[str]) -> list[dspy.Tool]:
        """Create DSPy-compatible Tools from FastAgent Tools.

        Must be called from async context after MCP connection is established.

        For each tool in tool_names:
        1. Get tool metadata from agent's list_tools()
        2. Create wrapper callable that calls agent.call_tool()
        3. Convert to dspy.Tool using helper function (preserves all metadata)

        Args:
            tool_names: List of tool names to create callables for (unprefixed names)

        Returns:
            List of dspy.Tool instances ready for ReAct modules
        """
        # Get all available tools from agent (direct await, no threading!)
        tools_result = await self.list_tools()

        # Create map of both prefixed and unprefixed tool names for lookup
        # MCP tools are returned with server prefix (e.g., "diagramming__draw_technical_diagram")
        tools_map = {}
        for tool in tools_result.tools:
            tools_map[tool.name] = tool
            # Also map unprefixed name (after "__") for convenience
            if "__" in tool.name:
                unprefixed_name = tool.name.split("__", 1)[1]
                tools_map[unprefixed_name] = tool

        # Convert tool name to dspy.Tool
        dspy_tools = []
        for tool_name in tool_names:
            if tool_name not in tools_map:
                available = list(tools_map.keys())
                raise ValueError(
                    f"Tool '{tool_name}' not found in available tools: {available}"
                )

            fastagent_tool = tools_map[tool_name]
            # Use the full prefixed name for the wrapper
            wrapper_callable = self._create_tool_wrapper(fastagent_tool.name)
            dspy_tool = _fastagent_tool_to_dspy_tool(fastagent_tool, wrapper_callable)
            dspy_tools.append(dspy_tool)

        return dspy_tools

    def _create_tool_wrapper(self, tool_name: str) -> Callable[..., str]:
        """Create a tool wrapper that:
        1. Executes the MCP tool via call_tool()
        2. Tracks call and result in FastAgent message history
        3. Returns string result for DSPy

        Args:
            tool_name: Name of the tool to wrap

        Returns:
            Synchronous callable for DSPy (which expects sync tools)
        """
        from mcp.types import CallToolRequest, CallToolRequestParams

        # Track call ID for correlation
        call_counter = [0]  # Mutable to increment in closure

        async def _execute_and_track(**kwargs: Any) -> str:
            """Execute tool, track in history, return string."""
            from fast_agent.types import PromptMessageExtended

            call_id = f"{tool_name}_{call_counter[0]}"
            call_counter[0] += 1

            # Execute tool
            result: CallToolResult = await self.call_tool(tool_name, kwargs)

            # Create tool call message (assistant requesting tool)
            tool_call_msg = PromptMessageExtended(
                role="assistant",
                content=[],
                tool_calls={
                    call_id: CallToolRequest(
                        method="tools/call",
                        params=CallToolRequestParams(name=tool_name, arguments=kwargs),
                    )
                },
            )

            # Create tool result message
            tool_result_msg = PromptMessageExtended(
                role="user",
                content=[],
                tool_results={call_id: result},
            )

            # Append to history
            self._append_history([tool_call_msg, tool_result_msg])

            # Extract text for DSPy (expects string return)
            text_parts = []
            for content in result.content:
                if hasattr(content, "text"):
                    text_parts.append(content.text)

            result_text = (
                "\n".join(text_parts)
                if text_parts
                else json.dumps({"status": "completed"})
            )

            # Store for later extraction
            self._tool_results_collected[call_id] = result_text

            return result_text

        def sync_wrapper(**kwargs: Any) -> str:
            """Synchronous wrapper for DSPy (which expects sync tools)."""
            return asyncio.run(_execute_and_track(**kwargs))

        return sync_wrapper

    def _append_history(self, messages: list["PromptMessageExtended"]) -> None:
        """Append messages to the agent's conversation history.

        Args:
            messages: List of messages to append
        """
        # Access the parent's message history via the property setter pattern
        current_history = self.message_history
        current_history.extend(messages)
        self.load_message_history(current_history)

    def _format_history_for_dspy(self, messages: list["PromptMessageExtended"]) -> str:
        """Convert FastAgent message history to markdown for DSPy modules.

        Includes tool calls and results since new requests often ask to
        fix previous generation results - the generated code must be visible.

        Args:
            messages: FastAgent message history

        Returns:
            Markdown-formatted conversation history
        """
        parts = []
        for msg in messages:
            role = msg.role.upper()

            # Text content
            for content in msg.content:
                if hasattr(content, "text") and content.text:
                    parts.append(f"## {role}\n{content.text}")

            # Tool calls (assistant requesting tools)
            if msg.tool_calls:
                for call_id, call in msg.tool_calls.items():
                    args_json = json.dumps(call.params.arguments or {}, indent=2)
                    parts.append(
                        f"## TOOL CALL: {call.params.name}\n```json\n{args_json}\n```"
                    )

            # Tool results (critical: contains generated code)
            if msg.tool_results:
                for call_id, result in msg.tool_results.items():
                    result_text = self._extract_tool_result_text(result)
                    parts.append(f"## TOOL RESULT\n```\n{result_text}\n```")

        return "\n\n".join(parts)

    def _extract_tool_result_text(self, result: CallToolResult) -> str:
        """Extract text content from CallToolResult.

        Args:
            result: CallToolResult from tool execution

        Returns:
            Text content from the result
        """
        for content in result.content:
            if hasattr(content, "text"):
                return content.text
        return str(result)

    def _build_response_from_prediction(self, prediction: dspy.Prediction) -> str:
        """Build response text from DSPy prediction.

        Args:
            prediction: DSPy module prediction result

        Returns:
            Response text for the assistant message
        """
        # Try to get title and diagram_code from prediction
        parts = []

        if hasattr(prediction, "title") and prediction.title:
            parts.append(f"**{prediction.title}**")

        if hasattr(prediction, "diagram_code") and prediction.diagram_code:
            parts.append(
                f"Generated diagram code:\n```\n{prediction.diagram_code}\n```"
            )

        if hasattr(prediction, "response") and prediction.response:
            # Fallback response (used by fallback agent)
            parts.append(prediction.response)

        if not parts:
            # Last resort - just convert prediction to string
            parts.append(str(prediction))

        return "\n\n".join(parts)

    async def _save_dspy_trace(
        self, prediction: dspy.Prediction, user_request: str
    ) -> str:
        """Save DSPy prediction/trajectory to file for training data.

        Returns trace_id that links to conversation.

        Args:
            prediction: DSPy module prediction result
            user_request: The user's request that generated this prediction

        Returns:
            Trace ID (UUID) linking to the trace file
        """
        trace_id = str(uuid.uuid4())

        # Extract trajectory if available (ReAct modules have this)
        trajectory = {}
        if hasattr(prediction, "trajectory"):
            trajectory = prediction.trajectory

        # Extract outputs (everything except trajectory)
        outputs = {}
        for k, v in prediction.items():
            if k != "trajectory":
                try:
                    # Try to serialize, skip if not serializable
                    json.dumps(v)
                    outputs[k] = v
                except (TypeError, ValueError):
                    outputs[k] = str(v)

        trace_data = {
            "trace_id": trace_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_request": user_request,
            "trajectory": trajectory,
            "outputs": outputs,
            "conversation_message_count": len(self.message_history),
            "tool_results": self._tool_results_collected,
        }

        # Ensure directory exists
        TRACES_DIR.mkdir(parents=True, exist_ok=True)
        trace_file = TRACES_DIR / f"{trace_id}.json"
        trace_file.write_text(json.dumps(trace_data, indent=2, default=str))

        return trace_id

    def extract_last_tool_result(self) -> dict:
        """Extract the last diagram tool result from message history.

        Returns raw parsed result without AI rewriting.

        Returns:
            Dictionary with tool result (containing "uri" and "title") or empty dict
        """
        for msg in reversed(self.message_history):
            if msg.tool_results:
                for call_id, result in msg.tool_results.items():
                    # Parse the raw CallToolResult content
                    for content in result.content:
                        if hasattr(content, "text"):
                            try:
                                parsed = json.loads(content.text)
                                if "uri" in parsed:  # Valid diagram result
                                    return parsed
                            except json.JSONDecodeError:
                                continue
        return {}

    @property
    def last_trace_id(self) -> str | None:
        """Get the trace ID from the last generation.

        Returns:
            Trace ID or None if no generation has occurred
        """
        return self._last_trace_id
