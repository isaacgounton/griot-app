# OpenAI-Compatible LLM Integration

Use any OpenAI-compatible LLM with the Media API by configuring custom base URLs and model names. This allows you to use local models, alternative providers, or self-hosted LLM services.

## Overview

The Media API supports any LLM service that implements the OpenAI Chat Completions API format. This includes:

- **Local LLMs**: Ollama, LM Studio, vLLM, Text Generation WebUI
- **Cloud Providers**: Together AI, Anyscale, OpenRouter, Replicate
- **Self-Hosted**: Custom deployments with OpenAI-compatible APIs
- **OpenAI**: The original OpenAI API (default)

## Configuration

Set these environment variables to use custom LLM providers:

```bash
# Required: Your API key (format depends on provider)
OPENAI_API_KEY=your_api_key_here

# Optional: Custom base URL (defaults to OpenAI)
OPENAI_BASE_URL=http://localhost:11434/v1

# Optional: Custom model name (defaults to gpt-4o)
OPENAI_MODEL=llama3.1:8b
```

## Popular Provider Examples

### 1. **Ollama (Local)**

Run powerful models locally with Ollama:

```bash
# Install and start Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama serve

# Pull a model
ollama pull llama3.1:8b

# Configure Media API
OPENAI_API_KEY=dummy_key_for_ollama
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:8b
```

**Recommended Models:**
- `llama3.1:8b` - Great balance of quality and speed
- `llama3.1:70b` - Higher quality, slower generation
- `qwen2.5:7b` - Excellent for script generation
- `mistral:7b` - Fast and reliable

### 2. **LM Studio (Local)**

Easy-to-use GUI for local LLM hosting:

```bash
# Download and install LM Studio
# Start a model with OpenAI-compatible server

# Configure Media API
OPENAI_API_KEY=lm-studio
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_MODEL=your-loaded-model-name
```

### 3. **Together AI (Cloud)**

High-performance cloud LLM service:

```bash
# Get API key from together.ai
OPENAI_API_KEY=your_together_api_key
OPENAI_BASE_URL=https://api.together.xyz/v1
OPENAI_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo
```

**Popular Models:**
- `meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo` - Fast and affordable
- `meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo` - Higher quality
- `mistralai/Mixtral-8x7B-Instruct-v0.1` - Excellent for creative content

### 4. **OpenRouter (Cloud)**

Access to multiple LLM providers through one API:

```bash
# Get API key from openrouter.ai
OPENAI_API_KEY=sk-or-v1-your_openrouter_key
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=meta-llama/llama-3.1-8b-instruct:free
```

**Popular Models:**
- `meta-llama/llama-3.1-8b-instruct:free` - Free tier
- `anthropic/claude-3.5-sonnet` - Very high quality
- `google/gemini-pro-1.5` - Good for creative tasks

### 5. **Anyscale (Cloud)**

Serverless LLM platform:

```bash
# Get API key from anyscale.com
OPENAI_API_KEY=esecret_your_anyscale_key
OPENAI_BASE_URL=https://api.endpoints.anyscale.com/v1
OPENAI_MODEL=meta-llama/Llama-2-7b-chat-hf
```

### 6. **vLLM (Self-Hosted)**

High-performance LLM serving:

```bash
# Start vLLM server
python -m vllm.entrypoints.openai.api_server \
  --model meta-llama/Llama-3.1-8B-Instruct \
  --port 8000

# Configure Media API
OPENAI_API_KEY=token-abc123
OPENAI_BASE_URL=http://localhost:8000/v1
OPENAI_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

### 7. **Text Generation WebUI (Local)**

Popular local LLM interface:

```bash
# Start with OpenAI extension
python server.py --listen --extensions openai

