# KubeAgentic v2 🤖

<div align="center">

**Build powerful AI agents from YAML configuration with OpenAI-compatible REST API**

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PyPI version](https://badge.fury.io/py/kubeagentic.svg)](https://pypi.org/project/kubeagentic/)

[🌐 Website](https://kubeagentic.com) | [📚 Documentation](https://kubeagentic.com/guides) | [🚀 Quick Start](https://kubeagentic.com/guides/kubeagentic-local-testing-guide/) | [💬 Discussions](https://github.com/KubeAgentic-Community/kubeagenticpkg/discussions)

</div>

---

## 🌟 Overview

KubeAgentic v2 is a powerful Python library that simplifies building AI agents with LangGraph. Define your agents declaratively in YAML and access them through an OpenAI-compatible REST API. No complex code required!

### Key Features

✨ **Declarative Configuration** - Define agents in simple YAML files  
🔌 **OpenAI-Compatible API** - Drop-in replacement for OpenAI endpoints  
🚀 **Multiple LLM Providers** - OpenAI, Anthropic, Ollama, Hugging Face, and more  
🔧 **Flexible Tool System** - Built-in and custom tool support  
📊 **Production-Ready** - Logging, monitoring, rate limiting, and more  
🔒 **Secure by Default** - API key auth, CORS, rate limiting  
💾 **Session Management** - Persistent conversation history  
⚡ **Streaming Support** - Real-time token streaming  
📈 **Cost Tracking** - Monitor token usage and costs  

---

## 🚀 Quick Start

### Installation

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install KubeAgentic
pip install kubeagentic

# Or install from source
git clone https://github.com/KubeAgentic-Community/kubeagenticpkg.git
cd kubeagenticpkg
pip install -e ".[dev]"
```

### Create Your First Agent

**1. Create a configuration file** (`my_agent.yaml`):

```yaml
version: "1.0"
agent:
  name: "customer_support_agent"
  description: "A helpful customer support agent"
  
  llm:
    provider: "openai"
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 1000
  
  system_prompt: |
    You are a helpful customer support agent.
    Be friendly, professional, and concise.
  
  tools:
    - name: "search_knowledge_base"
      description: "Search the company knowledge base"
    - name: "create_ticket"
      description: "Create a support ticket"
  
  logging:
    level: "info"
```

**2. Start the API server**:

```bash
# Using CLI
kubeagentic serve --config my_agent.yaml --port 8000

# Or using Python
from kubeagentic import AgentServer

server = AgentServer.from_yaml("my_agent.yaml")
server.run(host="0.0.0.0", port=8000)
```

**3. Use the API**:

```python
import openai

# Point to your KubeAgentic server
client = openai.OpenAI(
    api_key="your-api-key",
    base_url="http://localhost:8000/v1"
)

# Chat with your agent
response = client.chat.completions.create(
    model="customer_support_agent",
    messages=[
        {"role": "user", "content": "How do I reset my password?"}
    ]
)

print(response.choices[0].message.content)
```

---

## 📖 Documentation

### Configuration Schema

Full YAML configuration options:

```yaml
version: "1.0"

agent:
  name: "my_agent"
  description: "Agent description"
  
  # LLM Configuration
  llm:
    provider: "openai"  # openai, anthropic, ollama, huggingface
    model: "gpt-4"
    temperature: 0.7
    max_tokens: 1000
    top_p: 1.0
    frequency_penalty: 0.0
    presence_penalty: 0.0
    
  # Alternative: Multiple LLMs with fallback
  llms:
    - provider: "openai"
      model: "gpt-4"
      priority: 1
    - provider: "anthropic"
      model: "claude-3-opus-20240229"
      priority: 2
      
  # System prompt
  system_prompt: "Your system prompt here"
  
  # Tools configuration
  tools:
    - name: "tool_name"
      description: "Tool description"
      parameters:
        type: "object"
        properties:
          param1:
            type: "string"
            description: "Parameter description"
      
  # Memory & session configuration
  memory:
    type: "buffer"  # buffer, summary, conversation
    max_messages: 10
    
  # Logging configuration
  logging:
    level: "info"  # debug, info, warning, error
    format: "json"
    output: "console"  # console, file
    
  # Cost & rate limits
  limits:
    max_tokens_per_request: 4000
    max_requests_per_minute: 60
    daily_token_budget: 1000000
```

### API Endpoints

KubeAgentic provides OpenAI-compatible endpoints:

#### Chat Completions

```bash
POST /v1/chat/completions
```

```python
{
  "model": "customer_support_agent",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7,
  "stream": false
}
```

#### Streaming

```python
response = client.chat.completions.create(
    model="my_agent",
    messages=[{"role": "user", "content": "Tell me a story"}],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end="")
```

#### Health & Monitoring

```bash
GET /health          # Liveness check
GET /ready           # Readiness check
GET /metrics         # Prometheus metrics
```

---

## 🔧 Advanced Features

### Custom Tools

Create custom tools for your agents:

```python
from kubeagentic.tools import BaseTool
from pydantic import BaseModel, Field

class SearchInput(BaseModel):
    query: str = Field(..., description="Search query")

class SearchTool(BaseTool):
    name = "search"
    description = "Search the web"
    args_schema = SearchInput
    
    async def _arun(self, query: str) -> str:
        # Your search implementation
        results = await search_web(query)
        return results
```

Register in YAML:

```yaml
tools:
  - type: "custom"
    class: "my_module.SearchTool"
```

### Multiple Agents

Run multiple agents simultaneously:

```python
from kubeagentic import AgentManager

manager = AgentManager()
manager.load_agent("agent1.yaml")
manager.load_agent("agent2.yaml")

# Access different agents
response = await manager.chat(
    agent_name="agent1",
    message="Hello!"
)
```

### Session Management

Maintain conversation context:

```python
# Create a session
session_id = await manager.create_session(
    agent_name="my_agent",
    user_id="user123"
)

# Continue conversation
response = await manager.chat(
    agent_name="my_agent",
    message="What did we discuss earlier?",
    session_id=session_id
)
```

---

## 🔒 Security

### API Key Authentication

```bash
# Generate API key
kubeagentic apikey create --name "my-app"

# Use in requests
curl -H "Authorization: Bearer YOUR_API_KEY" \
     http://localhost:8000/v1/chat/completions
```

### Environment Variables

```bash
# .env file
KUBEAGENTIC_API_KEYS=key1,key2,key3
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
DATABASE_URL=postgresql://user:pass@localhost/db
REDIS_URL=redis://localhost:6379
```

---

## 📊 Monitoring & Observability

### Prometheus Metrics

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'kubeagentic'
    static_configs:
      - targets: ['localhost:8000']
```

Available metrics:
- `kubeagentic_requests_total` - Total requests
- `kubeagentic_request_duration_seconds` - Request latency
- `kubeagentic_tokens_used_total` - Token usage
- `kubeagentic_costs_total` - Total costs

### Structured Logging

```python
# Configure logging
import logging
from kubeagentic.logging import setup_logging

setup_logging(
    level="INFO",
    format="json",
    output="console"
)
```

---

## 🐳 Docker Deployment

### Docker

```bash
# Build image
docker build -t kubeagentic:latest .

# Run container
docker run -d \
  -p 8000:8000 \
  -v $(pwd)/config:/app/config \
  -e OPENAI_API_KEY=sk-... \
  kubeagentic:latest
```

### Docker Compose

```yaml
version: '3.8'
services:
  kubeagentic:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./config:/app/config
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - DATABASE_URL=postgresql://postgres:password@db:5432/kubeagentic
      - REDIS_URL=redis://redis:6379
    depends_on:
      - db
      - redis
      
  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=kubeagentic
      - POSTGRES_PASSWORD=password
      
  redis:
    image: redis:7-alpine
```

---

## ☸️ Kubernetes Deployment

```bash
# Apply manifests
kubectl apply -f k8s/

# Or use Helm
helm install kubeagentic ./helm/kubeagentic
```

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=kubeagentic --cov-report=html

# Run specific test
pytest tests/test_agent.py -v

# Run load tests
locust -f tests/load/locustfile.py
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- Built with [LangGraph](https://github.com/langchain-ai/langgraph)
- Powered by [LangChain](https://github.com/langchain-ai/langchain)
- API framework by [FastAPI](https://fastapi.tiangolo.com/)

---

## 📮 Support

- 🌐 Website: [https://kubeagentic.com](https://kubeagentic.com)
- 📧 Email: contact@kubeagentic.com
- 🐛 Issues: [GitHub Issues](https://github.com/KubeAgentic-Community/kubeagenticpkg/issues)
- 📚 Docs: [Documentation](https://kubeagentic.com/guides)
- 💬 Discussions: [GitHub Discussions](https://github.com/KubeAgentic-Community/kubeagenticpkg/discussions)

---

**Built with ❤️ by the KubeAgentic Team** 