# Image Processing Documentation

This section documents all image-related endpoints provided by the Griot, including both AI generation and editing capabilities.

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| [/v1/images/generate](./generate.md) | POST | Generate images from text prompts using AI |
| [/v1/images/generate/{job_id}](./generate.md#check-status) | GET | Get the status of an image generation job |
| [/v1/images/edit](./edit.md) | POST | Edit images by overlaying multiple images |
| [/v1/images/edit/{job_id}](./edit.md#get-job-status) | GET | Get the status of an image edit job |
| [/v1/pollinations/image/generate](./pollinations.md) | POST | Generate images using Pollinations AI |
| [/v1/pollinations/vision/analyze](./pollinations.md) | POST | Analyze images using Pollinations vision AI |
| [/v1/pollinations/models/image](./pollinations.md) | GET | List available Pollinations image models |

## Feature Overview

### 🎨 AI Image Generation (New!)

Generate high-quality images from text descriptions using state-of-the-art AI models:

- **Together.ai FLUX Models**: Photorealistic and artistic image generation
- **Customizable Dimensions**: From 256×256 to 2048×2048 pixels
- **Quality Control**: Adjustable inference steps for speed vs quality
- **Environment Configuration**: Default settings via environment variables

[**📖 Full Documentation**](./generate.md)

### 🧠 Pollinations AI Integration

Access advanced AI services for image generation and vision analysis:

- **Image Generation**: Create images using Pollinations specialized models
- **Vision Analysis**: Analyze images with multimodal AI capabilities
- **Model Selection**: Access to various image and text models
- **Upload Support**: Direct file upload for vision analysis

*For detailed Pollinations documentation, see [pollinations.md](./pollinations.md)*

## Common Use Cases

### Content Creation

- **Social Media Posts**: Generate unique visuals for platforms
- **Marketing Materials**: Create custom branded imagery
- **Blog Headers**: Generate relevant article images
- **Product Mockups**: Visualize products in different settings

### Business Applications

- **Logo Integration**: Add watermarks and branding to existing images
- **Template Systems**: Generate dynamic visual templates
- **E-commerce**: Create product lifestyle images
- **Presentations**: Generate custom slide backgrounds and graphics

### Creative Workflows

- **Concept Art**: Generate initial visual concepts
- **Storyboarding**: Create visual narratives
- **Prototyping**: Rapid visual mockup creation
- **Artistic Projects**: AI-assisted creative work

## Quick Start Examples

### Generate a Simple Image

```bash
curl -X POST "http://localhost:8000/v1/images/generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A serene mountain landscape at sunset"
  }'
```

### Generate with Custom Settings

```bash
curl -X POST "http://localhost:8000/v1/images/generate" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Professional headshot of a businesswoman",
    "width": 768,
    "height": 768,
    "steps": 8
  }'
```

### Edit Existing Image

```bash
curl -X POST "http://localhost:8000/v1/images/edit" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "overlays": [
      {
        "image_url": "https://example.com/logo.png",
        "x": 10,
        "y": 10,
        "width": 100,
        "height": 50
      }
    ]
  }'
```

## Environment Setup

For AI image generation, configure these environment variables:

```bash
# Required
TOGETHER_API_KEY=your_together_api_key

# Optional (with defaults)
TOGETHER_DEFAULT_MODEL=black-forest-labs/FLUX.1-schnell-Free
TOGETHER_DEFAULT_WIDTH=576
TOGETHER_DEFAULT_HEIGHT=1024
TOGETHER_DEFAULT_STEPS=4

# Core services
S3_ACCESS_KEY=your_s3_key
S3_SECRET_KEY=your_s3_secret
S3_BUCKET_NAME=your_bucket
```

## Integration with Video Pipelines

The image generation endpoint integrates seamlessly with the AI video pipelines:

- **Script-to-Video Pipeline**: Automatically generates custom images for each video segment
- **Standalone Generation**: Create images independently for other uses
- **Batch Processing**: Generate multiple images concurrently

## Performance Guidelines

### Image Generation Times

| Dimensions | Steps | Typical Time | Use Case |
|------------|-------|--------------|----------|
| 512×512 | 4 | 5-10 seconds | Quick previews |
| 768×768 | 8 | 10-15 seconds | Social media |
| 1024×1024 | 12 | 15-25 seconds | High quality |
| 1536×1024 | 20 | 30-45 seconds | Professional |

### Optimization Tips

1. **Use Environment Defaults**: Avoid specifying dimensions if defaults work
2. **Batch Requests**: Generate multiple images in parallel
3. **Cache Results**: Store generated images for reuse
4. **Monitor Costs**: Track API usage and optimize accordingly

## Error Handling

All image endpoints follow standard HTTP status codes:

- **200**: Successful operation
- **400**: Bad request (invalid parameters)
- **401**: Unauthorized (invalid API key)
- **404**: Resource not found
- **503**: Service unavailable (API key not configured)
- **500**: Internal server error

### Common Issues

#### Image Generation Failed

```json
{
  "status": "failed",
  "error": "Together.ai API error 429: Rate limit exceeded"
}
```

**Solution**: Implement exponential backoff and retry logic.

#### Service Unavailable

```json
{
  "detail": "Image generation service is currently unavailable"
}
```

**Solution**: Check `TOGETHER_API_KEY` environment variable.

#### Invalid Dimensions

```json
{
  "detail": "Image width must be between 256 and 2048 pixels"
}
```

**Solution**: Use supported dimension ranges.

## Best Practices

### Prompt Engineering

- **Be Specific**: Include details about style, lighting, composition
- **Use Keywords**: Add artistic or photographic style terms
- **Avoid Negatives**: Focus on what you want, not what you don't want
- **Test Iterations**: Refine prompts based on results

### Quality Control

- **Start Small**: Test with lower resolution and steps first
- **Iterate Quickly**: Use 4 steps for rapid prototyping
- **Scale Up**: Increase steps and resolution for final versions
- **Monitor Costs**: Balance quality needs with budget constraints

### Production Deployment

- **Load Balancing**: Distribute requests across multiple workers
- **Caching**: Cache frequently requested images
- **Monitoring**: Track generation times and success rates
- **Fallbacks**: Implement fallback strategies for failures

## Future Enhancements

### Planned Features

- **Additional AI Models**: Support for DALL-E, Midjourney
- **Style Transfer**: Apply artistic styles to existing images
- **Image Variations**: Generate variations of existing images
- **Batch Generation**: Single API call for multiple images
- **Real-time Streaming**: Progressive image generation

### Community Requests

- **Custom Model Fine-tuning**: Train models on specific datasets
- **Advanced Editing**: Inpainting, outpainting, object removal
- **Format Support**: SVG, WebP, AVIF output formats
- **Webhook Notifications**: Real-time completion alerts

## Support & Community

### Getting Help

1. **Documentation**: Start with the detailed guides
2. **Examples**: Check code examples in each section
3. **GitHub Issues**: Report bugs and request features
4. **Discord**: Join the developer community

### Contributing

- **Bug Reports**: Help us identify and fix issues
- **Feature Requests**: Suggest new capabilities
- **Documentation**: Improve guides and examples
- **Code Contributions**: Submit pull requests

---

*For detailed API reference and advanced usage, see the individual endpoint documentation.*
