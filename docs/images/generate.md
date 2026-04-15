# AI Image Generation

Generate high-quality images from text prompts using state-of-the-art AI models like Together.ai's FLUX.

## 🎯 Overview

The AI Image Generation endpoint provides access to powerful image generation models through a simple REST API. Currently supports Together.ai's FLUX models for creating photorealistic and artistic images from text descriptions.

**Features:**
- High-quality AI image generation
- Customizable dimensions and quality settings
- Automatic S3 storage with direct URLs
- Environment-based configuration
- Async job processing for scalability

## 🚀 Quick Start

### Basic Image Generation

```bash
curl -X POST "http://localhost:8000/v1/images/generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A majestic mountain landscape at sunset with golden light reflecting on a crystal clear lake"
  }'
```

### Response

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

### Check Status

```bash
curl -X GET "http://localhost:8000/v1/images/generate/123e4567-e89b-12d3-a456-426614174000" \
  -H "X-API-Key: your-api-key"
```

## 📋 API Reference

### Endpoints

```
POST /v1/images/generate
GET /v1/images/generate/{job_id}
```

### Request Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `prompt` | string | - | ✅ | Text description of the image to generate (max 1000 chars) |
| `model` | string | env/auto | ❌ | AI model to use (uses TOGETHER_DEFAULT_MODEL) |
| `width` | integer | env/576 | ❌ | Image width in pixels (256-2048) |
| `height` | integer | env/1024 | ❌ | Image height in pixels (256-2048) |
| `steps` | integer | env/4 | ❌ | Number of inference steps (1-50) |
| `provider` | string | "together" | ❌ | AI provider (currently only "together") |

### Environment Configuration

Default values are configurable via environment variables:

```bash
# Together.ai Configuration
TOGETHER_API_KEY=your_api_key_here
TOGETHER_DEFAULT_MODEL=black-forest-labs/FLUX.1-schnell-Free
TOGETHER_DEFAULT_WIDTH=576
TOGETHER_DEFAULT_HEIGHT=1024
TOGETHER_DEFAULT_STEPS=4
```

### Response Format (Completed)

```json
{
  "job_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": {
    "image_url": "https://s3.amazonaws.com/bucket/generated-images/image.png",
    "prompt_used": "A majestic mountain landscape at sunset...",
    "model_used": "black-forest-labs/FLUX.1-schnell",
    "dimensions": {
      "width": 576,
      "height": 1024
    },
    "processing_time": 12.5
  }
}
```

## 🎨 Supported Models

### Together.ai FLUX Models

#### FLUX.1-schnell (Default)
- **Speed**: Fast (4-8 steps)
- **Quality**: High
- **Best for**: General purpose, rapid prototyping
- **Recommended steps**: 4-6

#### FLUX.1-dev
- **Speed**: Medium (8-16 steps)  
- **Quality**: Very High
- **Best for**: Professional artwork, detailed images
- **Recommended steps**: 12-20

### Model Selection

```json
{
  "prompt": "Professional headshot of a businessman",
  "model": "black-forest-labs/FLUX.1-dev",
  "steps": 12,
  "width": 768,
  "height": 768
}
```

## 📐 Dimension Guidelines

### Standard Sizes

| Aspect Ratio | Dimensions | Use Case |
|--------------|------------|----------|
| Portrait | 576 × 1024 | Social media, mobile |
| Landscape | 1024 × 576 | Desktop, presentations |
| Square | 768 × 768 | Profile pics, Instagram |
| Widescreen | 1280 × 720 | YouTube thumbnails |
| Ultra-wide | 1536 × 512 | Banners, headers |

### Performance vs Quality

| Steps | Quality | Speed | Use Case |
|-------|---------|-------|----------|
| 1-4 | Good | Fast | Rapid iteration, previews |
| 4-8 | High | Medium | Production content |
| 8-20 | Very High | Slow | Professional artwork |
| 20+ | Exceptional | Very Slow | Gallery-quality images |

## ✍️ Prompt Engineering

