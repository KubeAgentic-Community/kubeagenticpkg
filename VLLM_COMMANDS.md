# vLLM Quick Command Reference

## 🚀 Complete Setup & Testing Commands

### Step 1: Setup Virtual Environment (First Time Only)

```bash
# Navigate to project
cd /Users/sudeshmu/work/opensource/kubeagenticV2

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Verify installation
python test_vllm_demo.py
```

---

## 🎮 Running with vLLM

### Option A: Two Terminal Setup (Recommended)

#### Terminal 1: Start vLLM Server

```bash
# Install vLLM (one time only)
pip install vllm

# Start vLLM server with your model
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --host 0.0.0.0 \
    --port 8000

# KEEP THIS TERMINAL RUNNING!
```

#### Terminal 2: Run KubeAgentic Commands

```bash
# Navigate to project
cd /Users/sudeshmu/work/opensource/kubeagenticV2

# Activate venv
source .venv/bin/activate

# Validate simple configuration
python -m kubeagentic.cli validate examples/vllm_simple.yaml

# Validate advanced configuration
python -m kubeagentic.cli validate examples/vllm_advanced.yaml

# Show agent info
python -m kubeagentic.cli info examples/vllm_simple.yaml

# Test simple agent
python -m kubeagentic.cli test examples/vllm_simple.yaml

# Test with custom message
python -m kubeagentic.cli test examples/vllm_simple.yaml --message "What is AI?"

# Test advanced agent (with fallback)
python -m kubeagentic.cli test examples/vllm_advanced.yaml --message "Explain machine learning"
```

---

## 📝 Example Commands for Different Models

### Llama 2 7B (Default)
```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --port 8000
```

### Llama 2 13B (More Capable)
```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-13b-chat-hf \
    --port 8000
```

### Mistral 7B
```bash
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.1 \
    --port 8000
```

### CodeLlama 7B (For Code)
```bash
python -m vllm.entrypoints.openai.api_server \
    --model codellama/CodeLlama-7b-Instruct-hf \
    --port 8000
```

---

## 🔧 Update Configuration for Your Model

Edit `examples/vllm_simple.yaml`:

```yaml
llm:
  provider: "vllm"
  model: "YOUR_MODEL_NAME_HERE"  # Change this
  api_base: "http://localhost:8000/v1"
```

---

## 🎯 All KubeAgentic CLI Commands

```bash
# Make sure venv is activated first!
source .venv/bin/activate

# 1. Validate configuration
python -m kubeagentic.cli validate examples/vllm_simple.yaml
python -m kubeagentic.cli validate examples/vllm_advanced.yaml

# 2. Show agent information
python -m kubeagentic.cli info examples/vllm_simple.yaml
python -m kubeagentic.cli info examples/vllm_advanced.yaml

# 3. Test agent with default message
python -m kubeagentic.cli test examples/vllm_simple.yaml
python -m kubeagentic.cli test examples/vllm_advanced.yaml

# 4. Test agent with custom message
python -m kubeagentic.cli test examples/vllm_simple.yaml -m "Your question here"
python -m kubeagentic.cli test examples/vllm_advanced.yaml -m "Your question here"

# 5. Show version
python -m kubeagentic.cli version
```

---

## 🐍 Python Code Examples

### Simple Usage
```python
# Save as test_simple.py
from kubeagentic import Agent

# Load agent
agent = Agent.from_config_file("examples/vllm_simple.yaml")

# Ask question
response = agent.invoke("What is artificial intelligence?")
print(response["content"])
```

Run: `python test_simple.py`

### Advanced Usage with Manager
```python
# Save as test_manager.py
from kubeagentic import AgentManager

# Create manager
manager = AgentManager()

# Load agents
manager.load_agent(config_path="examples/vllm_simple.yaml")
manager.load_agent(config_path="examples/vllm_advanced.yaml")

# List available agents
print("Available agents:", manager.list_agents())

# Chat with agent
response = manager.chat(
    agent_name="vllm_assistant",
    message="Explain deep learning"
)
print(response["content"])
```

Run: `python test_manager.py`

### Async Usage
```python
# Save as test_async.py
import asyncio
from kubeagentic import Agent

async def main():
    agent = Agent.from_config_file("examples/vllm_simple.yaml")
    response = await agent.ainvoke("What is machine learning?")
    print(response["content"])

asyncio.run(main())
```

Run: `python test_async.py`

---

## ✅ Quick Test Checklist

Run these commands in order:

```bash
# 1. Setup (first time only)
cd /Users/sudeshmu/work/opensource/kubeagenticV2
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Verify installation
python test_vllm_demo.py

# 3. Start vLLM server (separate terminal)
pip install vllm
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --port 8000

# 4. Test KubeAgentic (back in first terminal)
source .venv/bin/activate
python -m kubeagentic.cli validate examples/vllm_simple.yaml
python -m kubeagentic.cli test examples/vllm_simple.yaml -m "Hello!"
```

---

## 🐛 Troubleshooting Commands

### Check if vLLM server is running
```bash
curl http://localhost:8000/v1/models
```

### Check available models
```bash
curl http://localhost:8000/v1/models | python -m json.tool
```

### Test vLLM directly
```bash
curl http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "meta-llama/Llama-2-7b-chat-hf",
        "prompt": "Hello, how are you?",
        "max_tokens": 50
    }'
```

### Check venv is activated
```bash
which python
# Should show: /Users/sudeshmu/work/opensource/kubeagenticV2/.venv/bin/python
```

### List installed packages
```bash
pip list | grep -E "(kubeagentic|langchain|langgraph)"
```

---

## 📚 Documentation Files

- `VLLM_SETUP_GUIDE.md` - Comprehensive setup guide
- `VLLM_COMMANDS.md` - This file (quick reference)
- `README.md` - General documentation
- `QUICKSTART.md` - Getting started guide
- `IMPLEMENTATION_STATUS.md` - Project status

---

## 🎯 Most Common Commands (Copy-Paste Ready)

```bash
# Complete workflow
cd /Users/sudeshmu/work/opensource/kubeagenticV2
source .venv/bin/activate
python -m kubeagentic.cli test examples/vllm_simple.yaml -m "Explain AI simply"
```

---

**Need help? See VLLM_SETUP_GUIDE.md for detailed instructions!** 