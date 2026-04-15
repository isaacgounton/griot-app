# Text Routes Documentation

This directory contains documentation for all text-related endpoints in the Media Master API.

## Available Endpoints

### Text Generation

- **Generate Text**: `POST /api/v1/text/generate`
- **Generate Script**: `POST /api/v1/text/generate/script`
- **Generate Image Prompt**: `POST /api/v1/text/generate/image-prompt`
- **Discover Topics**: `POST /api/v1/text/discover/topics`

### Pollinations AI Integration

- **Generate Text**: `POST /api/v1/pollinations/text/generate`
- **Chat Completions**: `POST /api/v1/pollinations/chat/completions`

### Job Status

- **Check Job Status**: `GET /api/v1/jobs/{job_id}/status`

## Common Use Cases

### Text Generation

Generate high-quality text content using advanced AI models for various creative and professional applications. Supports different text types including articles, scripts, prompts, and creative writing.

### Script Generation

Create structured scripts and narratives with proper formatting and dialogue. Perfect for content creators, filmmakers, and educators needing scripted content.

### Image Prompt Generation

Generate detailed, descriptive prompts optimized for AI image generation. Helps create better visual content by crafting precise and effective prompts.

### Topic Discovery

Analyze text content to automatically identify and extract key topics and themes. Useful for content categorization, research, and content management.

### Pollinations AI Integration

Access Pollinations AI services for advanced text generation and conversational AI capabilities, including chat completions and specialized text processing.

## Advanced Features

### Multi-Model Support

- **Diverse AI Models**: Access to multiple language models for different use cases
- **Model Selection**: Choose appropriate models based on content type and requirements
- **Quality Optimization**: Automatic model selection for optimal output quality

### Content Structuring

- **Script Formatting**: Proper dialogue and scene formatting for scripts
- **Topic Organization**: Hierarchical topic extraction and organization
- **Prompt Engineering**: Optimized prompts for various AI image generation models

### Pollinations AI Features

- **Conversational AI**: Advanced chat completion capabilities
- **Specialized Models**: Access to domain-specific language models
- **Context Awareness**: Maintain conversation context across interactions

## Error Handling

All text endpoints follow standard HTTP status codes:

- **200**: Successful operation
- **400**: Bad request (invalid parameters or malformed JSON)
- **401**: Unauthorized (missing or invalid API key)
- **404**: Resource not found (invalid job ID or endpoint)
- **422**: Validation error (invalid input parameters)
- **429**: Rate limit exceeded
- **500**: Internal server error (processing failure or system issues)

Detailed error messages are provided in the response body for debugging and error resolution.
