"""Fallback agent examples for DSPy optimization.

Trivia/off-topic requests that should trigger a diagram-only response.
"""

import dspy


def get_fallback_examples() -> list[dspy.Example]:
    """Get 10 fallback examples (off-topic requests).

    Returns:
        List of dspy.Example with conversation_history, user_request.
    """
    requests = [
        "What is the mitochondria?",
        "Who won the 2022 FIFA World Cup?",
        "Solve the equation 2x + 5 = 15",
        "Write a haiku about spring",
        "What is the population of Japan?",
        "Explain how photosynthesis works",
        "Tell me a joke",
        "What is the fastest animal on Earth?",
        "Translate 'hello' to French",
        "How do I cook pasta?",
    ]

    examples = []
    for req in requests:
        examples.append(
            dspy.Example(
                conversation_history="",
                user_request=req,
            ).with_inputs("conversation_history", "user_request")
        )

    return examples
