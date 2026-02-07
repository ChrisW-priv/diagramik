from typing import Callable, Type, Any
import asyncio
import functools
import uuid
import dspy
from fast_agent.agents import McpAgent, AgentConfig
from fast_agent import Context
from pydantic import BaseModel
from mcp.types import Tool as FastAgentTool


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


def _create_tool_wrapper(context: "DspyAgent", tool_name: str) -> Callable[[Any], str]:
    """Create a tool wrapper callable for a specific tool.

    Args:
        tool_name: Name of the tool to wrap
        context: DspyAgent instance (acts as self)

    Returns:
        Callable that executes the tool
    """

    def _get_async_loop():
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop

    def tool_wrapper(**kwargs: Any) -> str:
        """Execute the FastAgent tool via call_tool()."""
        # Generate unique tool use ID
        tool_use_id = str(uuid.uuid4())

        # Call tool using agent's call_tool method (async)
        loop = _get_async_loop()

        try:
            result = loop.run_until_complete(
                context.call_tool(
                    name=tool_name,
                    arguments=kwargs,
                    tool_use_id=tool_use_id,
                    request_params=None,
                )
            )

            # Handle error results
            if result.isError:
                return f"Error calling tool: {result.content}"

            # Extract text content from CallToolResult.content blocks
            return "".join(
                block.text if hasattr(block, "text") else str(block)
                for block in result.content
            )

        except Exception as e:
            return f"Error calling tool '{tool_name}': {str(e)}"

    return tool_wrapper


def _initialize_react_module(
    agent: "DspyAgent",
    module_config: DspyModuleArgs,
) -> tuple[str, dspy.Module]:
    """Initialize a single ReAct module with its tools.

    Args:
        module_config: Configuration for the module
        agent: DspyAgent instance to get tools from

    Returns:
        Tuple of (module_name, initialized_module)
    """
    # Create tool callables for this module
    tools = agent._create_callable_tools(module_config.tools)

    # Initialize module with args and "tools" as kwarg
    module = module_config.module_type(*module_config.args, tools=tools)

    # Load state if path provided
    if module_config.load_path is not None:
        module.load(module_config.load_path)

    return module_config.name, module


class DspyAgent(McpAgent):
    def __init__(
        self,
        config: AgentConfig,
        connection_persistence: bool = True,
        context: "Context | None" = None,
        dspy_fast_agent_config: DspyFastAgentConfig | None = None,
        **kwargs,
    ) -> None:
        super().__init__(config, connection_persistence, context, **kwargs)

        if dspy_fast_agent_config is None:
            raise TypeError("dspy_fast_agent_config parameter cannot be None.")

        self.router = dspy_fast_agent_config.router_module
        self.react_modules = dspy_fast_agent_config.react_modules
        self._main_module = None  # Lazy initialization
        self._modules_constructed = False

    @property
    def main_module(self) -> dspy.Module:
        """
        Lazily construct and return the main module.

        Modules are constructed on first access to ensure the MCP connection
        is properly initialized.
        """
        if not self._modules_constructed:
            self._main_module = self.construct_main_module()
            self._modules_constructed = True
        return self._main_module

    def construct_main_module(self) -> dspy.Module:
        """
        Initializes each ReAct like dspy.Module with tools.
        Initializes Router Module with new modules as kwargs to init module

        Returns:
            Initialized router module (main entry point)
        """
        # Initialize all react modules using map
        react_modules_dict = dict(
            _initialize_react_module(self, module) for module in self.react_modules
        )

        # Initialize router module with react modules as kwargs
        router = self.router.module_type(
            *self.router.args,
            **react_modules_dict,
        )

        # Load router state if path provided
        if self.router.load_path is not None:
            router.load(self.router.load_path)

        return router

    def _create_callable_tools(self, tool_names: list[str]) -> list[dspy.Tool]:
        """
        Create DSPy-compatible Tools from FastAgent Tools.

        For each tool in tool_names:
        1. Get tool metadata from agent's list_tools()
        2. Create wrapper callable that calls agent.call_tool()
        3. Convert to dspy.Tool using helper function (preserves all metadata)

        Args:
            tool_names: List of tool names to create callables for

        Returns:
            List of dspy.Tool instances ready for ReAct modules
        """
        # Get all available tools from agent
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, create a new one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        tools_result = loop.run_until_complete(self.list_tools())

        # Create map of tool_name -> Tool for easy lookup
        tools_map = {tool.name: tool for tool in tools_result.tools}

        # Create tool wrapper with self bound as context
        create_wrapper_with_context = functools.partial(
            _create_tool_wrapper,
            self,
        )

        # Convert tool name to dspy.Tool
        def tool_name_to_dspy_tool(tool_name: str) -> dspy.Tool:
            if tool_name not in tools_map:
                raise ValueError(f"Tool '{tool_name}' not found in available tools")

            fastagent_tool = tools_map[tool_name]
            wrapper_callable = create_wrapper_with_context(tool_name)
            return _fastagent_tool_to_dspy_tool(fastagent_tool, wrapper_callable)

        # Use map to convert all tool names to dspy.Tools
        return list(map(tool_name_to_dspy_tool, tool_names))


