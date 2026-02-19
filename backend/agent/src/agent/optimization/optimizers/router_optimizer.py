"""Router classifier optimizer using BootstrapFewShot."""

import logging
from pathlib import Path
from typing import Literal

import dspy

from agent.dspy_modules.agent_router import DiagramRouter

from ..datasets import get_router_examples
from ..metrics import router_accuracy_metric

logger = logging.getLogger(__name__)

SAVE_DIR = (
    Path(__file__).parent.parent.parent.parent.parent
    / "data"
    / "optimized_prompts"
    / "router"
)


class RouterClassifierWrapper(dspy.Module):
    """Wraps just the DiagramRouter classifier for isolated optimization.

    Mirrors DiagramRouter.classifier but without the full routing machinery,
    so we can optimize the classification step independently.
    """

    def __init__(self):
        super().__init__()

        # Build the same Literal type and classifier as DiagramRouter
        all_keywords = []
        for keywords in DiagramRouter.TOOL_ROUTING.values():
            all_keywords.extend(keywords)

        literal_type = Literal[tuple(all_keywords)]

        self.classifier = dspy.ChainOfThought(
            dspy.Signature(
                {
                    "conversation_history": dspy.InputField(),
                    "user_request": dspy.InputField(),
                },
                f"Classify the diagram request type based on keywords: {', '.join(all_keywords)}",
            ).append("diagram_type", dspy.OutputField(), type_=literal_type)
        )

    def forward(self, conversation_history, user_request):
        return self.classifier(
            conversation_history=conversation_history,
            user_request=user_request,
        )


def optimize_router(lm: dspy.LM) -> dspy.Module:
    """Optimize the router classifier module.

    Args:
        lm: Configured DSPy language model.

    Returns:
        Optimized RouterClassifierWrapper module.
    """
    examples = get_router_examples()

    # Train/dev split: 24/6
    train_examples = examples[:24]
    dev_examples = examples[24:]

    logger.info(
        "Router optimization: %d train, %d dev examples",
        len(train_examples),
        len(dev_examples),
    )

    module = RouterClassifierWrapper()

    optimizer = dspy.BootstrapFewShot(
        metric=router_accuracy_metric,
        max_bootstrapped_demos=4,
        max_labeled_demos=8,
    )

    with dspy.context(lm=lm):
        optimized = optimizer.compile(
            module,
            trainset=train_examples,
        )

    # Evaluate on dev set
    with dspy.context(lm=lm):
        correct = 0
        for ex in dev_examples:
            pred = optimized(
                conversation_history=ex.conversation_history,
                user_request=ex.user_request,
            )
            score = router_accuracy_metric(ex, pred)
            correct += score

        dev_accuracy = correct / len(dev_examples) if dev_examples else 0
        logger.info(
            "Router dev accuracy: %.2f (%d/%d)",
            dev_accuracy,
            correct,
            len(dev_examples),
        )

    # Save optimized state
    SAVE_DIR.mkdir(parents=True, exist_ok=True)
    save_path = SAVE_DIR / "classifier.json"
    optimized.save(str(save_path))
    logger.info("Saved optimized router to %s", save_path)

    return optimized
