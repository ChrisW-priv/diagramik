"""Mermaid diagram generator module - generates validated Mermaid syntax."""

from pathlib import Path

import dspy
from pydantic import BaseModel

from agent.config import get_configured_lm
from agent.core.validators import MermaidCodeValidator, ValidationResult
from agent.signatures import MermaidSignature


class MermaidGenerationResult(BaseModel):
    """Result of Mermaid diagram code generation."""

    diagram_title: str
    diagram_type: str
    mermaid_code: str
    reasoning: str
    validation_notes: str
    validation_result: ValidationResult
    is_valid: bool

    @property
    def code(self) -> str:
        """Alias for mermaid_code for consistency."""
        return self.mermaid_code


def _load_style_guide() -> str:
    """Load the Mermaid diagram style guide from file.

    Returns:
        Style guide content as string
    """
    style_guide_path = (
        Path(__file__).parent.parent.parent.parent
        / "data"
        / "style_guides"
        / "mermaid.md"
    )

    if not style_guide_path.exists():
        # Fallback to basic guide
        return (
            "Generate valid Mermaid diagram syntax. "
            "Start with diagram type declaration (flowchart TD, sequenceDiagram, etc.). "
            "Use proper syntax for the chosen diagram type."
        )

    return style_guide_path.read_text()


class MermaidGenerator(dspy.Module):
    """Generator module for Mermaid diagram syntax.

    Uses Chain of Thought reasoning to generate valid Mermaid code for
    flowcharts, sequence diagrams, ER diagrams, etc. Includes integrated validation.

    Attributes:
        lm: Configured language model for predictions
        predictor: DSPy ChainOfThought predictor with MermaidSignature
        validator: MermaidCodeValidator instance
        style_guide: Loaded style guide content
    """

    def __init__(self, lm_provider: str | None = None):
        """Initialize the Mermaid generator.

        Args:
            lm_provider: Optional LM provider name from config.
                        If None, uses the default provider (gemini-flash).
        """
        super().__init__()
        self.lm = get_configured_lm(lm_provider)
        self.predictor = dspy.ChainOfThought(MermaidSignature)
        self.validator = MermaidCodeValidator()
        self.style_guide = _load_style_guide()

    def forward(
        self,
        user_intent: str,
        conversation_context: str = "",
        validation_feedback: str | None = None,
    ) -> MermaidGenerationResult:
        """Generate Mermaid diagram code.

        Args:
            user_intent: The user's request describing the diagram
            conversation_context: Previous conversation history (may be empty)
            validation_feedback: Optional feedback from previous validation failure
                                (used for retry attempts)

        Returns:
            MermaidGenerationResult with code, title, type, and validation status

        Example:
            >>> generator = MermaidGenerator()
            >>> result = generator("Create a login flow diagram")
            >>> if result.is_valid:
            ...     print(result.mermaid_code)
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
        validation_result = self.validator.validate(prediction.mermaid_code)

        return MermaidGenerationResult(
            diagram_title=prediction.diagram_title,
            diagram_type=prediction.diagram_type,
            mermaid_code=prediction.mermaid_code,
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
    ) -> MermaidGenerationResult:
        """Generate Mermaid code with automatic retry on validation failure.

        Args:
            user_intent: The user's request describing the diagram
            conversation_context: Previous conversation history (may be empty)
            max_retries: Maximum number of retry attempts (default: 2)

        Returns:
            MermaidGenerationResult (may still be invalid after max retries)

        Example:
            >>> generator = MermaidGenerator()
            >>> result = generator.generate_with_retry("Create a sequence diagram")
            >>> print(f"Valid: {result.is_valid}")
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
    ) -> MermaidGenerationResult:
        """Convenience method to call forward().

        Args:
            user_intent: The user's request describing the diagram
            conversation_context: Previous conversation history (may be empty)

        Returns:
            MermaidGenerationResult with generated code and validation
        """
        return self.forward(user_intent, conversation_context)
