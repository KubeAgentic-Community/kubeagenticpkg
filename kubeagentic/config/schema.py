"""Pydantic schemas for agent configuration validation."""

from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator


class LogLevel(str, Enum):
    """Logging levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogFormat(str, Enum):
    """Logging formats."""

    JSON = "json"
    TEXT = "text"


class LogOutput(str, Enum):
    """Logging outputs."""

    CONSOLE = "console"
    FILE = "file"


class LLMProvider(str, Enum):
    """Supported LLM providers."""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    HUGGINGFACE = "huggingface"
    AZURE_OPENAI = "azure_openai"
    COHERE = "cohere"
    GOOGLE = "google"
    BEDROCK = "bedrock"
    VLLM = "vllm"


class MemoryType(str, Enum):
    """Memory types for conversation history."""

    BUFFER = "buffer"
    SUMMARY = "summary"
    CONVERSATION = "conversation"


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: LogLevel = Field(default=LogLevel.INFO, description="Logging level")
    format: LogFormat = Field(default=LogFormat.JSON, description="Log format")
    output: LogOutput = Field(default=LogOutput.CONSOLE, description="Log output destination")
    file_path: Optional[str] = Field(default=None, description="Log file path if output is file")


class LLMConfig(BaseModel):
    """LLM provider configuration."""

    provider: LLMProvider = Field(..., description="LLM provider name")
    model: str = Field(..., description="Model name/identifier")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: int = Field(default=1000, gt=0, description="Maximum tokens to generate")
    top_p: float = Field(default=1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    frequency_penalty: float = Field(
        default=0.0, ge=-2.0, le=2.0, description="Frequency penalty"
    )
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0, description="Presence penalty")
    stop: Optional[List[str]] = Field(default=None, description="Stop sequences")
    api_key: Optional[str] = Field(default=None, description="API key for the provider")
    api_base: Optional[str] = Field(default=None, description="Base URL for API")
    priority: int = Field(default=1, description="Priority for fallback (lower is higher priority)")
    timeout: int = Field(default=60, gt=0, description="Request timeout in seconds")
    max_retries: int = Field(default=3, ge=0, description="Maximum number of retries")
    extra: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific parameters")


class ToolParameter(BaseModel):
    """Tool parameter definition."""

    type: str = Field(..., description="Parameter type")
    description: Optional[str] = Field(None, description="Parameter description")
    enum: Optional[List[str]] = Field(None, description="Allowed values for enum types")
    default: Optional[Any] = Field(None, description="Default value")


class ToolConfig(BaseModel):
    """Tool configuration."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    type: str = Field(default="builtin", description="Tool type: builtin, custom, rest_api, langchain")
    class_path: Optional[str] = Field(None, description="Python class path for custom tools")
    parameters: Dict[str, ToolParameter] = Field(
        default_factory=dict, description="Tool parameters schema"
    )
    required: List[str] = Field(default_factory=list, description="Required parameter names")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    config: Optional[Dict[str, Any]] = Field(None, description="Tool-specific configuration (e.g., API endpoints for rest_api)")


class MemoryConfig(BaseModel):
    """Memory and conversation history configuration."""

    type: MemoryType = Field(default=MemoryType.BUFFER, description="Memory type")
    max_messages: int = Field(default=10, gt=0, description="Maximum messages to keep in memory")
    max_tokens: Optional[int] = Field(
        default=None, gt=0, description="Maximum tokens in memory (for summary mode)"
    )


class LimitsConfig(BaseModel):
    """Rate limits and resource constraints."""

    max_tokens_per_request: int = Field(
        default=4000, gt=0, description="Maximum tokens per request"
    )
    max_requests_per_minute: int = Field(
        default=60, gt=0, description="Maximum requests per minute"
    )
    max_concurrent_requests: int = Field(
        default=10, gt=0, description="Maximum concurrent requests"
    )
    daily_token_budget: Optional[int] = Field(
        default=None, gt=0, description="Daily token budget limit"
    )
    timeout_seconds: int = Field(default=30, gt=0, description="Request timeout in seconds")


class AgentDefinition(BaseModel):
    """Agent definition from configuration."""

    name: str = Field(..., description="Agent name/identifier")
    description: str = Field(..., description="Agent description")
    system_prompt: str = Field(..., description="System prompt for the agent")
    llm: Optional[LLMConfig] = Field(None, description="Single LLM configuration")
    llms: Optional[List[LLMConfig]] = Field(None, description="Multiple LLMs with fallback")
    tools: List[ToolConfig] = Field(default_factory=list, description="Tools available to agent")
    memory: MemoryConfig = Field(default_factory=MemoryConfig, description="Memory configuration")
    logging: LoggingConfig = Field(
        default_factory=LoggingConfig, description="Logging configuration"
    )
    limits: LimitsConfig = Field(default_factory=LimitsConfig, description="Resource limits")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("llm", "llms")
    @classmethod
    def validate_llm_config(cls, v: Any, info: Any) -> Any:
        """Ensure at least one LLM is configured."""
        # This will be called for both llm and llms fields
        return v

    def model_post_init(self, __context: Any) -> None:
        """Validate that either llm or llms is provided."""
        if self.llm is None and (self.llms is None or len(self.llms) == 0):
            raise ValueError("Either 'llm' or 'llms' must be provided")
        if self.llm is not None and self.llms is not None:
            raise ValueError("Cannot specify both 'llm' and 'llms', choose one")


class AgentConfigSchema(BaseModel):
    """Root configuration schema for agent YAML."""

    version: str = Field(..., description="Configuration schema version")
    agent: AgentDefinition = Field(..., description="Agent definition")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate configuration version."""
        supported_versions = ["1.0", "1"]
        if v not in supported_versions:
            raise ValueError(
                f"Unsupported configuration version: {v}. "
                f"Supported versions: {', '.join(supported_versions)}"
            )
        return v 