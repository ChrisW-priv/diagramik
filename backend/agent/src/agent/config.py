"""Configuration module for LM providers in DSPy modules."""

from pathlib import Path
from typing import Any

import dspy
import yaml


def get_configured_lm(provider_name: str | None = None) -> dspy.LM:
    """Get configured LM for DSPy modules.

    Args:
        provider_name: Name of provider from lm_providers.yaml.
                      If None, uses the default provider.

    Returns:
        Configured dspy.LM instance

    Raises:
        ValueError: If provider_name is unknown or config file not found
        FileNotFoundError: If lm_providers.yaml doesn't exist

    Example:
        >>> # Use default (Gemini Flash)
        >>> lm = get_configured_lm()
        >>>
        >>> # Use specific provider
        >>> lm = get_configured_lm("gemini-pro")
    """
    # Find config file relative to this module
    config_path = Path(__file__).parent.parent.parent / "config" / "lm_providers.yaml"

    if not config_path.exists():
        raise FileNotFoundError(
            f"LM provider config not found at {config_path}. "
            "Ensure config/lm_providers.yaml exists."
        )

    with open(config_path) as f:
        config = yaml.safe_load(f)

    providers: dict[str, dict[str, Any]] = config.get("providers", {})

    if not providers:
        raise ValueError("No providers configured in lm_providers.yaml")

    # Find default provider or use specified
    if provider_name is None:
        provider_name = next(
            (name for name, conf in providers.items() if conf.get("default")),
            "gemini-flash",  # fallback
        )

    if provider_name not in providers:
        available = ", ".join(providers.keys())
        raise ValueError(f"Unknown provider: {provider_name}. Available providers: {available}")

    provider_config = providers[provider_name]

    # Create DSPy LM instance
    return dspy.LM(
        model=provider_config["model"],
        max_tokens=provider_config.get("max_tokens", 2000),
        temperature=provider_config.get("temperature", 0.7),
    )


def get_provider_list() -> list[str]:
    """Get list of available provider names.

    Returns:
        List of provider names from config

    Example:
        >>> providers = get_provider_list()
        >>> print(providers)
        ['gemini-flash', 'gemini-pro']
    """
    config_path = Path(__file__).parent.parent.parent / "config" / "lm_providers.yaml"

    if not config_path.exists():
        return []

    with open(config_path) as f:
        config = yaml.safe_load(f)

    return list(config.get("providers", {}).keys())
