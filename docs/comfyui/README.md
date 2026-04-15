# ComfyUI Integration

The Griot includes integration with ComfyUI for custom video generation workflows, enabling advanced AI-powered video creation capabilities.

## Overview

ComfyUI provides:
- **Custom Workflows**: Design complex video generation pipelines
- **Node-Based Editor**: Visual workflow design interface
- **Advanced AI Models**: Support for Stable Diffusion, Video diffusion, and more
- **Flexible Integration**: Embed in Griot pipelines for seamless automation
- **API Access**: Remote API integration for workflow execution

## Features

### Workflow Management

- **Upload Workflows**: Import ComfyUI workflow JSON files
- **Execute Workflows**: Run workflows with custom parameters
- **Queue Management**: Multiple workflow execution queues
- **Result Retrieval**: Get generated videos and metadata

### Authentication

Multiple authentication methods supported:
- **No Auth**: For local ComfyUI instances
- **HTTP Basic Auth**: Username and password protection
- **Bearer Token**: API key authentication
- **Custom Headers**: Additional HTTP headers for authentication

### Integration Patterns

- **Standalone**: Direct ComfyUI workflow execution
- **Pipeline Integration**: Use within existing Griot video pipelines
- **Batch Processing**: Execute multiple workflows in parallel
- **Custom Nodes**: Support for custom ComfyUI nodes

## Configuration

### Environment Variables

```bash
# ComfyUI Server URL (required)
COMFYUI_URL=https://your-comfyui-instance.com/

# Authentication (optional, choose one)
COMFYUI_USERNAME=your_username        # HTTP Basic Auth username
COMFYUI_PASSWORD=your_password        # HTTP Basic Auth password
COMFYUI_API_KEY=your_api_key          # Bearer token authentication

# Custom Headers (optional, JSON format)
COMFYUI_CUSTOM_HEADERS={"X-Custom-Header": "value"}
```

### Authentication Setup

#### No Authentication (Local Development)
```bash
COMFYUI_URL=http://localhost:8188
```

#### HTTP Basic Authentication
```bash
COMFYUI_URL=https://comfyui.example.com/
COMFYUI_USERNAME=admin
COMFYUI_PASSWORD=secure_password
```

#### Bearer Token Authentication
```bash
COMFYUI_URL=https://comfyui.example.com/
COMFYUI_API_KEY=your_bearer_token_here
```

#### Custom Headers
```bash
COMFYUI_URL=https://comfyui.example.com/
COMFYUI_CUSTOM_HEADERS={"X-API-Key": "key123", "X-Client": "griot"}
```

## API Endpoints

All ComfyUI endpoints are prefixed with `/api/v1/comfyui`

### Execute Workflow

Execute a ComfyUI workflow with optional parameters.

**Endpoint:**
```bash
POST /api/v1/comfyui/execute
```

**Request:**
```json
{
  "workflow": {
    "nodes": [
      {
        "id": 1,
        "type": "CheckpointLoaderSimple",
        "inputs": {
          "ckpt_name": "v1-5-pruned.ckpt"
        }
      },
      {
        "id": 2,
        "type": "CLIPTextEncode",
        "inputs": {
          "text": "beautiful sunset over the ocean",
          "clip": ["1", 1]
        }
      }
    ]
  },
  "parameters": {
    "prompt": "beautiful sunset over the ocean",
    "width": 1920,
    "height": 1080,
    "steps": 50
  }
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "ComfyUI workflow execution started"
}
```

### Execute Workflow from File

Execute a workflow from a JSON file.

**Endpoint:**
```bash
POST /api/v1/comfyui/execute/file
```

**Request (multipart/form-data):**
```bash
workflow_file: workflow.json
parameters: {"prompt": "custom prompt"}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "workflow_file": "workflow.json"
}
```

### Get Workflow Status

Check the status of a workflow execution.

**Endpoint:**
```bash
GET /api/v1/comfyui/status/{job_id}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "output_video_url": "https://s3.../video.mp4",
    "output_images": ["https://s3.../image1.png"],
    "metadata": {
      "workflow_type": "video_generation",
      "processing_time": 125.5
    }
  },
  "error": null
}
```

### List Available Workflows

List all available workflow templates.

**Endpoint:**
```bash
GET /api/v1/comfyui/workflows
```

**Response:**
```json
{
  "workflows": [
    {
      "name": "text_to_video",
      "description": "Generate video from text prompt",
      "file": "text_to_video.json"
    },
    {
      "name": "image_to_video",
      "description": "Animate image to video",
      "file": "image_to_video.json"
    }
  ]
}
```

## Usage Examples

### Basic Workflow Execution

```bash
curl -X POST "http://localhost:8000/api/v1/comfyui/execute" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "workflow": {
      "nodes": [...]
    },
    "parameters": {
      "prompt": "A beautiful landscape"
    }
  }'
```

### Execute Workflow File

```bash
curl -X POST "http://localhost:8000/api/v1/comfyui/execute/file" \
  -H "X-API-Key: your_api_key" \
  -F "workflow_file=@/path/to/workflow.json" \
  -F 'parameters={"prompt": "custom prompt", "width": 1920}'
```

### Check Status

```bash
curl -X GET "http://localhost:8000/api/v1/comfyui/status/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key"
```

## Workflow Examples

### Text-to-Video Workflow

