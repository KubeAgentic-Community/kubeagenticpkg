"""FastAPI application for KubeAgentic REST API."""

import logging
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends, Header, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from kubeagentic import __version__
from kubeagentic.api.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    AgentChatRequest,
    AgentChatResponse,
    HealthResponse,
    AgentListResponse,
    AgentInfo,
    ErrorResponse,
    Message,
    Choice,
    Usage,
)
from kubeagentic.core.manager import AgentManager
from kubeagentic.exceptions import AgentError, KubeAgenticError

logger = logging.getLogger(__name__)

# Global agent manager
agent_manager: Optional[AgentManager] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle."""
    global agent_manager
    
    # Startup
    logger.info("Starting KubeAgentic API server")
    agent_manager = AgentManager()
    logger.info("Agent manager initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down KubeAgentic API server")


def create_app(
    title: str = "KubeAgentic API",
    description: str = "REST API for KubeAgentic - Declarative AI Agents",
    version: str = __version__,
    enable_cors: bool = True,
    api_keys: Optional[list] = None,
) -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Args:
        title: API title
        description: API description
        version: API version
        enable_cors: Whether to enable CORS
        api_keys: List of valid API keys for authentication
        
    Returns:
        Configured FastAPI application
    """
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        lifespan=lifespan,
    )
    
    # Store API keys in app state
    app.state.api_keys = set(api_keys) if api_keys else set()
    
    # CORS middleware
    if enable_cors:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Request ID middleware
    @app.middleware("http")
    async def add_request_id(request, call_next):
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    # Exception handlers
    @app.exception_handler(KubeAgenticError)
    async def kubeagentic_exception_handler(request, exc: KubeAgenticError):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content=ErrorResponse(
                error=str(exc),
                detail=exc.__class__.__name__,
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )
    
    @app.exception_handler(Exception)
    async def general_exception_handler(request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                error="Internal server error",
                detail=str(exc),
                request_id=getattr(request.state, "request_id", None),
            ).model_dump(),
        )
    
    # Authentication dependency
    async def verify_api_key(authorization: Optional[str] = Header(None)):
        """Verify API key from Authorization header."""
        if not app.state.api_keys:
            # No authentication required
            return None
        
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing",
            )
        
        # Extract key from "Bearer <key>" format
        parts = authorization.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Use: Bearer <key>",
            )
        
        api_key = parts[1]
        if api_key not in app.state.api_keys:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key",
            )
        
        return api_key
    
    # Health endpoints
    @app.get("/health", response_model=HealthResponse, tags=["Health"])
    async def health_check():
        """Health check endpoint."""
        return HealthResponse(
            status="healthy",
            version=__version__,
        )
    
    @app.get("/ready", response_model=HealthResponse, tags=["Health"])
    async def readiness_check():
        """Readiness check endpoint."""
        if agent_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent manager not initialized",
            )
        
        return HealthResponse(
            status="ready",
            version=__version__,
        )
    
    # Agent management endpoints
    @app.get("/v1/agents", response_model=AgentListResponse, tags=["Agents"])
    async def list_agents(api_key: Optional[str] = Depends(verify_api_key)):
        """List all available agents."""
        if agent_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent manager not initialized",
            )
        
        agents_dict = agent_manager.list_agents()
        agents_info = []
        
        for name, description in agents_dict.items():
            try:
                agent = agent_manager.get_agent(name)
                llm_info = "Unknown"
                if agent.agent_def.llm:
                    llm_info = f"{agent.agent_def.llm.provider.value}/{agent.agent_def.llm.model}"
                elif agent.agent_def.llms:
                    llm_info = f"{agent.agent_def.llms[0].provider.value}/{agent.agent_def.llms[0].model}"
                
                agents_info.append(
                    AgentInfo(
                        name=name,
                        description=description,
                        status="active",
                        tools_count=len(agent.agent_def.tools) if agent.agent_def.tools else 0,
                        llm_provider=agent.agent_def.llm.provider.value if agent.agent_def.llm else "multiple",
                        llm_model=agent.agent_def.llm.model if agent.agent_def.llm else "multiple",
                    )
                )
            except Exception as e:
                logger.error(f"Error getting agent info for {name}: {e}")
                continue
        
        return AgentListResponse(agents=agents_info, total=len(agents_info))
    
    @app.post("/v1/agents/{agent_name}/load", tags=["Agents"])
    async def load_agent(
        agent_name: str,
        config_path: str,
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """Load an agent from configuration file."""
        if agent_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent manager not initialized",
            )
        
        try:
            agent_manager.load_agent(config_path=config_path)
            return {"message": f"Agent loaded successfully", "agent_name": agent_name}
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to load agent: {str(e)}",
            )
    
    # Chat endpoints
    @app.post("/v1/chat", response_model=AgentChatResponse, tags=["Chat"])
    async def chat(
        request: AgentChatRequest,
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """Simple chat endpoint for agent interaction."""
        if agent_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent manager not initialized",
            )
        
        try:
            response = agent_manager.chat(
                agent_name=request.agent_name,
                message=request.message,
                session_id=request.session_id,
            )
            
            return AgentChatResponse(
                agent_name=request.agent_name,
                message=response["content"],
                session_id=request.session_id,
                metadata=response.get("metadata", {}),
            )
        except AgentError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
    
    # OpenAI-compatible endpoint
    @app.post("/v1/chat/completions", response_model=ChatCompletionResponse, tags=["OpenAI Compatible"])
    async def chat_completions(
        request: ChatCompletionRequest,
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """OpenAI-compatible chat completions endpoint."""
        if agent_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent manager not initialized",
            )
        
        try:
            # Extract user message from messages
            user_messages = [msg.content for msg in request.messages if msg.role == "user"]
            if not user_messages:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No user message found in request",
                )
            
            # Use the model field as agent name
            agent_name = request.model
            message = user_messages[-1]  # Use last user message
            
            # Call agent
            response = agent_manager.chat(
                agent_name=agent_name,
                message=message,
            )
            
            # Format response
            completion_id = f"chatcmpl-{uuid.uuid4().hex[:24]}"
            
            # Estimate token usage (rough estimate)
            prompt_tokens = len(message.split()) * 2
            completion_tokens = len(response["content"].split()) * 2
            
            return ChatCompletionResponse(
                id=completion_id,
                created=int(datetime.utcnow().timestamp()),
                model=agent_name,
                choices=[
                    Choice(
                        index=0,
                        message=Message(
                            role="assistant",
                            content=response["content"],
                        ),
                        finish_reason="stop",
                    )
                ],
                usage=Usage(
                    prompt_tokens=prompt_tokens,
                    completion_tokens=completion_tokens,
                    total_tokens=prompt_tokens + completion_tokens,
                ),
            )
            
        except AgentError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e),
            )
    
    # Tool execution endpoint
    @app.post("/v1/agents/{agent_name}/tools/{tool_name}/execute", tags=["Tools"])
    async def execute_tool(
        agent_name: str,
        tool_name: str,
        parameters: dict = {},
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """Execute a tool for a specific agent."""
        if agent_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent manager not initialized",
            )
        
        try:
            agent = agent_manager.get_agent(agent_name)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent '{agent_name}' not found",
                )
            
            result = agent.execute_tool(tool_name, parameters)
            return result
            
        except AgentError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    
    @app.get("/v1/agents/{agent_name}/tools", tags=["Tools"])
    async def list_agent_tools(
        agent_name: str,
        api_key: Optional[str] = Depends(verify_api_key)
    ):
        """List all tools available for an agent."""
        if agent_manager is None:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Agent manager not initialized",
            )
        
        try:
            agent = agent_manager.get_agent(agent_name)
            if not agent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Agent '{agent_name}' not found",
                )
            
            tools = agent.get_available_tools()
            return {"agent": agent_name, "tools": tools, "count": len(tools)}
            
        except AgentError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
    
    return app 