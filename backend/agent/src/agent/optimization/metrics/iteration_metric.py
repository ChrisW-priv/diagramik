"""Iteration count metric for DSPy optimization.

Fewer ReAct iterations = better (the agent found the solution faster).
"""


def iteration_count_metric(example, prediction, trace=None) -> float:
    """Score based on number of ReAct iterations.

    Counts thought_N entries in prediction.trajectory.

    Args:
        example: dspy.Example (unused for this metric).
        prediction: ReAct prediction with trajectory dict.
        trace: Optional trace (unused).

    Returns:
        1.0 for 1 iteration, 0.5 for 2, 0.25 for 3+, 0.0 if no trajectory.
    """
    trajectory = getattr(prediction, "trajectory", None)
    if not trajectory:
        return 0.0

    # Count thought entries (thought_0, thought_1, etc.)
    thought_count = sum(
        1 for key in trajectory if isinstance(key, str) and key.startswith("thought_")
    )

    if thought_count == 0:
        return 0.0
    elif thought_count == 1:
        return 1.0
    elif thought_count == 2:
        return 0.5
    else:
        return 0.25
