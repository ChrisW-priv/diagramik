"""DSPy signature for the diagram router module."""

from typing import Literal

import dspy


class DiagramRouterSignature(dspy.Signature):
    """Analyze user request and select the appropriate diagramming tool.

    The router decides between:
    - python_diagrams: For cloud architecture, infrastructure, deployment diagrams
    - mermaid: For flowcharts, sequence diagrams, ER diagrams, state diagrams
    - clarify: When the request is ambiguous and needs clarification
    """

    user_request: str = dspy.InputField(desc="The user's natural language diagram request")

    conversation_history: str = dspy.InputField(
        desc="Previous conversation context (formatted text, may be empty for first request)"
    )

    # Output fields
    reasoning: str = dspy.OutputField(
        desc=(
            "Step-by-step analysis of the diagram type needed. Consider: "
            "1) What is the user trying to visualize? "
            "2) Is this about cloud/infrastructure (python_diagrams) or process/flow (mermaid)? "
            "3) Is the request clear enough to generate a diagram?"
        )
    )

    tool_choice: Literal["python_diagrams", "mermaid", "clarify"] = dspy.OutputField(
        desc=(
            "Selected tool: "
            "'python_diagrams' for cloud architecture, AWS/GCP/Azure diagrams, deployment topology; "
            "'mermaid' for flowcharts, sequence diagrams, ER diagrams, state machines, timelines; "
            "'clarify' if the request is too ambiguous or vague to determine the diagram type"
        )
    )

    clarification_question: str = dspy.OutputField(
        desc=(
            "Question to ask the user if tool_choice is 'clarify'. "
            "Should be specific and help narrow down the diagram type. "
            "Leave empty if tool_choice is not 'clarify'."
        )
    )
