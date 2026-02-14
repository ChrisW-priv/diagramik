import dspy


class FallbackAgent(dspy.Module):
    """Handles requests that cannot be fulfilled with diagram generation."""

    def __init__(self, tools=None):
        """
        Initialize fallback agent.

        Args:
            tools: Ignored. Fallback agent doesn't use tools.
        """
        super().__init__()
        self.responder = dspy.Predict(
            "conversation_history, user_request -> response: str"
        )

    def forward(self, conversation_history, user_request):
        """Generate a helpful clarification or error message."""
        return self.responder(
            conversation_history=conversation_history, user_request=user_request
        )
