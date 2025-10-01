"""Configuration validation utilities."""

import logging
from typing import Any, Dict, List, Optional

from kubeagentic.config.schema import AgentConfigSchema, LLMProvider
from kubeagentic.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigValidator:
    """Validate configuration beyond basic schema validation."""

    @staticmethod
    def validate(config: AgentConfigSchema) -> List[str]:
        """
        Perform comprehensive validation on configuration.

        Args:
            config: Parsed configuration schema

        Returns:
            List of warning messages (empty if no warnings)

        Raises:
            ConfigurationError: If configuration has critical errors
        """
        warnings: List[str] = []

        # Validate LLM configuration
        warnings.extend(ConfigValidator._validate_llm_config(config))

        # Validate tools
        warnings.extend(ConfigValidator._validate_tools(config))

        # Validate memory configuration
        warnings.extend(ConfigValidator._validate_memory(config))

        # Validate limits
        warnings.extend(ConfigValidator._validate_limits(config))

        return warnings

    @staticmethod
    def _validate_llm_config(config: AgentConfigSchema) -> List[str]:
        """Validate LLM configuration."""
        warnings: List[str] = []
        agent = config.agent

        # Get LLM configs
        llm_configs = [agent.llm] if agent.llm else agent.llms or []

        for llm_config in llm_configs:
            # Check if API key is required but not provided
            if llm_config.provider in [
                LLMProvider.OPENAI,
                LLMProvider.ANTHROPIC,
                LLMProvider.COHERE,
            ]:
                if not llm_config.api_key:
                    warnings.append(
                        f"No API key provided for {llm_config.provider}. "
                        f"Ensure it's set via environment variable."
                    )

            # Validate temperature
            if llm_config.temperature > 1.5:
                warnings.append(
                    f"High temperature ({llm_config.temperature}) may produce "
                    f"less coherent responses for {llm_config.model}"
                )

            # Validate max_tokens
            if llm_config.max_tokens > 4096:
                warnings.append(
                    f"max_tokens ({llm_config.max_tokens}) is quite high "
                    f"and may increase costs and latency"
                )

        # Validate fallback priorities
        if agent.llms and len(agent.llms) > 1:
            priorities = [llm.priority for llm in agent.llms]
            if len(priorities) != len(set(priorities)):
                raise ConfigurationError(
                    "LLM fallback priorities must be unique. " f"Got: {priorities}"
                )

        return warnings

    @staticmethod
    def _validate_tools(config: AgentConfigSchema) -> List[str]:
        """Validate tools configuration."""
        warnings: List[str] = []
        agent = config.agent

        if not agent.tools:
            warnings.append("No tools configured. Agent will have limited functionality.")
            return warnings

        # Check for duplicate tool names
        tool_names = [tool.name for tool in agent.tools]
        duplicates = [name for name in tool_names if tool_names.count(name) > 1]
        if duplicates:
            raise ConfigurationError(f"Duplicate tool names found: {set(duplicates)}")

        # Validate custom tools
        for tool in agent.tools:
            if tool.type == "custom":
                if not tool.class_path:
                    raise ConfigurationError(
                        f"Custom tool '{tool.name}' must specify 'class_path'"
                    )

            # Warn if tool is disabled
            if not tool.enabled:
                warnings.append(f"Tool '{tool.name}' is disabled")

        return warnings

    @staticmethod
    def _validate_memory(config: AgentConfigSchema) -> List[str]:
        """Validate memory configuration."""
        warnings: List[str] = []
        agent = config.agent

        # Check if max_messages is reasonable
        if agent.memory.max_messages > 50:
            warnings.append(
                f"max_messages ({agent.memory.max_messages}) is quite high. "
                f"This may increase token usage and costs."
            )

        return warnings

    @staticmethod
    def _validate_limits(config: AgentConfigSchema) -> List[str]:
        """Validate resource limits configuration."""
        warnings: List[str] = []
        agent = config.agent

        # Check if limits are reasonable
        if agent.limits.max_tokens_per_request < 100:
            warnings.append(
                f"max_tokens_per_request ({agent.limits.max_tokens_per_request}) "
                f"is very low and may truncate responses"
            )

        if agent.limits.timeout_seconds < 10:
            warnings.append(
                f"timeout_seconds ({agent.limits.timeout_seconds}) is very short "
                f"and may cause premature timeouts"
            )

        # Check budget settings
        if agent.limits.daily_token_budget:
            max_req_tokens = agent.limits.max_tokens_per_request
            max_req_per_min = agent.limits.max_requests_per_minute
            daily_max = max_req_tokens * max_req_per_min * 60 * 24

            if agent.limits.daily_token_budget < daily_max:
                warnings.append(
                    f"daily_token_budget ({agent.limits.daily_token_budget}) may be "
                    f"reached quickly with current rate limits. "
                    f"Theoretical maximum: {daily_max:,} tokens/day"
                )

        return warnings

    @staticmethod
    def check_environment(config: AgentConfigSchema) -> Dict[str, Any]:
        """
        Check if required environment variables and dependencies are available.

        Args:
            config: Parsed configuration schema

        Returns:
            Dictionary with check results
        """
        results: Dict[str, Any] = {
            "api_keys": {},
            "dependencies": {},
            "warnings": [],
        }

        # Check for required API keys
        agent = config.agent
        llm_configs = [agent.llm] if agent.llm else agent.llms or []

        for llm_config in llm_configs:
            provider = llm_config.provider
            has_key = llm_config.api_key is not None

            # Check environment variables as fallback
            if not has_key:
                import os

                env_var_map = {
                    LLMProvider.OPENAI: "OPENAI_API_KEY",
                    LLMProvider.ANTHROPIC: "ANTHROPIC_API_KEY",
                    LLMProvider.AZURE_OPENAI: "AZURE_OPENAI_API_KEY",
                    LLMProvider.COHERE: "COHERE_API_KEY",
                    LLMProvider.GOOGLE: "GOOGLE_API_KEY",
                }

                env_var = env_var_map.get(provider)
                if env_var:
                    has_key = os.getenv(env_var) is not None

            results["api_keys"][provider] = has_key

            if not has_key:
                results["warnings"].append(
                    f"No API key found for {provider}. "
                    f"Agent may fail at runtime."
                )

        return results 