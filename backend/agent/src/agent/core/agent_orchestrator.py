"""Main agent orchestrator - coordinates DSPy modules and MCP tools."""

import json
from pathlib import Path

from fast_agent import FastAgent
from fast_agent.mcp.prompt_serialization import from_json, to_json
from pydantic import BaseModel, Field

from agent.core.mermaid_gen import MermaidGenerator
from agent.core.python_gen import PythonDiagramsGenerator
from agent.core.router import DiagramRouterModule
from agent.exceptions import ClarificationNeeded, CodeGenerationError, MCPToolError
from agent.utils import format_conversation_history

# Path to FastAgent config
CONFIG_PATH = (
    Path(__file__).parent.parent.parent.parent / "config" / "fastagent.config.yaml"
)


class AgentResult(BaseModel):
    """Complete result including response and updated history."""

    diagram_title: str = Field(
        ...,
        description="Title of the diagram",
    )
    media_uri: str = Field(..., description="URI of the generated diagram")
    history_json: str


# Initialize FastAgent with MCP server connection
fast = FastAgent(
    "Diagramming Agent",
    config_path=CONFIG_PATH,
)


async def agent(
    user_instruction: str, previous_history_json: str | None = None
) -> AgentResult:
    """Main agent function - orchestrates diagram generation.

    This function combines DSPy intelligence with FastAgent MCP tool access:
    1. Router decides which tool to use (Python diagrams vs Mermaid)
    2. Generator creates validated code
    3. MCP tool renders the diagram
    4. History is updated and returned

    Args:
        user_instruction: User's natural language diagram request
        previous_history_json: Optional JSON string of previous conversation

    Returns:
        AgentResult with diagram title, media URI, and updated history

    Raises:
        ClarificationNeeded: When request is ambiguous
        CodeGenerationError: When code generation fails after retries
        MCPToolError: When MCP tool call fails

    Example:
        >>> result = await agent("Create AWS 3-tier architecture")
        >>> print(result.diagram_title)
        >>> print(result.media_uri)
    """
    # Initialize DSPy modules
    router = DiagramRouterModule()
    python_gen = PythonDiagramsGenerator()
    mermaid_gen = MermaidGenerator()

    # Format conversation history for DSPy modules
    conversation_context = format_conversation_history(previous_history_json)

    # Step 1: Route the request
    routing = router(user_instruction, conversation_context)

    if routing.tool_choice == "clarify":
        raise ClarificationNeeded(
            routing.clarification_question or "Please clarify your request"
        )

    # Step 2: Generate code based on routing decision
    if routing.tool_choice == "python_diagrams":
        generation = python_gen.generate_with_retry(
            user_instruction, conversation_context, max_retries=2
        )

        if not generation.is_valid:
            raise CodeGenerationError(
                "Failed to generate valid Python code after retries",
                validation_errors=generation.validation_result.errors,
            )

        # Call Python diagrams MCP tool
        tool_name = "draw_technical_diagram"
        tool_params = {
            "title": generation.diagram_title,
            "code": generation.python_code,
        }
    else:  # mermaid
        generation = mermaid_gen.generate_with_retry(
            user_instruction, conversation_context, max_retries=2
        )

        if not generation.is_valid:
            raise CodeGenerationError(
                "Failed to generate valid Mermaid code after retries",
                validation_errors=generation.validation_result.errors,
            )

        # Call Mermaid MCP tool
        tool_name = "draw_mermaid"
        tool_params = {
            "title": generation.diagram_title,
            "code": generation.mermaid_code,
        }

    # Step 3: Call MCP tool through FastAgent
    async with fast.run() as fast_agent:
        # Load previous history if provided
        if previous_history_json:
            try:
                previous_messages = from_json(previous_history_json)
                # Create a simple agent runner
                agent_runner = fast_agent.create_agent(
                    name="diagram_generator",
                    servers=["diagramming"],
                )
                agent_runner.load_message_history(previous_messages)
            except Exception:
                # Start fresh on error
                agent_runner = fast_agent.create_agent(
                    name="diagram_generator",
                    servers=["diagramming"],
                )
        else:
            agent_runner = fast_agent.create_agent(
                name="diagram_generator",
                servers=["diagramming"],
            )

        # Call the MCP tool directly
        try:
            # Send a message that will trigger tool use
            tool_use_message = f"Use the {tool_name} tool with these parameters: {json.dumps(tool_params)}"
            await agent_runner.send(tool_use_message)

            # Extract tool result
            last_tool_call = agent_runner.message_history[-2].tool_results
            tool_result = next(iter(last_tool_call.values())).content[0].text
            last_tool_result = json.loads(tool_result)

            # Extract and serialize updated history
            updated_history = agent_runner.message_history
            history_json = to_json(updated_history)

            return AgentResult(
                diagram_title=last_tool_result.get("title", generation.diagram_title),
                media_uri=last_tool_result.get("uri"),
                history_json=history_json,
            )
        except Exception as e:
            raise MCPToolError(f"Failed to call MCP tool {tool_name}: {e}")