# Configure Media API
OPENAI_API_KEY=dummy_key
OPENAI_BASE_URL=http://localhost:5000/v1
OPENAI_MODEL=your-loaded-model
```

## Model Selection Guide

### **For Script Generation**

| Use Case | Recommended Models | Quality | Speed | Cost |
|----------|-------------------|---------|-------|------|
| **High Quality** | Llama-3.1-70B, Claude-3.5-Sonnet | ⭐⭐⭐⭐⭐ | ⭐⭐ | $$$ |
| **Balanced** | Llama-3.1-8B, Qwen2.5-7B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | $$ |
| **Fast/Local** | Llama-3.1-8B, Mistral-7B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | $ |
| **Free** | Llama-3.1-8B (OpenRouter), Ollama | ⭐⭐⭐ | ⭐⭐⭐ | Free |

### **For Video Search Queries**

| Use Case | Recommended Models | Visual Understanding | Speed |
|----------|-------------------|---------------------|-------|
| **Best Quality** | GPT-4o, Claude-3.5-Sonnet | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Good Balance** | Llama-3.1-8B, Qwen2.5-7B | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Fast Local** | Mistral-7B, Llama-3.1-8B | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

## Testing Your Configuration

### 1. **Test AI Script Generation**

```bash
curl -X POST "http://localhost:8000/v1/ai/script/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "test script generation",
    "provider": "openai"
  }'
```

### 2. **Check Job Status**

```bash
curl "http://localhost:8000/v1/ai/script/generate/{job_id}" \
  -H "X-API-Key: your_api_key"
```

### 3. **Verify Model Usage**

Check the response for:
- `provider_used`: Should show "openai"
- `model_used`: Should show your custom model name

## Performance Optimization

### **Local LLMs**

```bash
# Optimize for speed
OPENAI_MODEL=llama3.1:8b-instruct-q4_K_M  # Quantized model

# Optimize for quality
OPENAI_MODEL=llama3.1:70b                 # Larger model
```

### **Cloud Providers**

```bash
# Balance cost and quality
OPENAI_MODEL=meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo

# Maximum quality
OPENAI_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
```

## Groq-Compatible LLMs

The Media API also supports Groq-compatible LLM providers through environment variables. This allows you to use alternative Groq API endpoints or self-hosted Groq-compatible services.

### **Environment Variables**

```bash
GROQ_API_KEY=your_groq_api_key
GROQ_BASE_URL=http://localhost:8080/v1        # Optional: For Groq-compatible services only
GROQ_MODEL=mixtral-8x7b-32768                # Optional: Custom model name
```

### **Official Groq**

Default configuration (no base URL needed):

```bash
GROQ_API_KEY=gsk_your_groq_api_key
GROQ_MODEL=mixtral-8x7b-32768          # Fast inference
# or
GROQ_MODEL=llama3-70b-8192             # Higher quality

# DO NOT set GROQ_BASE_URL for official Groq API
# The client will use the default https://api.groq.com/openai/v1
```

### **Groq-Compatible Self-Hosted**

For services that implement the Groq API format:

```bash
GROQ_API_KEY=your_custom_key
GROQ_BASE_URL=http://localhost:8080/v1
GROQ_MODEL=your-local-model
```

### **Dual Provider Setup**

Use both OpenAI and Groq providers for redundancy:

```bash
# Primary: OpenAI
OPENAI_API_KEY=sk-proj-your_openai_key
OPENAI_MODEL=gpt-4o

# Fallback: Groq
GROQ_API_KEY=gsk_your_groq_key
GROQ_MODEL=mixtral-8x7b-32768
```

The AI services will automatically select the best available provider based on your configuration.

## Advanced Configuration

### **Multiple Providers**

You can use different models for different tasks by setting environment variables per service:

```bash
# Script generation with high-quality model
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL=gpt-4o

# Video search with fast local model
GROQ_API_KEY=dummy_key_for_local
GROQ_MODEL=llama3.1:8b
```

### **Custom Headers**

Some providers require additional headers. You can modify the service files to add custom headers:

```python
# In script_generator.py or video_search_query_generator.py
headers = {}
if openai_base_url and "your-provider.com" in openai_base_url:
    headers["X-Custom-Header"] = "value"

