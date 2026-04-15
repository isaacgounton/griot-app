# AnyLLM Integration Guide

This document explains how to use AnyLLM across the Griot application.

## Overview

AnyLLM provides universal LLM provider integration, allowing you to use multiple AI providers (OpenAI, Anthropic, Google, etc.) through a single interface.

## Backend Integration

### Quick Usage

```python
from app.utils.anyllm_helper import simple_complete, chat_complete

# Simple text completion
result = await simple_complete("Write a short poem about AI")

# Chat with message history
messages = [
    {"role": "user", "content": "Hello!"},
    {"role": "assistant", "content": "Hello! How can I help you?"},
    {"role": "user", "content": "Tell me about AI"}
]
response = await chat_complete(messages)
```

### Advanced Usage

```python
from app.services.anyllm_service import anyllm_service

# Get available providers
providers = await anyllm_service.get_providers()

# Get models for a specific provider
models = await anyllm_service.get_models("openai")

# Stream completion
request_data = {
    "provider": "openai",
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello"}],
    "temperature": 0.7
}

async for chunk in anyllm_service.stream_completion(request_data):
    # Process streaming chunks
    pass
```

### Environment Variables

Set up API keys for the providers you want to use:

```bash
# OpenAI
export OPENAI_API_KEY="your-openai-api-key"

# Anthropic
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# Google
export GOOGLE_API_KEY="your-google-api-key"

# Mistral
export MISTRAL_API_KEY="your-mistral-api-key"

# Add other provider API keys as needed
```

## Frontend Integration

### React Hook Usage

```tsx
import { useAnyLLM } from '../hooks/useAnyLLM';

function MyComponent() {
  const {
    providers,
    models,
    loading,
    error,
    currentProvider,
    currentModel,
    setProvider,
    complete,
    chat
  } = useAnyLLM();

  const handleComplete = async () => {
    try {
      const result = await complete("Write a story about AI");
      console.log(result);
    } catch (error) {
      console.error(error);
    }
  };

  return (
    <div>
      {/* Provider/Model selection UI */}
      {/* Your component JSX */}
    </div>
  );
}
```

### Simple Text Completion Hook

```tsx
import { useAnyLLMComplete } from '../hooks/useAnyLLM';

function QuickComplete() {
  const { complete, loading, error } = useAnyLLMComplete({
    provider: "openai",
    model: "gpt-3.5-turbo",
    temperature: 0.7
  });

  const handleComplete = async () => {
    const result = await complete("Summarize this text...");
  };

  return (
    <button onClick={handleComplete} disabled={loading}>
      {loading ? 'Processing...' : 'Complete'}
    </button>
  );
}
```

### Chat Hook

```tsx
import { useAnyLLMChat } from '../hooks/useAnyLLM';

function ChatComponent() {
  const { messages, loading, sendMessage, error } = useAnyLLMChat();

  const handleSendMessage = async (content: string) => {
    await sendMessage(content);
  };

  return (
    <div>
      {messages.map((msg, i) => (
        <div key={i}>
          <strong>{msg.role}:</strong> {msg.content}
        </div>
      ))}
      {/* Message input UI */}
    </div>
  );
}
```

### Universal Service Usage

```tsx
import { anyllm } from '../services/anyllm';

// Initialize service
await anyllm.initialize();

// Get recommended config
const config = await anyllm.getRecommendedConfig();

// Simple completion
const result = await anyllm.complete("Hello, world!");

// Chat with messages
const response = await anyllm.chat([
  { role: 'user', content: 'Hello' }
]);
```

## API Endpoints

### Get Providers
```
GET /api/anyllm/providers
```

### List Models
```
POST /api/anyllm/list-models
{
  "provider": "openai"
}
```

### Stream Completion
```
POST /api/anyllm/completion
{
  "provider": "openai",
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "temperature": 0.7
}
```

## Available Components

### Chat Interface
- Path: `/dashboard/chat`
- Full-featured chat interface with provider/model selection
- Streaming responses
- Thinking/reasoning display
- Message history

## Configuration

### Adding New Providers

1. Set the required environment variables for the provider
2. The provider will automatically appear in the providers list
3. Models will be dynamically loaded when the provider is selected

### Default Provider Selection

The system automatically selects providers in this order:
1. OpenAI (if available)
2. First available provider

### Default Model Selection

The system automatically selects models in this order:
1. gpt-3.5-turbo or gpt-4 (if available)
2. First available model

## Error Handling

- Missing API keys are handled gracefully
- Provider/model selection fallbacks
- Network error handling
- User-friendly error messages

## Performance

- Model caching to reduce API calls
- Streaming responses for real-time interaction
- Efficient React hooks with proper state management
- Backend service singleton pattern

## Security

- All endpoints require API key authentication
- Environment variables for API keys
- No API keys exposed to frontend
- Proper error handling to prevent information leakage