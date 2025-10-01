# KubeAgentic v2 - Quick Start Guide

**Welcome to KubeAgentic!** This guide will help you get started in minutes.

---

## 📋 Prerequisites

- Python 3.10 or higher
- pip (Python package manager)
- An API key from OpenAI, Anthropic, or another supported LLM provider

---

## 🚀 Installation Steps

### Step 1: Set Up Virtual Environment

```bash
# Navigate to the project directory
cd /Users/sudeshmu/work/opensource/kubeagenticV2

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate  # On macOS/Linux
# OR
.venv\Scripts\activate     # On Windows
```

### Step 2: Install Dependencies

```bash
# Install from requirements file
pip install -r requirements.txt

# For development (includes testing tools)
pip install -r requirements-dev.txt

# OR install in editable mode
pip install -e .
```

### Step 3: Set Up Environment Variables

```bash
# Set your OpenAI API key (or other provider)
export OPENAI_API_KEY="sk-your-api-key-here"

# OR create a .env file
echo "OPENAI_API_KEY=sk-your-api-key-here" > .env
```

### Step 4: Verify Installation

```bash
# Run the test script
python test_installation.py
```

Expected output:
```
============================================================
KubeAgentic Installation Test
============================================================
Testing dependencies...
  ✓ PyYAML
  ✓ Pydantic
  ✓ LangChain
  ✓ LangGraph
  ...

🎉 All tests passed! KubeAgentic is ready to use.
```

---

## 🎯 Try It Out!

### Example 1: Validate a Configuration

```bash
python -m kubeagentic.cli validate examples/simple_agent.yaml
```

Expected output:
```
✓ Configuration is valid!
Agent: simple_assistant
Description: A simple AI assistant for general questions
```

### Example 2: Show Agent Information

```bash
python -m kubeagentic.cli info examples/simple_agent.yaml
```

This displays a formatted table with agent details.

### Example 3: Test Agent Locally

```bash
# With default message
python -m kubeagentic.cli test examples/simple_agent.yaml

# With custom message
python -m kubeagentic.cli test examples/simple_agent.yaml -m "What is Python?"
```

### Example 4: Use in Python Code

Create a file `test_agent.py`:

```python
from kubeagentic import Agent

# Create agent from config
agent = Agent.from_config_file("examples/simple_agent.yaml")

# Test the agent
response = agent.invoke("Tell me about artificial intelligence")
print(response["content"])
```

Run it:
```bash
python test_agent.py
```

---

## 📝 Create Your Own Agent

### Step 1: Create Configuration File

Create `my_agent.yaml`:

```yaml
version: "1.0"

agent:
  name: "my_custom_agent"
  description: "My first custom agent"
  
  llm:
    provider: "openai"
    model: "gpt-3.5-turbo"
    temperature: 0.7
    max_tokens: 1000
  
  system_prompt: |
    You are a helpful assistant that specializes in [YOUR DOMAIN].
    Be concise and accurate in your responses.
  
  tools: []
  
  memory:
    type: "buffer"
    max_messages: 10
  
  logging:
    level: "info"
    format: "json"
    output: "console"
  
  limits:
    max_tokens_per_request: 2000
    max_requests_per_minute: 60
    timeout_seconds: 30
```

### Step 2: Validate Your Configuration

```bash
python -m kubeagentic.cli validate my_agent.yaml
```

### Step 3: Test Your Agent

```bash
python -m kubeagentic.cli test my_agent.yaml -m "Hello!"
```

---

## 🔧 Working with Multiple Agents

```python
from kubeagentic import AgentManager

# Create manager
manager = AgentManager()

# Load multiple agents
manager.load_agent(config_path="examples/simple_agent.yaml")
manager.load_agent(config_path="my_agent.yaml")

# List all agents
print(manager.list_agents())

# Chat with specific agent
response = manager.chat(
    agent_name="simple_assistant",
    message="Hello!"
)
print(response["content"])
```