```json
{
  "nodes": [
    {
      "id": 1,
      "type": "CheckpointLoaderSimple",
      "inputs": {
        "ckpt_name": "sd_v1-5.ckpt"
      }
    },
    {
      "id": 2,
      "type": "CLIPTextEncode",
      "inputs": {
        "text": "{prompt}",
        "clip": ["1", 1]
      }
    },
    {
      "id": 3,
      "type": "KSampler",
      "inputs": {
        "seed": 42,
        "steps": 50,
        "cfg": 7,
        "sampler_name": "euler",
        "scheduler": "normal",
        "denoise": 1,
        "model": ["1", 0],
        "positive": ["2", 0],
        "negative": ["2", 1]
      }
    },
    {
      "id": 4,
      "type": "VHS_VideoCombine",
      "inputs": {
        "frame_rate": 30,
        "loop_count": 0,
        "images": ["3", 0]
      }
    }
  ]
}
```

### Image-to-Video Workflow

```json
{
  "nodes": [
    {
      "id": 1,
      "type": "LoadImage",
      "inputs": {
        "image": "input_image.png"
      }
    },
    {
      "id": 2,
      "type": "IPAdapterApply",
      "inputs": {
        "weight": 0.6,
        "image": ["1", 0]
      }
    },
    {
      "id": 3,
      "type": "AnimateDiff",
      "inputs": {
        "model": ["2", 0],
        "motion_scale": 1.0,
        "frames": 30
      }
    }
  ]
}
```

## Integration with Video Pipelines

### Topic-to-Video with ComfyUI

```bash
curl -X POST "http://localhost:8000/api/v1/ai/footage-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "amazing space facts",
    "use_comfyui": true,
    "comfyui_workflow": "text_to_video",
    "comfyui_parameters": {
      "prompt": "{script}",
      "width": 1920,
      "height": 1080
    }
  }'
```

### Custom Workflow in Pipeline

```bash
curl -X POST "http://localhost:8000/api/v1/ai/scenes-to-video" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [
      {
        "text": "Amazing space discovery",
        "duration": 5.0,
        "use_comfyui": true,
        "workflow": "space_scene.json"
      }
    ]
  }'
```

## Best Practices

### Workflow Design

1. **Keep Workflows Simple**: Start with basic workflows
2. **Test Locally**: Test in ComfyUI UI before API use
3. **Use Templates**: Create reusable workflow templates
4. **Document Parameters**: Document all workflow parameters
5. **Version Control**: Track workflow versions in git

### Performance Optimization

1. **Optimize Steps**: Reduce sampling steps for faster generation
2. **Batch Processing**: Process multiple items in one workflow
3. **Cache Models**: Keep models loaded in ComfyUI
4. **Use GPU**: Ensure ComfyUI has GPU access
5. **Monitor Resources**: Track CPU/GPU/memory usage

### Error Handling

1. **Validate Workflows**: Check workflow JSON before execution
2. **Handle Timeouts**: Set appropriate timeout values
3. **Retry Logic**: Implement retry for failed workflows
4. **Log Errors**: Capture detailed error information
5. **Fallback Strategies**: Have backup workflows ready

## Troubleshooting

### Common Issues

**Connection Refused:**
```
Error: Cannot connect to ComfyUI server
```

**Solutions:**
- Verify COMFYUI_URL is correct
- Check ComfyUI server is running
- Ensure firewall allows connection
- Test URL in browser

**Authentication Failed:**
```
Error: Authentication failed
```

**Solutions:**
- Verify username/password are correct
- Check API key is valid
- Ensure authentication method matches ComfyUI config
- Test credentials in ComfyUI UI

**Workflow Execution Failed:**
```
Error: Workflow execution failed
```

**Solutions:**
- Validate workflow JSON syntax
- Check all required nodes are available
- Verify node inputs are correct
- Test workflow in ComfyUI UI first
- Check ComfyUI server logs

**Timeout Errors:**
```
Error: Workflow execution timeout
```

**Solutions:**
- Increase timeout value
- Optimize workflow for speed
- Reduce complexity/sampling steps
- Check ComfyUI server performance

### Debug Mode

Enable debug logging for ComfyUI integration:

```python
import logging
logging.getLogger("app.services.comfyui").setLevel(logging.DEBUG)
```

## Advanced Features

### Custom Nodes

Support for ComfyUI custom nodes:

1. Install custom nodes in ComfyUI
2. Use in workflow JSON
3. Griot will execute via API

**Example:**
```json
{
  "id": 10,
  "type": "MyCustomNode",
  "inputs": {
    "custom_parameter": "value"
  }
}
```

### Dynamic Parameters

Replace parameters in workflows dynamically:

**Workflow Template:**
```json
{
  "inputs": {
    "text": "{prompt}",
    "width": "{width}",
    "height": "{height}"
  }
}
```

**Execution:**
```json
{
  "parameters": {
    "prompt": "beautiful sunset",
    "width": 1920,
    "height": 1080
  }
}
```

### Batch Processing

Execute multiple workflows in parallel:

```bash
for workflow in workflow1.json workflow2.json workflow3.json; do
  curl -X POST "http://localhost:8000/api/v1/comfyui/execute/file" \
    -H "X-API-Key: your_api_key" \
    -F "workflow_file=@$workflow" &
done
wait
```

## Resources

- **ComfyUI GitHub**: [github.com/comfyanonymous/ComfyUI](https://github.com/comfyanonymous/ComfyUI)
- **ComfyUI Documentation**: Available in GitHub repository
- **Workflow Examples**: Community examples on GitHub and Discord
- **Custom Nodes**: ComfyUI Custom Nodes repository

---

*Last updated: January 2025*
