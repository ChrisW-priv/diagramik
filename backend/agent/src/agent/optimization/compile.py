"""CLI entry point for DSPy module optimization.

Usage:
    python -m agent.optimization.compile              # all modules
    python -m agent.optimization.compile router        # router only
    python -m agent.optimization.compile technical     # technical diagram only
    python -m agent.optimization.compile mermaid       # mermaid only
    python -m agent.optimization.compile fallback      # fallback only
"""

import logging
import sys
from pathlib import Path

import mlflow

from agent.config import get_configured_lm

from .optimizers import (
    optimize_fallback,
    optimize_mermaid,
    optimize_router,
    optimize_technical,
)

# MLflow tracking directory (local, no server needed)
MLFLOW_DIR = Path(__file__).parent.parent.parent.parent / "data" / "mlflow"

logger = logging.getLogger(__name__)

TARGETS = {
    "router": ("router", optimize_router),
    "technical": ("technical_diagram", optimize_technical),
    "mermaid": ("mermaid", optimize_mermaid),
    "fallback": ("fallback", optimize_fallback),
}


def setup_mlflow():
    """Configure MLflow for local file-based tracking."""
    MLFLOW_DIR.mkdir(parents=True, exist_ok=True)
    tracking_uri = f"file://{MLFLOW_DIR.resolve()}"
    mlflow.set_tracking_uri(tracking_uri)
    logger.info("MLflow tracking URI: %s", tracking_uri)


def run_optimization(target: str, lm):
    """Run optimization for a single target.

    Args:
        target: One of 'router', 'technical', 'mermaid', 'fallback'.
        lm: Configured DSPy language model.
    """
    if target not in TARGETS:
        logger.error("Unknown target: %s. Available: %s", target, list(TARGETS.keys()))
        return

    experiment_name, optimize_fn = TARGETS[target]

    mlflow.set_experiment(experiment_name)

    with mlflow.start_run(run_name=f"optimize_{target}"):
        mlflow.log_param("target", target)
        mlflow.log_param("model", lm.model)

        logger.info("Starting optimization for: %s", target)
        optimize_fn(lm)

        # Log the save path as artifact
        save_dir = (
            Path(__file__).parent.parent.parent.parent / "data" / "optimized_prompts"
        )
        if save_dir.exists():
            for json_file in save_dir.rglob("*.json"):
                if target in str(json_file) or experiment_name in str(json_file):
                    mlflow.log_artifact(str(json_file))

        logger.info("Completed optimization for: %s", target)


def main():
    """Main entry point for CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    setup_mlflow()

    lm = get_configured_lm()
    logger.info("Using LM: %s", lm.model)

    # Parse target argument
    targets = sys.argv[1:] if len(sys.argv) > 1 else list(TARGETS.keys())

    for target in targets:
        if target not in TARGETS:
            logger.error(
                "Unknown target: '%s'. Available: %s", target, list(TARGETS.keys())
            )
            sys.exit(1)

    for target in targets:
        run_optimization(target, lm)

    logger.info("All optimizations complete.")


if __name__ == "__main__":
    main()
