# MCP Server Integration

The Griot includes a Model Context Protocol (MCP) server that enables AI agents (like Claude) to programmatically create and manage videos and other media content.

## Overview

The MCP server provides:
- **AI Agent Integration**: Connect Claude and other AI agents to the Griot API
- **Video Creation**: Create short videos from scenes and configuration
- **Job Status Monitoring**: Track processing status of video jobs
- **Voice Management**: List and validate TTS voices and providers
- **Server-Sent Events**: Real-time updates via SSE protocol

## Connection Details

### Endpoint
```
http://localhost:8000/api/mcp/sse
```

### Protocol
- **Transport**: Server-Sent Events (SSE)
- **Message Format**: JSON-RPC 2.0
- **Authentication**: X-API-Key header required

### Authentication

All MCP requests require API key authentication:

```bash
curl -H "X-API-Key: your_api_key" \
  http://localhost:8000/api/mcp/sse
```

## Available MCP Tools

### 1. create-short-video

Create short videos from scenes and configuration.

**Parameters:**

```json
{
  "scenes": [
    {
      "text": "Welcome to this amazing video",
      "duration": 3.0,
      "searchTerms": ["welcome", "introduction"]
    }
  ],
  "voice_provider": "kokoro",
  "voice_name": "af_bella",
  "language": "en",
  "resolution": "1080x1920",
  "add_captions": true,
  "caption_style": "viral_bounce",
  "background_music": false
}
```

**Parameters Schema:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `scenes` | array | Yes | Array of scene objects with text, duration, and searchTerms |
| `voice_provider` | string | Yes | TTS provider (kokoro, edge, kitten) |
| `voice_name` | string | Yes | Specific voice name from provider |
| `language` | string | No | Language code (default: "en") |
| `resolution` | string | No | Video resolution (default: "1080x1920") |
| `add_captions` | boolean | No | Add captions to video (default: true) |
| `caption_style` | string | No | Caption style (default: "viral_bounce") |
| `background_music` | boolean | No | Add background music (default: false) |

**Response:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Video creation job started"
}
```

### 2. get-video-status

Check the processing status of a video job.

**Parameters:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Response:**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "final_video_url": "https://s3.../video.mp4",
    "processing_time": 125.5,
    "scenes_count": 5
  },
  "error": null
}
```

**Status Values:**
- `pending`: Job is queued
- `processing`: Job is being processed
- `completed`: Job completed successfully
- `failed`: Job failed with error

### 3. list-tts-voices

Get available TTS voices by provider and language.

**Parameters:**

```json
{
  "provider": "kokoro",
  "language": "en"
}
```

**Parameters Schema:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `provider` | string | No | Filter by provider (kokoro, edge, kitten) |
| `language` | string | No | Filter by language code |

**Response:**

```json
{
  "voices": [
    {
      "id": "af_bella",
      "name": "Bella",
      "language": "en",
      "gender": "female",
      "provider": "kokoro"
    },
    {
      "id": "am_michael",
      "name": "Michael",
      "language": "en",
      "gender": "male",
      "provider": "kokoro"
    }
  ]
}
```

### 4. validate-voice-combination

Validate if a voice/provider combination is valid.

**Parameters:**

```json
{
  "voice_provider": "kokoro",
  "voice_name": "af_bella"
}
```

**Response (Valid):**

```json
{
  "valid": true,
  "voice": {
    "id": "af_bella",
    "name": "Bella",
    "language": "en",
    "gender": "female",
    "provider": "kokoro"
  }
}
```

**Response (Invalid):**

```json
{
  "valid": false,
  "error": "Voice 'af_bella' not found for provider 'kokoro'"
}
```

## Usage Examples

### Claude AI Agent Integration

**Step 1: Connect to MCP Server**

```python
import anthropic
import httpx

client = anthropic.Anthropic(api_key="your_claude_api_key")

# Configure MCP server
mcp_config = {
    "mcpServers": {
        "griot": {
            "url": "http://localhost:8000/api/mcp/sse",
            "headers": {
                "X-API-Key": "your_griot_api_key"
            }
        }
    }
}
```

**Step 2: Create Video via MCP**

```python
# Claude will use the MCP tool to create video
response = client.messages.create(
    model="claude-sonnet-4-6",
    max_tokens=1024,
    tools=[
        {
            "type": "function",
            "function": {
                "name": "create-short-video",
                "description": "Create a short video from scenes",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "scenes": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "text": {"type": "string"},
                                    "duration": {"type": "number"},
                                    "searchTerms": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    }
                                }
                            }
                        },
                        "voice_provider": {"type": "string"},
                        "voice_name": {"type": "string"}
                    },
                    "required": ["scenes", "voice_provider", "voice_name"]
                }
            }
        }
    ],
    messages=[
        {
            "role": "user",
            "content": "Create a 30-second video about AI with 3 scenes"
        }
    ]
)
```

### Direct API Usage (JSON-RPC 2.0)

**Create Video Request:**

