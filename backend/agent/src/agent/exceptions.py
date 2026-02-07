"""Exception classes for the agent module."""


class AgentException(Exception):
    """Base exception for agent errors."""

    pass


class ClarificationNeeded(AgentException):
    """Raised when the user request is ambiguous and needs clarification.

    The clarification_question attribute contains the question to ask the user.
    """

    def __init__(self, clarification_question: str):
        """Initialize with clarification question.

        Args:
            clarification_question: Question to ask the user
        """
        self.clarification_question = clarification_question
        super().__init__(clarification_question)

    def __str__(self) -> str:
        """Return the clarification question."""
        return self.clarification_question


class CodeGenerationError(AgentException):
    """Raised when code generation fails after retries.

    The validation_errors attribute contains details about what went wrong.
    """

    def __init__(self, message: str, validation_errors: list[str] | None = None):
        """Initialize with error message and optional validation errors.

        Args:
            message: Error message
            validation_errors: List of validation error messages
        """
        self.validation_errors = validation_errors or []
        super().__init__(message)

    def __str__(self) -> str:
        """Return formatted error message."""
        msg = super().__str__()
        if self.validation_errors:
            msg += "\n\nValidation errors:\n" + "\n".join(
                f"  - {err}" for err in self.validation_errors
            )
        return msg


class MCPToolError(AgentException):
    """Raised when MCP tool call fails."""

    pass
