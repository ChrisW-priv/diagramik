"""Tests for DspyAgent initialization and routing behavior."""

import pytest
from agent.fastagent.dspy_agent import main, DspyAgent


class TestDspyAgentInitialization:
    """Test DspyAgent proper initialization."""

    @pytest.fixture
    async def initialized_agent(self):
        """Fixture providing agent with MCP connection initialized."""
        agent = main()
        # Initialize MCP connection using context manager
        async with agent:
            yield agent

    def test_main_returns_dspy_agent_instance(self):
        """Test that main() returns a DspyAgent instance."""
        agent = main()
        assert isinstance(agent, DspyAgent)

    def test_agent_has_correct_name(self):
        """Test agent config has expected name."""
        agent = main()
        assert agent.config.name == "diagram-generation-agent"

    def test_agent_connected_to_diagramming_server(self):
        """Test agent is configured with diagramming server."""
        agent = main()
        assert "diagramming" in agent.config.servers

    def test_agent_has_two_react_modules(self):
        """Test agent configured with exactly 2 ReAct modules."""
        agent = main()
        assert len(agent.react_modules) == 2

        # Verify module names
        module_names = [m.name for m in agent.react_modules]
        assert "technical_diagram_agent" in module_names
        assert "mermaid_diagram_agent" in module_names

    def test_react_modules_have_correct_tools(self):
        """Test each ReAct module is configured with correct tools."""
        agent = main()

        # Find modules by name
        tech_module = next(
            m for m in agent.react_modules if m.name == "technical_diagram_agent"
        )
        mermaid_module = next(
            m for m in agent.react_modules if m.name == "mermaid_diagram_agent"
        )

        # Verify tool assignments
        assert tech_module.tools == ["draw_technical_diagram"]
        assert mermaid_module.tools == ["draw_mermaid"]

    def test_router_module_configured(self):
        """Test router module is properly configured."""
        agent = main()
        assert agent.router.name == "diagram_router"
        assert agent.router.tools == []  # Router has no tools

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_main_module_is_router(self, initialized_agent):
        """Test that main_module is the initialized router."""
        assert initialized_agent.main_module.__class__.__name__ == "DiagramRouter"


@pytest.mark.integration
class TestDiagramRouterBehavior:
    """Test DiagramRouter routing logic (requires MCP server)."""

    @pytest.fixture
    async def agent(self):
        """Fixture providing agent with MCP connection initialized."""
        agent = main()
        # Initialize MCP connection using context manager
        async with agent:
            yield agent

    @pytest.mark.asyncio
    async def test_router_has_tool_routing_config(self, agent):
        """Test router has TOOL_ROUTING dictionary."""
        router = agent.main_module
        assert hasattr(router, "TOOL_ROUTING")
        assert "draw_technical_diagram" in router.TOOL_ROUTING
        assert "draw_mermaid" in router.TOOL_ROUTING

    @pytest.mark.asyncio
    async def test_router_keyword_mapping_complete(self, agent):
        """Test router built complete keyword_to_tool mapping."""
        router = agent.main_module
        assert hasattr(router, "keyword_to_tool")

        # Verify technical keywords
        assert router.keyword_to_tool["technical"] == "draw_technical_diagram"
        assert router.keyword_to_tool["architecture"] == "draw_technical_diagram"
        assert router.keyword_to_tool["cloud"] == "draw_technical_diagram"

        # Verify mermaid keywords
        assert router.keyword_to_tool["flow"] == "draw_mermaid"
        assert router.keyword_to_tool["sequence"] == "draw_mermaid"

    @pytest.mark.asyncio
    async def test_router_has_both_agents(self, agent):
        """Test router stores references to both specialist agents."""
        router = agent.main_module
        assert hasattr(router, "agents")
        assert "draw_technical_diagram" in router.agents
        assert "draw_mermaid" in router.agents

    @pytest.mark.asyncio
    async def test_router_forward_signature(self, agent):
        """Test router forward() accepts conversation_history and user_request."""
        router = agent.main_module
        import inspect

        sig = inspect.signature(router.forward)
        params = list(sig.parameters.keys())
        assert "conversation_history" in params
        assert "user_request" in params


class TestReActModuleSignatures:
    """Test ReAct module signatures include conversation history."""

    def test_technical_agent_signature(self):
        """Test technical diagram agent has correct signature."""
        agent = main()
        tech_module_config = next(
            m for m in agent.react_modules if m.name == "technical_diagram_agent"
        )
        signature_str = tech_module_config.args[0]

        # Verify signature includes both history and request
        assert "conversation_history" in signature_str
        assert "user_request" in signature_str
        assert "diagram_code" in signature_str
        assert "title" in signature_str

    def test_mermaid_agent_signature(self):
        """Test mermaid agent has correct signature."""
        agent = main()
        mermaid_module_config = next(
            m for m in agent.react_modules if m.name == "mermaid_diagram_agent"
        )
        signature_str = mermaid_module_config.args[0]

        # Verify signature includes both history and request
        assert "conversation_history" in signature_str
        assert "user_request" in signature_str
        assert "diagram_code" in signature_str
        assert "title" in signature_str


@pytest.mark.integration
class TestDspyAgentWithMCPServer:
    """Integration tests requiring MCP server to be running."""

    @pytest.fixture
    async def agent_with_tools(self):
        """Fixture providing agent with MCP tools loaded."""
        agent = main()
        # Initialize MCP connection using context manager
        async with agent:
            yield agent

    @pytest.mark.asyncio
    async def test_agent_can_list_tools(self, agent_with_tools):
        """Test agent can retrieve tools from MCP server."""
        tools_result = await agent_with_tools.list_tools()
        tool_names = [tool.name for tool in tools_result.tools]

        # MCP tools are prefixed with server name
        assert "diagramming__draw_technical_diagram" in tool_names
        assert "diagramming__draw_mermaid" in tool_names

    @pytest.mark.asyncio
    async def test_create_callable_tools_success(self, agent_with_tools):
        """Test _create_callable_tools converts MCP tools to dspy.Tool."""
        dspy_tools = await agent_with_tools._create_callable_tools(
            ["draw_technical_diagram", "draw_mermaid"]
        )

        assert len(dspy_tools) == 2
        assert all(hasattr(tool, "name") for tool in dspy_tools)
        assert all(hasattr(tool, "func") for tool in dspy_tools)
