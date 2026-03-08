"""Fallback quality metric for DSPy optimization.

Checks that fallback responses appropriately indicate the agent
is specialized for diagram generation.
"""

import re


def fallback_quality_metric(example, prediction, trace=None) -> float:
    """Check that fallback response mentions diagram capability and indicates limitation.

    Args:
        example: dspy.Example (unused).
        prediction: FallbackAgent prediction with response field.
        trace: Optional trace (unused).

    Returns:
        1.0 if mentions diagrams AND indicates limitation,
        0.5 if only mentions diagrams,
        0.0 otherwise.
    """
    response = getattr(prediction, "response", "")
    if not response:
        return 0.0

    response_lower = response.lower()

    # Check if response mentions diagrams/diagramming
    mentions_diagrams = bool(re.search(r"\bdiagram", response_lower))

    # Check if response indicates limitation/specialization
    limitation_patterns = [
        r"\bonly\b",
        r"\bcannot\b",
        r"\bcan't\b",
        r"\bunable\b",
        r"\bspecializ",
        r"\bdesigned (for|to)\b",
        r"\bfocus(ed)? on\b",
        r"\bnot able\b",
        r"\boutside.{0,20}scope\b",
        r"\blimited to\b",
    ]
    indicates_limitation = any(
        re.search(pattern, response_lower) for pattern in limitation_patterns
    )

    if mentions_diagrams and indicates_limitation:
        return 1.0
    elif mentions_diagrams:
        return 0.5
    else:
        return 0.0
