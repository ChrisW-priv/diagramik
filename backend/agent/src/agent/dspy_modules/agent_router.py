from typing import Literal

import dspy


class DiagramRouter(dspy.Module):
    """
    Routes diagram requests to appropriate specialist agent.

    Uses keyword-based routing with dynamically constructed Literal types
    to ensure type-safe routing decisions. Includes fallback agent for
    requests that cannot be fulfilled.
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
        "fallback": [
            "clarify",
            "error",
            "unknown",
            "cannot",
            "unable",
            "help",
        ],
    }

    def __init__(self, technical_diagram_agent, mermaid_diagram_agent, fallback_agent):
        super().__init__()

        # Store module references with tool mapping
        self.agents = {
            "draw_technical_diagram": technical_diagram_agent,
            "draw_mermaid": mermaid_diagram_agent,
            "fallback": fallback_agent,
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
        tool_name = self.keyword_to_tool.get(diagram_type, "fallback")

        # Get agent and pass both history and request
        agent = self.agents[tool_name]
        return agent(
            conversation_history=conversation_history, user_request=user_request
        )