### Effective Prompts

**Good Prompt:**
```
"A photorealistic portrait of a young woman with curly brown hair, 
wearing a vintage leather jacket, soft natural lighting, 
professional photography style, shallow depth of field"
```

**Poor Prompt:**
```
"woman"
```

### Prompt Structure

1. **Subject**: What/who is the main focus
2. **Style**: Art style, photography type, medium
3. **Lighting**: Lighting conditions and mood
4. **Composition**: Camera angle, framing, depth
5. **Details**: Specific features, colors, textures

### Style Keywords

#### Photography Styles
- `professional photography`
- `portrait photography` 
- `landscape photography`
- `macro photography`
- `documentary style`

#### Artistic Styles
- `oil painting`
- `watercolor`
- `digital art`
- `concept art`
- `photorealistic`

#### Lighting
- `golden hour lighting`
- `studio lighting`
- `natural lighting`
- `dramatic lighting`
- `soft diffused light`

## 🎯 Use Cases & Examples

### Social Media Content

```json
{
  "prompt": "Modern minimalist workspace with laptop, coffee cup, and plants, clean aesthetic, soft natural lighting, Instagram style",
  "width": 1080,
  "height": 1080,
  "steps": 6
}
```

### Marketing Materials

```json
{
  "prompt": "Professional business team in modern office, diverse group collaborating, corporate photography style, bright lighting",
  "width": 1280,
  "height": 720,
  "steps": 8
}
```

### Product Visualization

```json
{
  "prompt": "Luxury watch on marble surface, dramatic lighting, commercial product photography, high-end aesthetic",
  "width": 768,
  "height": 768,
  "steps": 10
}
```

### Concept Art

```json
{
  "prompt": "Futuristic cityscape at night, neon lights, cyberpunk style, detailed digital art, atmospheric perspective",
  "width": 1024,
  "height": 576,
  "steps": 16
}
```

## 🔧 Advanced Usage

### Batch Generation

For multiple images, make parallel requests:

```python
import asyncio
import aiohttp

async def generate_images(prompts, api_key):
    async with aiohttp.ClientSession() as session:
        tasks = []
        for prompt in prompts:
            task = session.post(
                "http://localhost:8000/v1/images/generate",
                headers={"X-API-Key": api_key},
                json={"prompt": prompt}
            )
            tasks.append(task)
        
        responses = await asyncio.gather(*tasks)
        job_ids = [await r.json() for r in responses]
        return [job["job_id"] for job in job_ids]
```

### Quality Optimization

```json
{
  "prompt": "Ultra-detailed portrait, 8K resolution, professional studio lighting",
  "width": 1024,
  "height": 1024,
  "steps": 20,
  "model": "black-forest-labs/FLUX.1-dev"
}
```

### Speed Optimization

```json
{
  "prompt": "Quick concept sketch, simple composition",
  "width": 512,
  "height": 512,
  "steps": 4,
  "model": "black-forest-labs/FLUX.1-schnell"
}
```

## 🚨 Error Handling

### Common Errors

#### Service Unavailable (503)
```json
{
  "detail": "Image generation service is currently unavailable (API key not configured)"
}
```
**Solution**: Configure `TOGETHER_API_KEY` environment variable.

#### Bad Request (400)
```json
{
  "detail": "Only 'together' provider is currently supported"
}
```
**Solution**: Use `"provider": "together"` or omit the provider field.

#### Processing Failed
```json
{
  "status": "failed",
  "error": "Image generation failed: API rate limit exceeded"
}
```
**Solution**: Implement retry logic with exponential backoff.

### Error Recovery

```python
import time

def wait_for_generation(job_id, api_key, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = requests.get(
                f"http://localhost:8000/v1/images/generate/{job_id}",
                headers={"X-API-Key": api_key}
            )
            result = response.json()
            
            if result["status"] == "completed":
                return result["result"]
            elif result["status"] == "failed":
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
                else:
                    raise Exception(result["error"])
            
            time.sleep(5)  # Still processing
            
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise e
```

