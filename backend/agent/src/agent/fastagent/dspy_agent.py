import asyncio
import functools
from typing import Any, Callable, Type

import dspy
from fast_agent import Context
from fast_agent.agents import AgentConfig, McpAgent
from mcp.types import Tool as FastAgentTool
from pydantic import BaseModel


class DspyModuleArgs(BaseModel):
    module_type: Type[dspy.Module]
    name: str
    args: tuple
    tools: list[str]
    load_path: str | None = None


class DspyFastAgentConfig(BaseModel):
    router_module: DspyModuleArgs
    react_modules: list[DspyModuleArgs]
    """
    Dictionary of assignment of what tools should be available to what dspy react modules
    Accepts a map of dspy.Module -> list[tool_name], where tool_name is a string as passed by fast-agent.
    """


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


def build_dspy_agent_class(dspy_fast_agent_config):
    class DspyAgent(McpAgent):
        def __init__(
            self,
            config: AgentConfig,
            connection_persistence: bool = True,
            context: "Context | None" = None,
            **kwargs,
        ) -> None:
            super().__init__(config, connection_persistence, context, **kwargs)

            self.router = dspy_fast_agent_config.router_module
            self.react_modules = dspy_fast_agent_config.react_modules
            self._main_module = None

        @property
        def main_module(self) -> dspy.Module:
            if self._main_module is None:
                self.main_module = self.main_module
            return self._main_module

        async def construct_main_module(self) -> dspy.Module:
            """
            Initializes each ReAct like dspy.Module with tools.
            Initializes Router Module with new modules as kwargs to init module

            Returns:
                Initialized router module (main entry point)
            """
            # Initialize all react modules using async map
            react_modules_dict = {}
            for module in self.react_modules:
                name, initialized_module = await self._initialize_react_module(
                    self, module
                )
                react_modules_dict[name] = initialized_module

            # Initialize router module with react modules as kwargs
            router = self.router.module_type(
                *self.router.args,
                **react_modules_dict,
            )

            # Load router state if path provided
            if self.router.load_path is not None:
                router.load(self.router.load_path)

            return router

        async def _create_callable_tools(
            self, tool_names: list[str]
        ) -> list[dspy.Tool]:
            """
            Create DSPy-compatible Tools from FastAgent Tools.

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

            # Create tool wrapper with self bound as context
            create_wrapper_with_context = functools.partial(
                self._create_tool_wrapper,
                self,
            )

            # Convert tool name to dspy.Tool
            def tool_name_to_dspy_tool(tool_name: str) -> dspy.Tool:
                if tool_name not in tools_map:
                    available = list(tools_map.keys())
                    raise ValueError(
                        f"Tool '{tool_name}' not found in available tools: {available}"
                    )

                fastagent_tool = tools_map[tool_name]
                # Use the full prefixed name for the wrapper
                wrapper_callable = create_wrapper_with_context(fastagent_tool.name)
                return _fastagent_tool_to_dspy_tool(fastagent_tool, wrapper_callable)

            # Use map to convert all tool names to dspy.Tools
            return list(map(tool_name_to_dspy_tool, tool_names))

        async def _initialize_react_module(
            self, module_config: DspyModuleArgs
        ) -> tuple[str, dspy.Module]:
            """Initialize a single ReAct module with its tools.

            Args:
                module_config: Configuration for the module
                agent: DspyAgent instance to get tools from

            Returns:
                Tuple of (module_name, initialized_module)
            """
            # Create tool callables for this module (now async)
            tools = await self._create_callable_tools(module_config.tools)

            # Initialize module with args and "tools" as kwarg
            module = module_config.module_type(*module_config.args, tools=tools)

            # Load state if path provided
            if module_config.load_path is not None:
                module.load(module_config.load_path)

            return module_config.name, module

        def _create_tool_wrapper(self, tool_name: str) -> Callable[[Any], str]:
            """Create a tool wrapper callable for a specific tool.

            Args:
                tool_name: Name of the tool to wrap
                agent: DspyAgent instance

            Returns:
                Callable that executes the tool synchronously by storing result in agent
            """

            def tool_wrapper(**kwargs: Any) -> str:
                """Execute the FastAgent tool by calling the agent's async method in sync mode."""
                return asyncio.run(self.call_tool(tool_name, kwargs))

            return tool_wrapper

    return DspyAgent
