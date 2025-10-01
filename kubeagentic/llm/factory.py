"""Factory for creating LLM provider instances."""

import logging
import os
from typing import Any, Dict, Optional

from langchain_anthropic import ChatAnthropic
from langchain_community.chat_models import ChatOllama
from langchain_openai import AzureChatOpenAI, ChatOpenAI

from kubeagentic.config.schema import LLMConfig, LLMProvider
from kubeagentic.exceptions import LLMError

logger = logging.getLogger(__name__)


class LLMFactory:
    """Factory for creating LLM instances from configuration."""

    @staticmethod
    def create(config: LLMConfig) -> Any:
        """
        Create an LLM instance from configuration.

        Args:
            config: LLM configuration

        Returns:
            Initialized LLM instance

        Raises:
            LLMError: If provider is unsupported or initialization fails
        """
        try:
            provider = config.provider

            if provider == LLMProvider.OPENAI:
                return LLMFactory._create_openai(config)
            elif provider == LLMProvider.ANTHROPIC:
                return LLMFactory._create_anthropic(config)
            elif provider == LLMProvider.OLLAMA:
                return LLMFactory._create_ollama(config)
            elif provider == LLMProvider.AZURE_OPENAI:
                return LLMFactory._create_azure_openai(config)
            elif provider == LLMProvider.VLLM:
                return LLMFactory._create_vllm(config)
            else:
                raise LLMError(f"Unsupported LLM provider: {provider}")

        except Exception as e:
            logger.error(f"Failed to create LLM instance for {config.provider}: {e}")
            raise LLMError(f"Failed to initialize {config.provider}: {e}") from e

    @staticmethod
    def _create_openai(config: LLMConfig) -> ChatOpenAI:
        """Create OpenAI LLM instance."""
        api_key = config.api_key or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise LLMError("OpenAI API key not provided")

        kwargs: Dict[str, Any] = {
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "api_key": api_key,
            "timeout": config.timeout,
            "max_retries": config.max_retries,
        }

        if config.api_base:
            kwargs["base_url"] = config.api_base

        if config.stop:
            kwargs["stop"] = config.stop

        # Add any extra parameters
        kwargs.update(config.extra)

        logger.info(f"Initializing OpenAI LLM: {config.model}")
        return ChatOpenAI(**kwargs)

    @staticmethod
    def _create_anthropic(config: LLMConfig) -> ChatAnthropic:
        """Create Anthropic LLM instance."""
        api_key = config.api_key or os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise LLMError("Anthropic API key not provided")

        kwargs: Dict[str, Any] = {
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "api_key": api_key,
            "timeout": config.timeout,
            "max_retries": config.max_retries,
        }

        if config.api_base:
            kwargs["base_url"] = config.api_base

        if config.stop:
            kwargs["stop_sequences"] = config.stop

        # Add any extra parameters
        kwargs.update(config.extra)

        logger.info(f"Initializing Anthropic LLM: {config.model}")
        return ChatAnthropic(**kwargs)

    @staticmethod
    def _create_ollama(config: LLMConfig) -> ChatOllama:
        """Create Ollama LLM instance."""
        kwargs: Dict[str, Any] = {
            "model": config.model,
            "temperature": config.temperature,
        }

        if config.api_base:
            kwargs["base_url"] = config.api_base
        else:
            kwargs["base_url"] = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

        if config.stop:
            kwargs["stop"] = config.stop

        # Add any extra parameters
        kwargs.update(config.extra)

        logger.info(f"Initializing Ollama LLM: {config.model}")
        return ChatOllama(**kwargs)

    @staticmethod
    def _create_azure_openai(config: LLMConfig) -> AzureChatOpenAI:
        """Create Azure OpenAI LLM instance."""
        api_key = config.api_key or os.getenv("AZURE_OPENAI_API_KEY")
        if not api_key:
            raise LLMError("Azure OpenAI API key not provided")

        # Azure requires deployment name and endpoint
        deployment_name = config.extra.get("deployment_name")
        if not deployment_name:
            raise LLMError("Azure OpenAI requires 'deployment_name' in extra config")

        endpoint = config.api_base or os.getenv("AZURE_OPENAI_ENDPOINT")
        if not endpoint:
            raise LLMError("Azure OpenAI endpoint not provided")

        kwargs: Dict[str, Any] = {
            "deployment_name": deployment_name,
            "azure_endpoint": endpoint,
            "api_key": api_key,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "timeout": config.timeout,
            "max_retries": config.max_retries,
        }

        # API version
        api_version = config.extra.get("api_version", "2024-02-15-preview")
        kwargs["api_version"] = api_version

        logger.info(f"Initializing Azure OpenAI LLM: {deployment_name}")
        return AzureChatOpenAI(**kwargs)

    @staticmethod
    def _create_vllm(config: LLMConfig) -> ChatOpenAI:
        """Create vLLM instance (OpenAI-compatible API)."""
        import httpx
        
        # vLLM server exposes OpenAI-compatible API
        base_url = config.api_base or os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")
        
        # vLLM doesn't require API key for local deployment, but use if provided
        api_key = config.api_key or os.getenv("VLLM_API_KEY", "EMPTY")

        # Create httpx client with longer timeout for internal servers
        # For internal/development servers with self-signed certificates,
        # SSL verification may need to be disabled
        verify_ssl = config.extra.get("verify_ssl", False)  # Default to False for flexibility
        
        http_client = httpx.Client(
            timeout=httpx.Timeout(config.timeout, connect=10.0),
            verify=verify_ssl,  # Allow disabling SSL verification for self-signed certs
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )

        kwargs: Dict[str, Any] = {
            "model": config.model,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
            "top_p": config.top_p,
            "frequency_penalty": config.frequency_penalty,
            "presence_penalty": config.presence_penalty,
            "base_url": base_url,
            "api_key": api_key,
            "timeout": config.timeout,
            "max_retries": config.max_retries,
            "http_client": http_client,
        }

        if config.stop:
            kwargs["stop"] = config.stop

        # Add any extra parameters (excluding verify_ssl as it's for HTTP client only)
        extra_params = {k: v for k, v in config.extra.items() if k != "verify_ssl"}
        kwargs.update(extra_params)

        logger.info(f"Initializing vLLM LLM: {config.model} at {base_url}")
        return ChatOpenAI(**kwargs) 