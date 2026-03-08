"""Fallback agent optimizer using BootstrapFewShot."""

import logging
from pathlib import Path

import dspy

from agent.dspy_modules.fallback_agent import FallbackAgent

from ..datasets import get_fallback_examples
from ..metrics import fallback_quality_metric

logger = logging.getLogger(__name__)

SAVE_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "data"
    / "optimized_prompts"
    / "fallback"
)


def optimize_fallback(lm: dspy.LM) -> dspy.Module:
    """Optimize the fallback agent module.

    Args:
        lm: Configured DSPy language model.

    Returns:
        Optimized FallbackAgent module.
    """
    examples = get_fallback_examples()

    # Train/dev split: 7/3
    train_examples = examples[:7]
    dev_examples = examples[7:]

    logger.info(
        "Fallback optimization: %d train, %d dev examples",
        len(train_examples),
        len(dev_examples),
    )

    module = FallbackAgent()

    optimizer = dspy.BootstrapFewShot(
        metric=fallback_quality_metric,
        max_bootstrapped_demos=3,
        max_labeled_demos=5,
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
                score = fallback_quality_metric(ex, pred)
                total_score += score
            except Exception as e:
                logger.warning("Dev example failed: %s", e)

        dev_score = total_score / len(dev_examples) if dev_examples else 0
        logger.info("Fallback dev score: %.2f", dev_score)

    # Save optimized state
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    save_path = SAVE_DIR / "predict_agent.json"
    optimized.save(str(save_path))
    logger.info("Saved optimized fallback agent to %s", save_path)

    return optimized
