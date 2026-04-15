# Pollinations.AI Integration

The Griot includes full integration with Pollinations.AI, providing access to powerful AI-driven content generation capabilities including image generation, text generation, vision analysis, and text-to-speech.

## Overview

Pollinations.AI provides a unified API for multiple AI content generation services:

- **Image Generation**: Text-to-image and image-to-image with Flux and advanced models
- **Text Generation**: OpenAI-compatible chat completions and simple text generation
- **Vision Capabilities**: Analyze images and answer questions about visual content
- **Function Calling**: Enable AI to call external tools and functions
- **Audio Generation**: Text-to-speech with premium voices and speech-to-text transcription

## API Version

The integration uses Pollinations API v0.3.0 with the unified base URL `https://gen.pollinations.ai` and Bearer token authentication.

## Features

### Image Generation

**Text-to-Image:**
- Multiple high-quality models (Flux, etc.)
- Customizable dimensions (width/height)
- Seed control for reproducible results
- Image enhancement options
- Safety filters

**Image-to-Image:**
- Transform existing images with new prompts
- Maintain visual consistency while changing content
- Support for various image formats

**Transparent Backgrounds:**
- Generate images with transparency (select models)
- Perfect for overlays and composites

### Text Generation

**Simple Text Generation:**
- Generate text from prompts using GET API
- Quick and easy for simple use cases

**Advanced Chat Completions:**
- Full OpenAI-compatible POST API
- Multimodal support (text + images)
- Function calling support
- Multiple model options

**Vision Capabilities:**
- Analyze images and extract information
- Answer questions about visual content
- Object detection and recognition

### Audio Generation

**Text-to-Speech:**
- 6+ premium voices (alloy, echo, fable, onyx, nova, shimmer)
- High-quality MP3 format output
- Natural speech synthesis

**Speech-to-Text:**
- Transcribe audio files to text
- Support for various audio formats

## Authentication

### API Key Configuration

```bash
# Environment variable
POLLINATIONS_API_KEY=your_secret_key  # Get from enter.pollinations.ai
```

### Authentication Methods

**Preferred (Bearer Token):**
```bash
curl -X POST "https://gen.pollinations.ai/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{...}'
```

**Fallback (Query Parameter):**
```bash
curl "https://gen.pollinations.ai/text/generate?prompt=hello&key=YOUR_API_KEY"
```

### Key Types

- **Secret Keys (`sk_`)**: For server-side use, no rate limits, can spend Pollen
- **Publishable Keys (`pk_`)**: For client-side use, IP rate-limited (1 pollen/hour per IP+key)

### Benefits with API Key

- **Higher Rate Limits**: No 15-second cooldowns between requests
- **Premium Features**: Automatic logo removal on generated images
- **Priority Processing**: Faster queue processing
- **Advanced Models**: Access to state-of-the-art model tiers

## API Endpoints

All Pollinations endpoints are prefixed with `/api/pollinations`

### Image Endpoints

#### Generate Image (Async)
```bash
POST /api/pollinations/image/generate
```

**Request:**
```json
{
  "prompt": "A beautiful sunset over the ocean",
  "width": 1920,
  "height": 1080,
  "model": "flux",
  "enhance": true,
  "seed": 42,
  "safety_checker": true
}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Generate Image (Sync)
```bash
POST /api/pollinations/image/generate/sync
```

**Response:**
```json
{
  "success": true,
  "image_url": "https://s3.../generated_image.png",
  "metadata": {
    "model": "flux",
    "width": 1920,
    "height": 1080,
    "seed": 42
  }
}
```

#### Analyze Image (Vision)
```bash
POST /api/pollinations/vision/analyze
```

**Request:**
```json
{
  "image_url": "https://example.com/image.jpg",
  "prompt": "Describe this image in detail",
  "detail": "high"
}
```

#### List Image Models
```bash
GET /api/pollinations/models/image
```

### Text Endpoints

#### Generate Text (Async)
```bash
POST /api/pollinations/text/generate
```

**Request:**
```json
{
  "prompt": "Write a creative story about AI",
  "model": "openai",
  "temperature": 0.8,
  "max_tokens": 500
}
```

#### Chat Completions (Async)
```bash
POST /api/pollinations/chat/completions
```

**Request:**
```json
{
  "messages": [
    {"role": "system", "content": "You are a helpful assistant"},
    {"role": "user", "content": "What is the capital of France?"}
  ],
  "model": "openai",
  "temperature": 0.7
}
```

#### Generate Text (Sync)
```bash
POST /api/pollinations/text/generate/sync
```

#### Chat Completions (Sync)
```bash
POST /api/pollinations/chat/completions/sync
```

#### List Text Models
```bash
GET /api/pollinations/models/text
```

### Audio Endpoints

#### Text-to-Speech (Async)
```bash
POST /api/pollinations/audio/tts
```

**Request:**
```json
{
  "text": "Hello, this is a test of text to speech",
  "voice": "nova",
  "speed": 1.0
}
```

#### Audio Transcription (Async)
```bash
POST /api/pollinations/audio/transcribe
```

**Request:**
```json
{
  "audio_url": "https://example.com/audio.mp3",
  "language": "en"
}
```

#### Text-to-Speech (Sync)
```bash
POST /api/pollinations/audio/tts/sync
```

#### List TTS Voices
```bash
GET /api/pollinations/voices
```

**Response:**
```json
{
  "voices": [
    {
      "id": "alloy",
      "name": "Alloy",
      "gender": "neutral",
      "language": "en"
    },
    {
      "id": "nova",
      "name": "Nova",
      "gender": "female",
      "language": "en"
    }
  ]
}
```

## Job Queue Integration

All Pollinations operations are integrated with the Griot job queue system:

- **Async Processing**: Long-running operations processed in background
- **Status Tracking**: Real-time job status monitoring
- **S3 Storage**: Generated content automatically saved to S3
- **Error Handling**: Comprehensive error reporting and recovery
- **Result Persistence**: All results stored with metadata

### Check Job Status

```bash
GET /api/pollinations/{endpoint}/{job_id}
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "image_url": "https://s3.../image.png"
  },
  "error": null
}
```

## Usage Examples

### Generate Image

```bash
curl -X POST "http://localhost:8000/api/pollinations/image/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "A beautiful sunset over the ocean",
    "width": 1920,
    "height": 1080,
    "model": "flux",
    "enhance": true
  }'
