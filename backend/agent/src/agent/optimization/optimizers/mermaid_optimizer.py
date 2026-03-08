"""Mermaid diagram agent optimizer using BootstrapFewShot with mock tools."""

import logging
from pathlib import Path

import dspy

from ..datasets import get_mermaid_examples
from ..metrics import iteration_count_metric, mermaid_format_metric
from ..mock_tools import create_mock_draw_mermaid

logger = logging.getLogger(__name__)

SAVE_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "data"
    / "optimized_prompts"
    / "mermaid"
)


def _mermaid_type_score(example, prediction) -> float:
    """Check if the generated mermaid code starts with the expected type prefix."""
    expected_type = getattr(example, "expected_mermaid_type", None)
    if not expected_type:
        return 1.0

    trajectory = getattr(prediction, "trajectory", None)
    if not trajectory:
        return 0.0

    # Extract code from trajectory
    code = ""
    for key, value in trajectory.items():
        if isinstance(key, str) and key.startswith("tool_args_"):
            if isinstance(value, dict) and "code" in value:
                code = value["code"]
                break

    if not code:
        return 0.0

    return 1.0 if code.strip().startswith(expected_type) else 0.0


def _combined_mermaid_metric(example, prediction, trace=None) -> float:
    """Combined metric: format (0.4) + iterations (0.3) + type correctness (0.3)."""
    format_score = mermaid_format_metric(example, prediction, trace)
    iteration_score = iteration_count_metric(example, prediction, trace)
    type_score = _mermaid_type_score(example, prediction)

    combined = 0.4 * format_score + 0.3 * iteration_score + 0.3 * type_score
    return combined


def optimize_mermaid(lm: dspy.LM) -> dspy.Module:
    """Optimize the mermaid diagram ReAct agent.

    Args:
        lm: Configured DSPy language model.

    Returns:
        Optimized dspy.ReAct module.
    """
    examples = get_mermaid_examples()

    # Train/dev split: 18/6
    train_examples = examples[:18]
    dev_examples = examples[18:]

    logger.info(
        "Mermaid optimization: %d train, %d dev examples",
        len(train_examples),
        len(dev_examples),
    )

    # Create mock tool as dspy.Tool
    mock_fn = create_mock_draw_mermaid()
    mock_tool = dspy.Tool(
        func=mock_fn,
        name="draw_mermaid",
        desc="Draw a diagram using Mermaid syntax. "
        "Pass 'title' (string) and 'code' (string of mermaid diagram code) as arguments.",
        args={
            "title": {"type": "string", "description": "The diagram title"},
            "code": {
                "type": "string",
                "description": "Mermaid diagram code",
            },
        },
    )

    # Create ReAct module with mock tool
    module = dspy.ReAct(
        "conversation_history, user_request -> diagram_code: str, title: str",
        tools=[mock_tool],
    )

    optimizer = dspy.BootstrapFewShot(
        metric=_combined_mermaid_metric,
        max_bootstrapped_demos=3,
        max_labeled_demos=6,
    )

    with dspy.context(lm=lm):
        optimized = optimizer.compile(
            module,
            trainset=train_examples,
        )

    # Evaluate on dev set
    with dspy.context(lm=lm):
        total_score = 0
        for ex in dev_examples:
            try:
                pred = optimized(
                    conversation_history=ex.conversation_history,
                    user_request=ex.user_request,
                )
                score = _combined_mermaid_metric(ex, pred)
                total_score += score
            except Exception as e:
                logger.warning("Dev example failed: %s", e)

        dev_score = total_score / len(dev_examples) if dev_examples else 0
        logger.info("Mermaid dev score: %.2f", dev_score)

    # Save optimized state
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    save_path = SAVE_DIR / "react_agent.json"
    optimized.save(str(save_path))
    logger.info("Saved optimized mermaid agent to %s", save_path)

    return optimized