## 💰 Cost Optimization

### Strategies

1. **Use Appropriate Dimensions**
   - Smaller images = faster generation = lower cost
   - Use the minimum size needed for your use case

2. **Optimize Steps**
   - 4 steps: Good for previews and iteration
   - 8 steps: Sweet spot for most use cases
   - 16+ steps: Only when exceptional quality is needed

3. **Batch Processing**
   - Group similar requests to reduce overhead
   - Use environment defaults to avoid parameter parsing

### Cost Examples

Assuming Together.ai pricing (rates may vary):

| Dimensions | Steps | Est. Cost | Use Case |
|------------|-------|-----------|----------|
| 512×512 | 4 | $0.01 | Quick preview |
| 768×768 | 8 | $0.03 | Social media |
| 1024×1024 | 12 | $0.06 | High quality |
| 1536×1024 | 20 | $0.12 | Professional |

## 🔄 Integration Examples

### WordPress Plugin

```php
function generate_featured_image($post_title) {
    $response = wp_remote_post('http://your-api/v1/images/generate', [
        'headers' => ['X-API-Key' => 'your-key'],
        'body' => json_encode([
            'prompt' => "Blog featured image for: " . $post_title,
            'width' => 1200,
            'height' => 630
        ])
    ]);
    
    $job_id = json_decode(wp_remote_retrieve_body($response))->job_id;
    return poll_for_completion($job_id);
}
```

### React Hook

```javascript
import { useState, useEffect } from 'react';

export function useImageGeneration(prompt) {
    const [status, setStatus] = useState('idle');
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    
    useEffect(() => {
        if (!prompt) return;
        
        const generateImage = async () => {
            setStatus('generating');
            
            try {
                const response = await fetch('/v1/images/generate', {
                    method: 'POST',
                    headers: {
                        'X-API-Key': process.env.REACT_APP_API_KEY,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ prompt })
                });
                
                const { job_id } = await response.json();
                
                // Poll for completion
                const result = await pollForCompletion(job_id);
                setResult(result);
                setStatus('completed');
                
            } catch (err) {
                setError(err.message);
                setStatus('failed');
            }
        };
        
        generateImage();
    }, [prompt]);
    
    return { status, result, error };
}
```

## 📊 Monitoring & Analytics

### Key Metrics

Track these metrics for optimization:

- **Generation Time**: Average time per image
- **Success Rate**: Percentage of successful generations  
- **Error Types**: Most common failure reasons
- **Cost per Image**: Resource usage tracking
- **User Satisfaction**: Quality ratings

### Logging

```python
import logging

logger = logging.getLogger('image_generation')

# Log successful generations
logger.info(f"Image generated: {job_id}, prompt: {prompt[:50]}, time: {processing_time}s")

# Log failures with context
logger.error(f"Generation failed: {job_id}, error: {error}, prompt: {prompt}")

# Log cost tracking
logger.info(f"Cost tracking: {dimensions}, {steps} steps, estimated: ${cost}")
```

## 🔮 Roadmap

### Upcoming Features

- **Multiple Providers**: Midjourney, DALL-E integration
- **Style Transfer**: Apply artistic styles to existing images
- **Batch API**: Generate multiple images in single request
- **Webhooks**: Real-time completion notifications
- **Image Editing**: Inpainting, outpainting, variations

### Model Updates

Stay updated with new model releases:
- FLUX.2 models when available
- Specialized models for specific use cases
- Community-fine-tuned models

## 🤝 Community & Support

### Getting Help

1. **Documentation**: Check this guide first
2. **GitHub Issues**: Report bugs and request features
3. **Community Discord**: Connect with other developers
4. **Support Email**: For enterprise support

### Contributing

To contribute to image generation features:

1. Fork the repository
2. Add new providers in `app/services/ai/`
3. Update models in request validation
4. Add tests for new functionality
5. Submit pull request with documentation

See the [development guide](../README.md) for more information.