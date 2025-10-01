# vLLM Setup Guide for KubeAgentic

This guide shows you how to use **vLLM** (high-performance LLM inference engine) with KubeAgentic.

---

## 🎯 What is vLLM?

vLLM is a fast and easy-to-use library for LLM inference that:
- ✅ Provides OpenAI-compatible API
- ✅ Supports various open-source models (Llama 2, Mistral, etc.)
- ✅ Runs on GPU for fast inference
- ✅ Optimized for high throughput

---

## 📋 Prerequisites

- Python 3.10+
- CUDA-capable GPU (recommended)
- Docker (optional, for containerized deployment)

---

## 🚀 Quick Start

### Option 1: Using vLLM Server (Recommended)

#### Step 1: Install vLLM

```bash
# Install vLLM
pip install vllm
```

#### Step 2: Start vLLM Server

```bash
# Start vLLM server with Llama 2 7B model
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --host 0.0.0.0 \
    --port 8000

# Or with Mistral 7B
python -m vllm.entrypoints.openai.api_server \
    --model mistralai/Mistral-7B-Instruct-v0.1 \
    --host 0.0.0.0 \
    --port 8000

# With GPU specification
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 1 \
    --dtype float16
```

The server will start at `http://localhost:8000`

#### Step 3: Verify vLLM Server

```bash
# Test if server is running
curl http://localhost:8000/v1/models

# Test completion
curl http://localhost:8000/v1/completions \
    -H "Content-Type: application/json" \
    -d '{
        "model": "meta-llama/Llama-2-7b-chat-hf",
        "prompt": "Hello, how are you?",
        "max_tokens": 50
    }'
```

### Option 2: Using Docker

```bash
# Pull vLLM Docker image
docker pull vllm/vllm-openai:latest

# Run vLLM server
docker run --gpus all \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-2-7b-chat-hf
```

---

## 🔧 Setup KubeAgentic with vLLM

### Step 1: Setup Virtual Environment

```bash
# Navigate to project directory
cd /Users/sudeshmu/work/opensource/kubeagenticV2

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Set Environment Variables (Optional)

```bash
# If your vLLM server is not on localhost:8000
export VLLM_BASE_URL="http://localhost:8000/v1"

# If you need API key (usually not required for local)
export VLLM_API_KEY="your-key"

# Optional: OpenAI key for fallback
export OPENAI_API_KEY="sk-your-openai-key"
```

### Step 3: Update Example Configuration

The examples are already configured! Just update the model name if needed:

Edit `examples/vllm_simple.yaml`:
```yaml
llm:
  provider: "vllm"
  model: "YOUR_MODEL_NAME"  # e.g., meta-llama/Llama-2-7b-chat-hf
  api_base: "http://localhost:8000/v1"
```

---

## 🎮 Running Examples

### Test 1: Validate Configuration

```bash
# Activate venv if not already active
source .venv/bin/activate

# Validate simple example
python -m kubeagentic.cli validate examples/vllm_simple.yaml

# Validate advanced example
python -m kubeagentic.cli validate examples/vllm_advanced.yaml
```

Expected output:
```
✓ Configuration is valid!
Agent: vllm_assistant
Description: AI assistant powered by vLLM local model
```

### Test 2: Show Agent Information

```bash
# Simple agent info
python -m kubeagentic.cli info examples/vllm_simple.yaml

# Advanced agent info
python -m kubeagentic.cli info examples/vllm_advanced.yaml
```

### Test 3: Test Simple Agent

```bash
# Test with default message
python -m kubeagentic.cli test examples/vllm_simple.yaml

# Test with custom message
python -m kubeagentic.cli test examples/vllm_simple.yaml \
    --message "What is machine learning?"

# Another example
python -m kubeagentic.cli test examples/vllm_simple.yaml \
    --message "Explain Python programming in simple terms"
```

### Test 4: Test Advanced Agent (with Fallback)

```bash
# This will try vLLM first, then fallback if needed
python -m kubeagentic.cli test examples/vllm_advanced.yaml \
    --message "Tell me about large language models"

# Test with longer conversation
python -m kubeagentic.cli test examples/vllm_advanced.yaml \
    --message "Write a short story about AI and humans working together"
```

---

## 🐍 Using in Python Code

### Simple Usage

Create `test_vllm.py`:

```python
from kubeagentic import Agent

# Load agent
agent = Agent.from_config_file("examples/vllm_simple.yaml")

# Single question
response = agent.invoke("What is artificial intelligence?")
print(response["content"])

# Another question
response = agent.invoke("Explain neural networks simply")
print(response["content"])
```

Run it:
```bash
source .venv/bin/activate
python test_vllm.py
```

### Advanced Usage with Multiple Agents

Create `test_vllm_advanced.py`:

```python
from kubeagentic import AgentManager

# Create manager
manager = AgentManager()

# Load agents
manager.load_agent(config_path="examples/vllm_simple.yaml")
manager.load_agent(config_path="examples/vllm_advanced.yaml")

# List agents
print("Available agents:", manager.list_agents())

# Chat with simple agent
response = manager.chat(
    agent_name="vllm_assistant",
    message="What is vLLM?"
)
print(f"\nSimple Agent: {response['content']}\n")

