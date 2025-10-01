"""Pydantic models for REST API requests and responses."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field
from datetime import datetime


# Request Models
class Message(BaseModel):
    """Chat message model."""
    role: Literal["system", "user", "assistant", "tool"] = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    name: Optional[str] = Field(None, description="Name of the sender")
    tool_call_id: Optional[str] = Field(None, description="Tool call ID for tool responses")


class ChatCompletionRequest(BaseModel):
    """Request model for chat completion endpoint (OpenAI-compatible)."""
    model: str = Field(..., description="Model/Agent name to use")
    messages: List[Message] = Field(..., description="List of messages")
    temperature: Optional[float] = Field(0.7, ge=0.0, le=2.0, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, ge=1, description="Maximum tokens to generate")
    stream: Optional[bool] = Field(False, description="Whether to stream the response")
    top_p: Optional[float] = Field(1.0, ge=0.0, le=1.0, description="Nucleus sampling parameter")
    n: Optional[int] = Field(1, ge=1, le=10, description="Number of completions to generate")
    stop: Optional[List[str]] = Field(None, description="Stop sequences")
    presence_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Presence penalty")
    frequency_penalty: Optional[float] = Field(0.0, ge=-2.0, le=2.0, description="Frequency penalty")
    user: Optional[str] = Field(None, description="User identifier")


class AgentChatRequest(BaseModel):
    """Simplified request model for agent chat."""
    agent_name: str = Field(..., description="Name of the agent to use")
    message: str = Field(..., description="User message")
    session_id: Optional[str] = Field(None, description="Session ID for conversation history")


# Response Models
class Usage(BaseModel):
    """Token usage information."""
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_tokens: int = Field(..., description="Total number of tokens used")


class Choice(BaseModel):
    """Chat completion choice."""
    index: int = Field(..., description="Index of the choice")
    message: Message = Field(..., description="Generated message")
    finish_reason: Optional[str] = Field(None, description="Reason for finishing")
    logprobs: Optional[Dict[str, Any]] = Field(None, description="Log probabilities")


class ChatCompletionResponse(BaseModel):
    """Response model for chat completion (OpenAI-compatible)."""
    id: str = Field(..., description="Unique identifier for the completion")
    object: str = Field("chat.completion", description="Object type")
    created: int = Field(..., description="Unix timestamp of creation")
    model: str = Field(..., description="Model used")
    choices: List[Choice] = Field(..., description="List of completion choices")
    usage: Usage = Field(..., description="Token usage information")
    system_fingerprint: Optional[str] = Field(None, description="System fingerprint")


class AgentChatResponse(BaseModel):
    """Simplified response model for agent chat."""
    agent_name: str = Field(..., description="Name of the agent")
    message: str = Field(..., description="Agent's response")
    session_id: Optional[str] = Field(None, description="Session ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")


class AgentInfo(BaseModel):
    """Agent information response."""
    name: str = Field(..., description="Agent name")
    description: str = Field(..., description="Agent description")
    status: str = Field(..., description="Agent status")
    tools_count: int = Field(..., description="Number of configured tools")
    llm_provider: str = Field(..., description="LLM provider")
    llm_model: str = Field(..., description="LLM model")


class AgentListResponse(BaseModel):
    """List of agents response."""
    agents: List[AgentInfo] = Field(..., description="List of available agents")
    total: int = Field(..., description="Total number of agents")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Detailed error information")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    request_id: Optional[str] = Field(None, description="Request identifier") 