```bash
curl -X POST "http://localhost:8000/api/mcp/sse" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
      "name": "create-short-video",
      "arguments": {
        "scenes": [
          {
            "text": "Welcome to the future of AI",
            "duration": 5.0,
            "searchTerms": ["future", "technology", "AI"]
          }
        ],
        "voice_provider": "kokoro",
        "voice_name": "af_bella"
      }
    }
  }'
```

**Check Status Request:**

```bash
curl -X POST "http://localhost:8000/api/mcp/sse" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/call",
    "params": {
      "name": "get-video-status",
      "arguments": {
        "job_id": "550e8400-e29b-41d4-a716-446655440000"
      }
    }
  }'
```

## MCP Tool Reference

### Complete Tool List

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `create-short-video` | Create short videos from scenes | scenes, voice_provider, voice_name, ... |
| `get-video-status` | Check video job status | job_id |
| `list-tts-voices` | List available TTS voices | provider, language |
| `validate-voice-combination` | Validate voice/provider combo | voice_provider, voice_name |

### Request/Response Format

All MCP tools follow JSON-RPC 2.0 specification:

**Request Format:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "tools/call",
  "params": {
    "name": "tool_name",
    "arguments": {
      // Tool-specific parameters
    }
  }
}
```

**Response Format:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    // Tool-specific result
  }
}
```

**Error Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": {}
  }
}
```

## Server-Sent Events (SSE)

The MCP server uses SSE for real-time communication:

### Connection

```bash
curl -N -H "X-API-Key: your_api_key" \
  http://localhost:8000/api/mcp/sse
```

### Event Types

**Tool Call Event:**
```
event: tool_call
data: {"jsonrpc":"2.0","method":"tools/call","params":{...}}
```

**Tool Result Event:**
```
event: tool_result
data: {"jsonrpc":"2.0","id":1,"result":{...}}
```

**Error Event:**
```
event: error
data: {"jsonrpc":"2.0","id":1,"error":{...}}
```

## Integration Patterns

### AI Agent Workflow

1. **Discovery**: Agent discovers available MCP tools
2. **Planning**: Agent plans video creation based on user request
3. **Tool Selection**: Agent selects appropriate MCP tools
4. **Execution**: Agent invokes tools with parameters
5. **Monitoring**: Agent monitors job status via get-video-status
6. **Result Delivery**: Agent delivers final result to user

### Video Creation Pipeline

```
User Request → AI Agent → MCP: create-short-video
                    ↓
              Job Created (job_id)
                    ↓
              MCP: get-video-status (polling)
                    ↓
              Status: completed
                    ↓
              Result: final_video_url
```

## Error Handling

### Common Errors

**Authentication Error:**
```json
{
  "error": {
    "code": -32000,
    "message": "Authentication failed",
    "data": "Invalid or missing X-API-Key header"
  }
}
```

**Invalid Parameters:**
```json
{
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "Missing required parameter: scenes"
  }
}
```

**Tool Not Found:**
```json
{
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": "Unknown tool: unknown_tool"
  }
}
```

**Job Not Found:**
```json
{
  "error": {
    "code": -32001,
    "message": "Job not found",
    "data": "Job ID does not exist"
  }
}
```

## Best Practices

### For AI Agents

1. **Validate Parameters**: Check voice combinations before creating videos
2. **Monitor Progress**: Poll job status regularly for long-running jobs
3. **Handle Errors**: Implement proper error handling and retry logic
4. **Cache Results**: Store job IDs and results for efficiency
5. **Rate Limiting**: Respect API rate limits when making requests

### For Developers

1. **Use Async Operations**: Long-running operations should use async jobs
2. **Implement Timeouts**: Set appropriate timeouts for MCP requests
3. **Log Everything**: Log all MCP interactions for debugging
4. **Handle SSE Disconnections**: Implement reconnection logic
5. **Validate Responses**: Always validate MCP tool responses

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to MCP server

**Solutions**:
- Verify Griot API is running
- Check X-API-Key header is correct
- Ensure MCP endpoint is accessible
- Check firewall/network settings

### Tool Execution Fails

**Problem**: MCP tool returns error

**Solutions**:
- Validate all required parameters are provided
- Check voice_provider and voice_name combination
- Verify job_id is valid for status checks
- Review error message in response

### Job Status Issues

**Problem**: Job status always returns "pending"

**Solutions**:
- Wait longer before checking status (processing takes time)
- Check job_queue service is running
- Verify Redis connection is healthy
- Check application logs for errors

## Security Considerations

### API Key Management

1. **Never Expose Keys**: Don't include API keys in client-side code
2. **Use Environment Variables**: Store keys in environment variables
3. **Rotate Keys Regularly**: Change API keys periodically
4. **Use Separate Keys**: Use different keys for different environments

### Access Control

1. **Authentication Required**: All MCP requests require valid API key
2. **Rate Limiting**: Implement rate limiting for MCP endpoints
3. **Input Validation**: Validate all parameters before processing
4. **Job Isolation**: Users can only access their own jobs

## Resources

- **MCP Specification**: [modelcontextprotocol.io](https://modelcontextprotocol.io)
- **Claude Documentation**: [anthropic.com](https://anthropic.com)
- **Griot API Docs**: [Main Documentation](../README.md)

---

*Last updated: January 2025*
