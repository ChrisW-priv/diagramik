"""Technical diagram agent optimizer using BootstrapFewShot with mock tools."""

import logging
from pathlib import Path

import dspy

from ..datasets import get_technical_diagram_examples
from ..metrics import iteration_count_metric, technical_format_metric
from ..mock_tools import create_mock_draw_technical_diagram

logger = logging.getLogger(__name__)

SAVE_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "data"
    / "optimized_prompts"
    / "technical_diagram"
)


def _combined_technical_metric(example, prediction, trace=None) -> float:
    """Combined metric: format (0.4) + iterations (0.3) + node validation (0.3)."""
    format_score = technical_format_metric(example, prediction, trace)
    iteration_score = iteration_count_metric(example, prediction, trace)

    # Node validation: check if expected nodes appear in the trajectory
    node_score = _node_presence_score(example, prediction)

    combined = 0.4 * format_score + 0.3 * iteration_score + 0.3 * node_score
    return combined


def _node_presence_score(example, prediction) -> float:
    """Check if expected node names appear in the tool call code."""
    expected_nodes = getattr(example, "expected_node_names", None)
    if not expected_nodes:
        return 1.0  # No expectation, pass

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

    # Check how many expected nodes appear in the code
    found = sum(1 for node in expected_nodes if node in code)
    return found / len(expected_nodes)


def optimize_technical(lm: dspy.LM) -> dspy.Module:
    """Optimize the technical diagram ReAct agent.

    Args:
        lm: Configured DSPy language model.

    Returns:
        Optimized dspy.ReAct module.
    """
    examples = get_technical_diagram_examples()

    # Train/dev split: 12/3
    train_examples = examples[:12]
    dev_examples = examples[12:]

    logger.info(
        "Technical optimization: %d train, %d dev examples",
        len(train_examples),
        len(dev_examples),
    )

    # Create mock tool as dspy.Tool
    mock_fn = create_mock_draw_technical_diagram()
    mock_tool = dspy.Tool(
        func=mock_fn,
        name="draw_technical_diagram",
        desc="Draw a technical architecture diagram using Python diagrams library. "
        "Pass 'title' (string) and 'code' (string of Python code) as arguments.",
        args={
            "title": {"type": "string", "description": "The diagram title"},
            "code": {
                "type": "string",
                "description": "Python code using the diagrams library",
            },
        },
    )

    # Create ReAct module with mock tool
    module = dspy.ReAct(
        "conversation_history, user_request -> diagram_code: str, title: str",
        tools=[mock_tool],
    )

    optimizer = dspy.BootstrapFewShot(
        metric=_combined_technical_metric,
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
                score = _combined_technical_metric(ex, pred)
                total_score += score
            except Exception as e:
                logger.warning("Dev example failed: %s", e)

        dev_score = total_score / len(dev_examples) if dev_examples else 0
        logger.info("Technical dev score: %.2f", dev_score)

    # Save optimized state
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    save_path = SAVE_DIR / "react_agent.json"
    optimized.save(str(save_path))
    logger.info("Saved optimized technical agent to %s", save_path)

    return optimized