self.openai_client = OpenAI(
    api_key=openai_key, 
    base_url=openai_base_url,
    default_headers=headers
)
```

### **Request Timeouts**

For slower local models, you might need to increase timeouts:

```python
self.openai_client = OpenAI(
    api_key=openai_key,
    base_url=openai_base_url,
    timeout=120.0  # 2 minutes for local models
)
```

## Troubleshooting

### **Common Issues**

**Connection Refused:**
```bash
# Check if your LLM server is running
curl http://localhost:11434/v1/models

# Verify the base URL in your config
echo $OPENAI_BASE_URL
```

**Authentication Failed:**
```bash
# Some providers need specific API key formats
OPENAI_API_KEY=Bearer your_actual_key  # Some providers
OPENAI_API_KEY=dummy_key               # Local servers
```

**Model Not Found:**
```bash
# List available models
curl http://localhost:11434/v1/models \
  -H "Authorization: Bearer dummy_key"

# Update your model name
OPENAI_MODEL=correct-model-name
```

**Slow Response Times:**
```bash
# Use smaller/quantized models for speed
OPENAI_MODEL=llama3.1:8b-instruct-q4_K_M  # Ollama
OPENAI_MODEL=meta-llama/Llama-3.1-8B      # Cloud
```

### **Debug Mode**

Enable debug logging to see API requests:

```bash
LOG_LEVEL=DEBUG
```

This will show:
- API requests being made
- Response times
- Model names being used
- Error details

## Best Practices

### **Local Development**
1. **Use Ollama**: Easiest setup for local development
2. **Start Small**: Begin with 7B-8B parameter models
3. **Monitor Resources**: Watch CPU/GPU/RAM usage
4. **Cache Models**: Download models once, reuse across projects

### **Production Deployment**
1. **Use Cloud Providers**: For reliability and scale
2. **Monitor Costs**: Track API usage and costs
3. **Implement Fallbacks**: Have backup providers configured
4. **Load Balance**: Distribute requests across multiple endpoints

### **Model Selection**
1. **Test Thoroughly**: Compare quality across different models
2. **Benchmark Speed**: Measure response times for your use case
3. **Consider Context**: Some models excel at creative tasks vs factual content
4. **Update Regularly**: New models are released frequently

## Example Configurations

### **Development Setup (Local)**
```bash
API_KEY=dev_api_key
OPENAI_API_KEY=dummy_key
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:8b
GROQ_API_KEY=dummy_key
PEXELS_API_KEY=your_pexels_key
```

### **Production Setup (Cloud)**
```bash
API_KEY=prod_api_key
OPENAI_API_KEY=sk-proj-your_openai_key
OPENAI_MODEL=gpt-4o
GROQ_API_KEY=gsk_your_groq_key
GROQ_MODEL=llama3-70b-8192
PEXELS_API_KEY=your_pexels_key
```

### **Hybrid Setup (Local + Cloud)**
```bash
API_KEY=hybrid_api_key
OPENAI_API_KEY=dummy_key               # Local for development
OPENAI_BASE_URL=http://localhost:11434/v1
OPENAI_MODEL=llama3.1:8b
GROQ_API_KEY=gsk_your_groq_key        # Cloud for production
GROQ_MODEL=llama3-70b-8192
PEXELS_API_KEY=your_pexels_key
```

## Support

For provider-specific issues:
- **Ollama**: [github.com/ollama/ollama](https://github.com/ollama/ollama)
- **LM Studio**: [lmstudio.ai/docs](https://lmstudio.ai/docs)
- **Together AI**: [docs.together.ai](https://docs.together.ai)
- **OpenRouter**: [openrouter.ai/docs](https://openrouter.ai/docs)

For Media API integration issues, check the [troubleshooting guide](troubleshooting.md).

---

*This feature enables complete flexibility in LLM provider choice while maintaining full compatibility with all Media API features.*