```

### Generate Text

```bash
curl -X POST "http://localhost:8000/api/pollinations/text/generate/sync" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a creative story about AI",
    "model": "openai",
    "temperature": 0.8
  }'
```

### Text-to-Speech

```bash
curl -X POST "http://localhost:8000/api/pollinations/audio/tts/sync" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Hello, this is a test of text to speech",
    "voice": "nova"
  }'
```

### Analyze Image

```bash
curl -X POST "http://localhost:8000/api/pollinations/vision/analyze" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/image.jpg",
    "prompt": "Describe what you see in this image"
  }'
```

## Integration with Existing Features

The Pollinations integration seamlessly works with existing Griot features:

- **Video Generation**: Use Pollinations for script generation and voice synthesis
- **Image Processing**: Generate backgrounds and overlays for video content
- **AI Workflows**: Combine with existing AI pipelines for enhanced content creation
- **Dashboard**: All endpoints accessible through the admin dashboard
- **Job Management**: Unified job tracking across all services

## Models Reference

### Image Models

| Model | Description | Best For |
|-------|-------------|----------|
| `flux` | FLUX.1-schnell | Fast, high-quality images |
| `flux-dev` | FLUX.1-dev | Highest quality, slower |

### Text Models

| Model | Description | Best For |
|-------|-------------|----------|
| `openai` | OpenAI GPT | General purpose |
| `mistral` | Mistral AI | Fast, efficient |
| `claude` | Anthropic Claude | Long context |

### TTS Voices

| Voice | Gender | Description |
|-------|--------|-------------|
| `alloy` | Neutral | Balanced, clear speech |
| `echo` | Male | Deep, authoritative |
| `fable` | Male | Warm, storytelling |
| `onyx` | Male | Professional, calm |
| `nova` | Female | Bright, energetic |
| `shimmer` | Female | Soft, natural |

## Best Practices

### Image Generation

1. **Use Descriptive Prompts**: Detailed prompts produce better results
2. **Adjust Dimensions**: Match your target platform's requirements
3. **Use Seed for Consistency**: Same seed + prompt = same image
4. **Enable Enhancement**: Improves quality for most use cases
5. **Safety Checker**: Enable for public content

### Text Generation

1. **Choose Right Model**: Match model to task complexity
2. **Temperature Control**: Lower for factual, higher for creative
3. **Max Tokens**: Set appropriate limits for your use case
4. **System Prompts**: Provide clear context and instructions

### Audio Generation

1. **Voice Selection**: Match voice to content tone
2. **Speed Adjustment**: Normal speed (1.0) for most content
3. **Text Preparation**: Clean text before TTS for best results

## Troubleshooting

### Common Issues

**Rate Limiting:**
- Use API key to avoid rate limits
- Add delay between requests if needed
- Consider upgrading Pollinations tier

**Image Generation Fails:**
- Check prompt doesn't violate safety guidelines
- Verify model is available
- Reduce dimensions if too large

**TTS Quality Issues:**
- Try different voices
- Clean up text (remove special characters)
- Adjust speed parameter

### Error Messages

**"Invalid API Key":**
- Verify POLLINATIONS_API_KEY is set correctly
- Check key hasn't expired
- Ensure key type matches use case

**"Model Not Available":**
- List available models to verify
- Check model name spelling
- Try alternative model

**"Job Failed":**
- Check job status endpoint for details
- Review error message in job result
- Verify input parameters are valid

## Performance Tips

### Speed Optimization

1. **Use Sync Endpoints**: For quick operations (< 30 seconds)
2. **Optimal Image Sizes**: 1024x1024 or smaller for speed
3. **Simple Prompts**: Faster processing, still good results
4. **Cache Results**: Store generated content for reuse

### Cost Optimization

1. **Free Tier**: Use free models (flux-schnell-free)
2. **Batch Operations**: Combine multiple requests
3. **Reduce Dimensions**: Smaller images cost less
4. **Limit Tokens**: Set appropriate max_tokens for text

## Resources

- **Pollinations Website**: [pollinations.ai](https://pollinations.ai)
- **API Documentation**: Available at enter.pollinations.ai
- **Get API Key**: [enter.pollinations.ai](https://enter.pollinations.ai)
- **Support**: Contact Pollinations support for account issues

---

*Last updated: January 2025*
