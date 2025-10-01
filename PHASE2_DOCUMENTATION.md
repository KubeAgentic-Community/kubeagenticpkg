# Phase 2: REST API Foundation - Complete Documentation

## Overview

Phase 2 adds a complete REST API layer to KubeAgentic with tool execution capabilities, OpenAI-compatible endpoints, and agent management.

---

## What's Implemented

### ✅ 1. Tool Execution System

**Files:**
- `kubeagentic/tools/executor.py` - Tool executor for REST API calls
- `kubeagentic/tools/registry.py` - Tool registry for management
- `kubeagentic/tools/__init__.py` - Tools package

**Features:**
- ✅ REST API tool execution with parameter substitution
- ✅ HTTP methods: GET, POST, PUT, DELETE, PATCH
- ✅ Custom headers and authentication
- ✅ Query parameters and request body support
- ✅ Error handling and result formatting
- ✅ Tool registry for discovery

**Usage:**
```python
from kubeagentic.tools.executor import ToolExecutor
from kubeagentic import Agent

# Load agent with tools
agent = Agent.from_config_file("examples/vllm_advanced.yaml")

# Check available tools
print(agent.get_available_tools())

# Execute a tool
result = agent.execute_tool("get_weather", {"city": "Mumbai"})
print(result)
```

---

### ✅ 2. FastAPI REST API Server

**Files:**
- `kubeagentic/api/app.py` - Main FastAPI application
- `kubeagentic/api/models.py` - Request/Response models
- `kubeagentic/api/server.py` - Server script
- `kubeagentic/api/__init__.py` - API package

**Features:**
- ✅ FastAPI application with async support
- ✅ Request ID middleware
- ✅ CORS middleware
- ✅ Exception handlers
- ✅ API key authentication
- ✅ Automatic OpenAPI documentation

**Endpoints Implemented:**

#### Health Endpoints
- `GET /health` - Health check
- `GET /ready` - Readiness check

#### Agent Management
- `GET /v1/agents` - List all agents
- `POST /v1/agents/{agent_name}/load` - Load an agent

#### Chat Endpoints
- `POST /v1/chat` - Simple chat endpoint
- `POST /v1/chat/completions` - OpenAI-compatible endpoint

#### Tool Endpoints
- `GET /v1/agents/{agent_name}/tools` - List agent tools
- `POST /v1/agents/{agent_name}/tools/{tool_name}/execute` - Execute a tool

---

### ✅ 3. Agent Integration

**Files:**
- `kubeagentic/core/agent.py` - Updated with tool support

**New Agent Methods:**
```python
# Check if agent has tools
agent.has_tools  # Property

# Get available tools
agent.get_available_tools()  # Returns List[str]

# Execute a tool
agent.execute_tool(tool_name, parameters)  # Returns Dict
```

---

### ✅ 4. Updated CLI

**File:** `kubeagentic/cli.py`

**New Command:**
```bash
# Start API server
kubeagentic serve --config-dir examples --port 8000

# With authentication
kubeagentic serve --config-dir examples --port 8000 --api-key YOUR_KEY

# Development mode
kubeagentic serve --config-dir examples --port 8000 --reload
```

---

## API Reference

### Authentication

If API keys are configured, include in header:
```
Authorization: Bearer YOUR_API_KEY
```

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "timestamp": "2025-10-01T22:00:00"
}
```

### List Agents

```bash
curl http://localhost:8000/v1/agents
```

Response:
```json
{
  "agents": [
    {
      "name": "vllm_assistant",
      "description": "AI assistant powered by vLLM",
      "status": "active",
      "tools_count": 0,
      "llm_provider": "vllm",
      "llm_model": "mistralai/Mistral-7B-Instruct-v0.3"
    }
  ],
  "total": 1
}
```

### Chat (Simple)

```bash
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "vllm_assistant",
    "message": "What is artificial intelligence?"
  }'
```

Response:
```json
{
  "agent_name": "vllm_assistant",
  "message": "Artificial Intelligence (AI) is...",
  "session_id": null,
  "timestamp": "2025-10-01T22:00:00",
  "metadata": {}
}
```

### Chat Completions (OpenAI Compatible)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "vllm_assistant",
    "messages": [
      {"role": "user", "content": "What is AI?"}
    ]
  }'
```

Response:
```json
{
  "id": "chatcmpl-abc123...",
  "object": "chat.completion",
  "created": 1696182000,
  "model": "vllm_assistant",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "Artificial Intelligence...",
        "name": null,
        "tool_call_id": null
      },
      "finish_reason": "stop",
      "logprobs": null
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 50,
    "total_tokens": 60
  }
}
```

### List Agent Tools

```bash
curl http://localhost:8000/v1/agents/vllm_advanced_assistant/tools
```

Response:
```json
{
  "agent": "vllm_advanced_assistant",
  "tools": [
    "get_weather",
    "get_available_cities",
    "get_products",
    "get_all_products"
  ],
  "count": 4
}
```

### Execute Tool

```bash
curl -X POST http://localhost:8000/v1/agents/vllm_advanced_assistant/tools/get_weather/execute \
  -H "Content-Type: application/json" \
  -d '{
    "parameters": {
      "city": "Mumbai"
    }
  }'
```