---

## 🔄 Advanced: Multiple LLM Providers with Fallback

Create `fallback_agent.yaml`:

```yaml
version: "1.0"

agent:
  name: "resilient_agent"
  description: "Agent with automatic fallback between LLM providers"
  
  # Multiple LLMs (will try in order of priority)
  llms:
    - provider: "openai"
      model: "gpt-4"
      priority: 1
      
    - provider: "openai"
      model: "gpt-3.5-turbo"
      priority: 2
  
  system_prompt: "You are a helpful assistant."
  
  tools: []
  
  memory:
    type: "buffer"
    max_messages: 10
  
  logging:
    level: "info"
```

If GPT-4 fails, it will automatically fall back to GPT-3.5-turbo!

---

## 📊 Available CLI Commands

```bash
# Show version
python -m kubeagentic.cli version

# Validate config
python -m kubeagentic.cli validate <config.yaml>

# Show agent info
python -m kubeagentic.cli info <config.yaml>

# Test agent
python -m kubeagentic.cli test <config.yaml> [-m "message"]

# Start API server (coming in Phase 2)
python -m kubeagentic.cli serve --config <config.yaml> --port 8000
```

---

## 🔑 Supported LLM Providers

### OpenAI
```yaml
llm:
  provider: "openai"
  model: "gpt-4"  # or gpt-3.5-turbo, gpt-4-turbo
```

Environment variable: `OPENAI_API_KEY`

### Anthropic (Claude)
```yaml
llm:
  provider: "anthropic"
  model: "claude-3-opus-20240229"
```

Environment variable: `ANTHROPIC_API_KEY`

### Ollama (Local)
```yaml
llm:
  provider: "ollama"
  model: "llama2"
  api_base: "http://localhost:11434"
```

No API key needed for local models!

### Azure OpenAI
```yaml
llm:
  provider: "azure_openai"
  model: "gpt-4"
  api_base: "https://your-resource.openai.azure.com/"
  extra:
    deployment_name: "gpt-4-deployment"
    api_version: "2024-02-15-preview"
```

Environment variables: `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`

---

## 🐛 Troubleshooting

### Issue: Import errors

**Solution:** Make sure virtual environment is activated and dependencies are installed:
```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### Issue: "API key not provided"

**Solution:** Set your API key:
```bash
export OPENAI_API_KEY="sk-your-key"
# OR add to .env file
```

### Issue: "Configuration validation failed"

**Solution:** Check your YAML syntax:
```bash
python -m kubeagentic.cli validate your_config.yaml
```

### Issue: Python version

**Solution:** Ensure Python 3.10+:
```bash
python --version
```

---

## 📚 Next Steps

1. ✅ **Read the full documentation:** See `README.md`
2. ✅ **Check requirements:** See `masterRequirements.md`
3. ✅ **View implementation status:** See `IMPLEMENTATION_STATUS.md`
4. ✅ **Explore examples:** Look in `examples/` directory
5. ✅ **Contribute:** Read `CONTRIBUTING.md`

---

## 🆘 Getting Help

- 📖 **Documentation:** Check `README.md` and `IMPLEMENTATION_STATUS.md`
- 🐛 **Issues:** Report bugs on GitHub Issues
- 💬 **Community:** Join our Discord (coming soon)
- 📧 **Email:** support@kubeagentic.io

---

## 🎉 Success!

You're now ready to build powerful AI agents with KubeAgentic!

**What you can do right now:**
- ✅ Define agents in YAML
- ✅ Validate configurations
- ✅ Test agents locally
- ✅ Use agents in Python
- ✅ Manage multiple agents
- ✅ Use multiple LLM providers

**Coming soon (Phase 2):**
- 🚀 REST API with OpenAI compatibility
- 🔐 Authentication & rate limiting
- 💾 Session management
- 📊 Metrics & monitoring

---

**Happy building! 🚀** 