def main():
    """
    Initializes a DspyAgent with two specialized ReAct modules and a router.

    Architecture:
    - DiagramRouter: Routes requests to appropriate diagram specialist using keyword-based routing
    - TechnicalDiagramAgent: Uses draw_technical_diagram for cloud/system diagrams
    - MermaidDiagramAgent: Uses draw_mermaid for flowcharts/sequences

    Both conversation history and user request are passed through all modules
    to support iterative refinement of diagrams.

    Requirements:
    - MCP_SERVICE_URL environment variable must be set
    - MCP diagram server must be running and accessible
    - Config file at config/dspy_agent.config.yaml (optional, uses defaults if not present)

    Raises:
        EnvironmentError: If MCP_SERVICE_URL is not set
    """
    import os
    from typing import Literal

    # Verify environment setup
    if not os.getenv("MCP_SERVICE_URL"):
        raise EnvironmentError(
            "MCP_SERVICE_URL environment variable must be set. "
            "Example: export MCP_SERVICE_URL=http://localhost:8080"
        )

    # Define custom router module with keyword-based routing
    class DiagramRouter(dspy.Module):
        """
        Routes diagram requests to appropriate specialist agent.

        Uses keyword-based routing with dynamically constructed Literal types
        to ensure type-safe routing decisions.
        """

        # Tool routing configuration: tool_name -> list of keywords
        TOOL_ROUTING = {
            "draw_technical_diagram": [
                "technical",
                "architecture",
                "cloud",
                "infrastructure",
                "system",
            ],
            "draw_mermaid": [
                "flow",
                "sequence",
                "flowchart",
                "process",
                "state",
                "class",
            ],
        }

        def __init__(self, technical_diagram_agent, mermaid_diagram_agent):
            super().__init__()

            # Store module references with tool mapping
            self.agents = {
                "draw_technical_diagram": technical_diagram_agent,
                "draw_mermaid": mermaid_diagram_agent,
            }

            # Build dynamic Literal type from all keywords
            all_keywords = []
            self.keyword_to_tool = {}  # keyword -> tool_name mapping

            for tool_name, keywords in self.TOOL_ROUTING.items():
                all_keywords.extend(keywords)
                for keyword in keywords:
                    self.keyword_to_tool[keyword] = tool_name

            # Create classifier with dynamic Literal type
            literal_type = Literal[tuple(all_keywords)]

            self.classifier = dspy.ChainOfThought(
                dspy.Signature(
                    {
                        "conversation_history": dspy.InputField(),
                        "user_request": dspy.InputField(),
                    },
                    f"Classify the diagram request type based on keywords: {', '.join(all_keywords)}",
                ).append("diagram_type", dspy.OutputField(), type_=literal_type)
            )

        def forward(self, conversation_history, user_request):
            """
            Route request to appropriate specialist.

            Args:
                conversation_history: Full conversation history for context
                user_request: Latest user request

            Returns:
                Result from specialist agent
            """
            # Classify diagram type using history + request
            classification = self.classifier(
                conversation_history=conversation_history, user_request=user_request
            )

            diagram_type = classification.diagram_type.lower()

            # Map diagram type to tool name
            tool_name = self.keyword_to_tool.get(diagram_type)
            if tool_name is None:
                # Default to mermaid for unrecognized types
                tool_name = "draw_mermaid"

            # Get agent and pass both history and request
            agent = self.agents[tool_name]
            return agent(
                conversation_history=conversation_history, user_request=user_request
            )

    # Create ReAct module configurations with conversation history
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

    # Create router module configuration
    router_module = DspyModuleArgs(
        module_type=DiagramRouter,
        name="diagram_router",
        args=(),
        tools=[],
        load_path=None,
    )

    # Create agent configuration with MCP server
    agent_config = AgentConfig(name="diagram-generation-agent", servers=["diagramming"])

    # Create DSPy-specific configuration
    dspy_config = DspyFastAgentConfig(
        router_module=router_module,
        react_modules=[technical_diagram_module, mermaid_diagram_module],
    )

    # Initialize DspyAgent
    agent = DspyAgent(
        config=agent_config,
        connection_persistence=True,
        context=None,
        dspy_fast_agent_config=dspy_config,
    )

    return agent


if __name__ == "__main__":
    main()
