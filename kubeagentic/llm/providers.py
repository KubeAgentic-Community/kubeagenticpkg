"""LLM provider management utilities."""

import logging
from typing import Any, List

from kubeagentic.config.schema import LLMConfig
from kubeagentic.exceptions import LLMError
from kubeagentic.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


def get_llm_provider(config: LLMConfig) -> Any:
    """
    Get LLM provider instance from configuration.

    Args:
        config: LLM configuration

    Returns:
        Initialized LLM instance

    Raises:
        LLMError: If provider initialization fails
    """
    return LLMFactory.create(config)


def get_llm_with_fallback(configs: List[LLMConfig]) -> Any:
    """
    Get LLM provider with fallback support.

    Attempts to initialize LLMs in order of priority.
    Returns the first successfully initialized provider.

    Args:
        configs: List of LLM configurations sorted by priority

    Returns:
        Initialized LLM instance

    Raises:
        LLMError: If all providers fail to initialize
    """
    if not configs:
        raise LLMError("No LLM configurations provided")

    # Sort by priority (lower is higher priority)
    sorted_configs = sorted(configs, key=lambda c: c.priority)

    errors = []
    for config in sorted_configs:
        try:
            llm = LLMFactory.create(config)
            logger.info(
                f"Successfully initialized LLM: {config.provider}/{config.model} "
                f"(priority: {config.priority})"
            )
            return llm
        except Exception as e:
            error_msg = f"{config.provider}/{config.model}: {str(e)}"
            errors.append(error_msg)
            logger.warning(f"Failed to initialize LLM {error_msg}, trying fallback...")

    # All providers failed
    error_summary = "\n  - ".join(errors)
    raise LLMError(
        f"All LLM providers failed to initialize:\n  - {error_summary}"
    ) 