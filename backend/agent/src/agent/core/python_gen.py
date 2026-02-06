"""Python diagrams generator module - generates validated Python code."""

from pathlib import Path

import dspy
from pydantic import BaseModel

from agent.config import get_configured_lm
from agent.core.validators import PythonCodeValidator, ValidationResult
from agent.signatures import PythonDiagramsSignature


class PythonGenerationResult(BaseModel):
    """Result of Python diagram code generation."""

    diagram_title: str
    python_code: str
    reasoning: str
    validation_notes: str
    validation_result: ValidationResult
    is_valid: bool

    @property
    def code(self) -> str:
        """Alias for python_code for consistency."""
        return self.python_code


def _load_style_guide() -> str:
    """Load the Python diagrams style guide from file.

    Returns:
        Style guide content as string
    """
    style_guide_path = (
        Path(__file__).parent.parent.parent.parent / "data" / "style_guides" / "python_diagrams.md"
    )

    if not style_guide_path.exists():
        # Fallback to basic guide
        return (
            "Generate Python code using the diagrams library. "
            "DO NOT include import statements. "
            "DO NOT use with statement for Diagram context. "
            "Use >> operator to connect nodes."
        )

    return style_guide_path.read_text()


class PythonDiagramsGenerator(dspy.Module):
    """Generator module for Python diagrams library code.

    Uses Chain of Thought reasoning to generate valid Python code for cloud
    architecture diagrams. Includes integrated validation.

    Attributes:
        lm: Configured language model for predictions
        predictor: DSPy ChainOfThought predictor with PythonDiagramsSignature
        validator: PythonCodeValidator instance
        style_guide: Loaded style guide content
    """

    def __init__(self, lm_provider: str | None = None):
        """Initialize the Python diagrams generator.

        Args:
            lm_provider: Optional LM provider name from config.
                        If None, uses the default provider (gemini-flash).
        """
        super().__init__()
        self.lm = get_configured_lm(lm_provider)
        self.predictor = dspy.ChainOfThought(PythonDiagramsSignature)
        self.validator = PythonCodeValidator()
        self.style_guide = _load_style_guide()

    def forward(
        self,
        user_intent: str,
        conversation_context: str = "",
        validation_feedback: str | None = None,
    ) -> PythonGenerationResult:
        """Generate Python diagram code.

        Args:
            user_intent: The user's request describing the architecture
            conversation_context: Previous conversation history (may be empty)
            validation_feedback: Optional feedback from previous validation failure
                                (used for retry attempts)

        Returns:
            PythonGenerationResult with code, title, and validation status

        Example:
            >>> generator = PythonDiagramsGenerator()
            >>> result = generator("Create a 3-tier web app on AWS")
            >>> if result.is_valid:
            ...     print(result.python_code)
        """
        # Enhance user intent with validation feedback if this is a retry
        enhanced_intent = user_intent
        if validation_feedback:
            enhanced_intent = (
                f"{user_intent}\n\n"
                f"PREVIOUS ATTEMPT FAILED VALIDATION:\n{validation_feedback}\n"
                f"Please fix the issues and regenerate."
            )

        # Use configured LM for this prediction
        with dspy.settings.context(lm=self.lm):
            prediction = self.predictor(
                user_intent=enhanced_intent,
                style_guide=self.style_guide,
                conversation_context=conversation_context or "",
            )

        # Validate generated code
        validation_result = self.validator.validate(prediction.python_code)

        return PythonGenerationResult(
            diagram_title=prediction.diagram_title,
            python_code=prediction.python_code,
            reasoning=prediction.reasoning,
            validation_notes=prediction.validation_notes,
            validation_result=validation_result,
            is_valid=validation_result.is_valid,
        )

    def generate_with_retry(
        self,
        user_intent: str,
        conversation_context: str = "",
        max_retries: int = 2,
    ) -> PythonGenerationResult:
        """Generate Python code with automatic retry on validation failure.

        Args:
            user_intent: The user's request describing the architecture
            conversation_context: Previous conversation history (may be empty)
            max_retries: Maximum number of retry attempts (default: 2)

        Returns:
            PythonGenerationResult (may still be invalid after max retries)

        Example:
            >>> generator = PythonDiagramsGenerator()
            >>> result = generator.generate_with_retry("Create AWS architecture")
            >>> print(f"Valid: {result.is_valid}, Attempts: {max_retries + 1}")
        """
        result = self.forward(user_intent, conversation_context)

        if result.is_valid:
            return result

        # Retry with validation feedback
        for attempt in range(max_retries):
            feedback = result.validation_result.get_feedback()
            result = self.forward(user_intent, conversation_context, feedback)

            if result.is_valid:
                return result

        # Return last result even if invalid (caller handles error)
        return result

    def __call__(
        self,
        user_intent: str,
        conversation_context: str = "",
    ) -> PythonGenerationResult:
        """Convenience method to call forward().

        Args:
            user_intent: The user's request describing the architecture
            conversation_context: Previous conversation history (may be empty)

        Returns:
            PythonGenerationResult with generated code and validation
        """
        return self.forward(user_intent, conversation_context)
