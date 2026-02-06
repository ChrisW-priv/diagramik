"""Diagram router module - selects appropriate tool based on user intent."""

from typing import Literal

import dspy
from pydantic import BaseModel

from agent.config import get_configured_lm
from agent.signatures import DiagramRouterSignature


class RouterResult(BaseModel):
    """Result of routing decision."""

    tool_choice: Literal["python_diagrams", "mermaid", "clarify"]
    reasoning: str
    clarification_question: str | None = None


class DiagramRouterModule(dspy.Module):
    """Router module that selects the appropriate diagram generation tool.

    Uses Chain of Thought reasoning to analyze the user's request and decide
    between Python diagrams (for cloud architecture) or Mermaid (for flows/sequences).

    Attributes:
        lm: Configured language model for predictions
        predictor: DSPy ChainOfThought predictor with DiagramRouterSignature
    """

    def __init__(self, lm_provider: str | None = None):
        """Initialize the router module.

        Args:
            lm_provider: Optional LM provider name from config.
                        If None, uses the default provider (gemini-flash).
        """
        super().__init__()
        self.lm = get_configured_lm(lm_provider)
        self.predictor = dspy.ChainOfThought(DiagramRouterSignature)

    def forward(
        self,
        user_request: str,
        conversation_history: str = "",
    ) -> RouterResult:
        """Route the user request to the appropriate tool.

        Args:
            user_request: The user's natural language diagram request
            conversation_history: Formatted previous conversation (may be empty)

        Returns:
            RouterResult with tool_choice, reasoning, and optional clarification

        Example:
            >>> router = DiagramRouterModule()
            >>> result = router("Create a 3-tier web app architecture on AWS")
            >>> print(result.tool_choice)
            'python_diagrams'
        """
        # Use configured LM for this prediction
        with dspy.settings.context(lm=self.lm):
            prediction = self.predictor(
                user_request=user_request,
                conversation_history=conversation_history or "",
            )

        return RouterResult(
            tool_choice=prediction.tool_choice,
            reasoning=prediction.reasoning,
            clarification_question=prediction.clarification_question
            if prediction.tool_choice == "clarify"
            else None,
        )

    def __call__(
        self,
        user_request: str,
        conversation_history: str = "",
    ) -> RouterResult:
        """Convenience method to call forward().

        Args:
            user_request: The user's natural language diagram request
            conversation_history: Formatted previous conversation (may be empty)

        Returns:
            RouterResult with routing decision
        """
        return self.forward(user_request, conversation_history)