# Chat with advanced agent (has fallback)
response = manager.chat(
    agent_name="vllm_advanced_assistant",
    message="Explain the benefits of local LLM deployment"
)
print(f"\nAdvanced Agent: {response['content']}\n")
```

Run it:
```bash
source .venv/bin/activate
python test_vllm_advanced.py
```

### Async Usage

Create `test_vllm_async.py`:

```python
import asyncio
from kubeagentic import Agent

async def main():
    # Load agent
    agent = Agent.from_config_file("examples/vllm_simple.yaml")
    
    # Async invoke
    response = await agent.ainvoke("What are the advantages of open-source AI?")
    print(response["content"])
    
    # Multiple concurrent calls
    tasks = [
        agent.ainvoke("What is Python?"),
        agent.ainvoke("What is machine learning?"),
        agent.ainvoke("What is deep learning?"),
    ]
    
    responses = await asyncio.gather(*tasks)
    for i, resp in enumerate(responses, 1):
        print(f"\nResponse {i}: {resp['content']}")

# Run
asyncio.run(main())
```

Run it:
```bash
source .venv/bin/activate
python test_vllm_async.py
```

---

## 🎯 Complete Setup Commands (Copy-Paste Ready)

### Terminal 1: Start vLLM Server

```bash
# Install vLLM (one time)
pip install vllm

# Start server
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --host 0.0.0.0 \
    --port 8000
```

Keep this terminal running!

### Terminal 2: Run KubeAgentic

```bash
# Navigate to project
cd /Users/sudeshmu/work/opensource/kubeagenticV2

# Activate venv
source .venv/bin/activate

# If not installed yet, install dependencies
pip install -r requirements.txt

# Validate configuration
python -m kubeagentic.cli validate examples/vllm_simple.yaml

# Test simple agent
python -m kubeagentic.cli test examples/vllm_simple.yaml \
    --message "Hello! Tell me about yourself."

# Test advanced agent with fallback
python -m kubeagentic.cli test examples/vllm_advanced.yaml \
    --message "Explain the concept of AI agents"
```

---

## 📝 Customizing for Your vLLM Model

### Edit the Configuration

```yaml
# examples/vllm_simple.yaml
llm:
  provider: "vllm"
  model: "YOUR_MODEL_NAME"  # Change this to your model
  api_base: "http://localhost:8000/v1"  # Change if different
  temperature: 0.7
  max_tokens: 1000
```

### Common vLLM Models

```yaml
# Llama 2 7B
model: "meta-llama/Llama-2-7b-chat-hf"

# Llama 2 13B
model: "meta-llama/Llama-2-13b-chat-hf"

# Mistral 7B
model: "mistralai/Mistral-7B-Instruct-v0.1"

# CodeLlama
model: "codellama/CodeLlama-7b-Instruct-hf"

# Vicuna
model: "lmsys/vicuna-7b-v1.5"
```

---

## 🐛 Troubleshooting

### Issue: "Connection refused"

**Solution:** Make sure vLLM server is running:
```bash
curl http://localhost:8000/v1/models
```

### Issue: "Model not found"

**Solution:** Check the model name matches your vLLM server:
```bash
# List available models
curl http://localhost:8000/v1/models
```

### Issue: "Out of memory"

**Solution:** Use a smaller model or reduce batch size:
```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --max-model-len 2048
```

### Issue: "Slow responses"

**Solution:** Enable GPU and adjust parameters:
```bash
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-2-7b-chat-hf \
    --tensor-parallel-size 1 \
    --dtype float16 \
    --gpu-memory-utilization 0.9
```

---

## 🚀 Performance Tips

1. **Use GPU**: vLLM is much faster on GPU
2. **Adjust batch size**: Increase for higher throughput
3. **Use FP16**: Set `--dtype float16` for faster inference
4. **Enable KV cache**: Default in vLLM, improves speed
5. **Parallel processing**: Use `--tensor-parallel-size` for multi-GPU

---

## 📊 Comparison: vLLM vs Cloud APIs

| Feature | vLLM (Local) | OpenAI API |
|---------|-------------|------------|
| Cost | Free (after setup) | Pay per token |
| Privacy | Complete privacy | Data sent to cloud |
| Speed | Fast (with GPU) | Network dependent |
| Models | Open-source only | Proprietary models |
| Setup | Requires GPU setup | Ready to use |
| Customization | Full control | Limited |

---

## 🎉 Success Checklist

- [ ] vLLM server is running (`curl http://localhost:8000/v1/models`)
- [ ] Virtual environment is activated (`source .venv/bin/activate`)
- [ ] Dependencies are installed (`pip list | grep kubeagentic`)
- [ ] Configuration validates (`python -m kubeagentic.cli validate examples/vllm_simple.yaml`)
- [ ] Test agent works (`python -m kubeagentic.cli test examples/vllm_simple.yaml`)

---

## 📚 Next Steps

1. ✅ Experiment with different models
2. ✅ Adjust temperature and max_tokens
3. ✅ Create custom system prompts
4. ✅ Use agent manager for multiple agents
5. ✅ Integrate into your applications

---

**Happy building with vLLM! 🚀** 