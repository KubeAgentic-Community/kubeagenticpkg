"""Streaming support for real-time responses."""

import asyncio
import json
import logging
import uuid
from datetime import datetime
from typing import AsyncGenerator, Dict, Any, Optional

from sse_starlette.sse import EventSourceResponse

logger = logging.getLogger(__name__)


async def stream_agent_response(
    agent,
    message: str,
    session_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream agent response token by token.
    
    Args:
        agent: Agent instance
        message: User message
        session_id: Optional session ID
        
    Yields:
        SSE-formatted chunks
    """
    try:
        logger.debug(f"Starting stream for agent: {agent.name}")
        
        # Check if agent's LLM supports streaming
        if hasattr(agent.llm, 'stream') or hasattr(agent.llm, 'astream'):
            # Use LangChain's streaming
            async for chunk in _stream_langchain_response(agent, message, session_id):
                yield chunk
        else:
            # Fallback: simulate streaming by chunking non-streaming response
            async for chunk in _simulate_streaming(agent, message, session_id):
                yield chunk
                
    except Exception as e:
        logger.error(f"Streaming error: {e}", exc_info=True)
        error_data = {
            "error": str(e),
            "type": "error"
        }
        yield f"data: {json.dumps(error_data)}\n\n"


async def _stream_langchain_response(
    agent,
    message: str,
    session_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream response using LangChain's native streaming."""
    from langchain_core.messages import HumanMessage
    
    # Prepare state
    state = {
        "messages": [HumanMessage(content=message)]
    }
    
    # Stream through the graph
    async for event in agent.graph.astream(state):
        if "messages" in event:
            messages = event["messages"]
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    # Send chunk
                    chunk_data = {
                        "content": last_message.content,
                        "role": "assistant",
                        "type": "content",
                        "metadata": {
                            "agent_name": agent.name,
                            "session_id": session_id,
                        }
                    }
                    yield f"data: {json.dumps(chunk_data)}\n\n"
    
    # Send completion marker
    completion_data = {
        "type": "done",
        "metadata": {
            "agent_name": agent.name,
            "session_id": session_id,
        }
    }
    yield f"data: {json.dumps(completion_data)}\n\n"


async def _simulate_streaming(
    agent,
    message: str,
    session_id: Optional[str] = None,
    chunk_size: int = 10,
    delay: float = 0.05,
) -> AsyncGenerator[str, None]:
    """
    Simulate streaming by chunking a non-streaming response.
    
    Args:
        agent: Agent instance
        message: User message
        session_id: Optional session ID
        chunk_size: Number of words per chunk
        delay: Delay between chunks in seconds
    """
    # Get full response
    response = await agent.ainvoke(message, session_id=session_id)
    content = response.get("content", "")
    
    # Split into words
    words = content.split()
    
    # Send chunks
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if i + chunk_size < len(words):
            chunk += " "
        
        chunk_data = {
            "content": chunk,
            "role": "assistant",
            "type": "content",
            "metadata": {
                "agent_name": agent.name,
                "session_id": session_id,
            }
        }
        yield f"data: {json.dumps(chunk_data)}\n\n"
        
        # Small delay to simulate real streaming
        await asyncio.sleep(delay)
    
    # Send completion marker
    completion_data = {
        "type": "done",
        "metadata": {
            "agent_name": agent.name,
            "session_id": session_id,
            "total_words": len(words),
        }
    }
    yield f"data: {json.dumps(completion_data)}\n\n"


async def stream_openai_compatible(
    agent,
    message: str,
    model: str,
    session_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """
    Stream response in OpenAI-compatible format.
    
    Args:
        agent: Agent instance
        message: User message
        model: Model/agent name
        session_id: Optional session ID
        
    Yields:
        SSE-formatted chunks in OpenAI format
    """
    chunk_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
    created = int(datetime.utcnow().timestamp())
    
    try:
        # Check if agent supports streaming
        if hasattr(agent.llm, 'stream') or hasattr(agent.llm, 'astream'):
            async for content_chunk in _stream_langchain_tokens(agent, message, session_id):
                # OpenAI format
                chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": content_chunk},
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(chunk)}\n\n"
        else:
            # Simulate streaming
            async for content_chunk in _simulate_token_streaming(agent, message, session_id):
                chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": model,
                    "choices": [
                        {
                            "index": 0,
                            "delta": {"content": content_chunk},
                            "finish_reason": None,
                        }
                    ],
                }
                yield f"data: {json.dumps(chunk)}\n\n"
        
        # Send final chunk with finish_reason
        final_chunk = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
        yield f"data: {json.dumps(final_chunk)}\n\n"
        yield "data: [DONE]\n\n"
        
    except Exception as e:
        logger.error(f"OpenAI streaming error: {e}", exc_info=True)
        error_chunk = {
            "error": {
                "message": str(e),
                "type": "server_error",
            }
        }
        yield f"data: {json.dumps(error_chunk)}\n\n"


async def _stream_langchain_tokens(
    agent,
    message: str,
    session_id: Optional[str] = None,
) -> AsyncGenerator[str, None]:
    """Stream individual tokens from LangChain."""
    from langchain_core.messages import HumanMessage
    
    state = {
        "messages": [HumanMessage(content=message)]
    }
    
    accumulated = ""
    async for event in agent.graph.astream(state):
        if "messages" in event:
            messages = event["messages"]
            if messages:
                last_message = messages[-1]
                if hasattr(last_message, 'content'):
                    current = last_message.content
                    # Get the new tokens
                    new_content = current[len(accumulated):]
                    if new_content:
                        yield new_content
                        accumulated = current


async def _simulate_token_streaming(
    agent,
    message: str,
    session_id: Optional[str] = None,
    chars_per_chunk: int = 5,
    delay: float = 0.03,
) -> AsyncGenerator[str, None]:
    """Simulate token-by-token streaming."""
    # Get full response
    response = await agent.ainvoke(message, session_id=session_id)
    content = response.get("content", "")
    
    # Stream character by character (grouped)
    for i in range(0, len(content), chars_per_chunk):
        chunk = content[i:i + chars_per_chunk]
        yield chunk
        await asyncio.sleep(delay)


def create_sse_response(generator: AsyncGenerator) -> EventSourceResponse:
    """
    Create Server-Sent Events response.
    
    Args:
        generator: Async generator yielding SSE data
        
    Returns:
        EventSourceResponse
    """
    return EventSourceResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable buffering in nginx
        },
    ) 