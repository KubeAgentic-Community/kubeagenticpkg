"""Custom exceptions for KubeAgentic."""


class KubeAgenticError(Exception):
    """Base exception for all KubeAgentic errors."""

    pass


class ConfigurationError(KubeAgenticError):
    """Raised when configuration is invalid or cannot be loaded."""

    pass


class AgentError(KubeAgenticError):
    """Raised when agent creation or execution fails."""

    pass


class LLMError(KubeAgenticError):
    """Raised when LLM provider communication fails."""

    pass


class ToolError(KubeAgenticError):
    """Raised when tool execution fails."""

    pass


class ValidationError(KubeAgenticError):
    """Raised when validation fails."""

    pass


class AuthenticationError(KubeAgenticError):
    """Raised when authentication fails."""

    pass


class RateLimitError(KubeAgenticError):
    """Raised when rate limit is exceeded."""

    pass


class SessionError(KubeAgenticError):
    """Raised when session management fails."""

    pass


class DatabaseError(KubeAgenticError):
    """Raised when database operations fail."""

    pass 