Response:
```json
{
  "success": true,
  "tool": "get_weather",
  "result": {
    "city": "Mumbai",
    "temperature": 28,
    "conditions": "Partly cloudy"
  },
  "status_code": 200
}
```

---

## Running the Server

### Method 1: Using CLI

```bash
# Activate virtual environment
source .venv/bin/activate

# Start server
python -m kubeagentic.cli serve --config-dir examples --port 8000
```

### Method 2: Using Python

```python
from kubeagentic.api.server import run_server

run_server(
    host="0.0.0.0",
    port=8000,
    agents_dir="examples",
    api_keys=["your-secret-key"],
)
```

### Method 3: Direct Uvicorn

```bash
uvicorn kubeagentic.api.app:create_app --host 0.0.0.0 --port 8000 --reload
```

---

## Configuration

### Server Configuration

```python
app = create_app(
    title="KubeAgentic API",
    description="REST API for KubeAgentic",
    version="0.1.0",
    enable_cors=True,
    api_keys=["key1", "key2"],  # Optional
)
```

### Tool Configuration (YAML)

```yaml
tools:
  - name: "get_weather"
    description: "Get weather for a city"
    type: "rest_api"
    enabled: true
    parameters:
      city:
        type: "string"
        description: "City name"
        required: true
    config:
      url: "http://api.example.com/weather"
      method: "GET"
      headers:
        Authorization: "Bearer TOKEN"
      query_params:
        city: "{city}"
```

---

## Testing

### Run Phase 2 Tests

```bash
source .venv/bin/activate
python test_phase2.py
```

### Test Individual Components

```python
# Test tool executor
from kubeagentic.tools.executor import ToolExecutor
executor = ToolExecutor(tools=your_tools)
result = executor.execute("tool_name", {"param": "value"})

# Test FastAPI app
from kubeagentic.api.app import create_app
app = create_app()

# Test with httpx
import httpx
client = httpx.Client()
response = client.get("http://localhost:8000/health")
```

### Test with curl

```bash
# Health check
curl http://localhost:8000/health

# API docs
curl http://localhost:8000/docs

# List agents
curl http://localhost:8000/v1/agents

# Chat
curl -X POST http://localhost:8000/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"agent_name": "vllm_assistant", "message": "Hello"}'
```

---

## OpenAPI Documentation

Once the server is running, visit:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

---

## Security Features

### API Key Authentication

```bash
# Set API key
python -m kubeagentic.cli serve --api-key my-secret-key

# Use in requests
curl -H "Authorization: Bearer my-secret-key" http://localhost:8000/v1/agents
```

### CORS

CORS is enabled by default for development. For production:

```python
app = create_app(enable_cors=False)

# Or configure specific origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_methods=["GET", "POST"],
)
```

### Request ID Tracking

Every request gets a unique ID:
```
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

---

## Error Handling

All errors return consistent format:

```json
{
  "error": "Error message",
  "detail": "Detailed information",
  "timestamp": "2025-10-01T22:00:00",
  "request_id": "550e8400-..."
}
```

**HTTP Status Codes:**
- `200` - Success
- `400` - Bad Request
- `401` - Unauthorized
- `404` - Not Found
- `500` - Internal Server Error
- `503` - Service Unavailable

---

## Performance

### Metrics

Process time is tracked in response headers:
```
X-Process-Time: 0.123
```

### Async Support

All endpoints support async operations:

```python
# Async endpoint
@app.post("/v1/chat")
async def chat(request: AgentChatRequest):
    response = await agent_manager.achat(...)
    return response
```

---

## Next Steps (Future Phases)

- [ ] Streaming responses (SSE)
- [ ] Session management with Redis
- [ ] Rate limiting per user
- [ ] Metrics endpoint (Prometheus)
- [ ] WebSocket support
- [ ] Tool calling in LLM responses
- [ ] Advanced authentication (JWT, OAuth2)
- [ ] Database persistence
- [ ] Caching layer

---

## Troubleshooting

### Server won't start

**Issue:** Import errors

**Solution:**
```bash
pip install -r requirements.txt
```

### Tools not working

**Issue:** Tool APIs not accessible

**Solution:**
1. Check network connectivity
2. Verify API endpoints are correct
3. Check authentication tokens
4. Review tool logs with `--log-level debug`

### Agent not found

**Issue:** Agent not loaded

**Solution:**
```bash
# Preload agents
python -m kubeagentic.cli serve --config-dir examples
```

### Authentication fails

**Issue:** Invalid API key

**Solution:**
1. Check API key is correct
2. Verify header format: `Authorization: Bearer YOUR_KEY`
3. Restart server if keys were changed

---

## File Structure

```
kubeagentic/
├── api/
│   ├── __init__.py
│   ├── app.py          # FastAPI application
│   ├── models.py       # Request/Response models
│   └── server.py       # Server runner
├── tools/
│   ├── __init__.py
│   ├── executor.py     # Tool executor
│   └── registry.py     # Tool registry
├── core/
│   ├── agent.py        # Updated with tool support
│   └── manager.py      # Agent manager
└── cli.py              # Updated with serve command
```

---

## Examples

See `examples/` directory:
- `vllm_simple.yaml` - Simple agent
- `vllm_advanced.yaml` - Agent with REST API tools

See `test_phase2.py` for comprehensive examples.

---

**Phase 2 Status:** ✅ Complete and Tested

**Date:** October 1, 2025

**Version:** 0.1.0 