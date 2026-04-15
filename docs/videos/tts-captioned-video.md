# TTS-Captioned Video Generation

Create professional videos with AI-generated speech and synchronized captions. This advanced endpoint combines text-to-speech audio generation, background visual effects, and customizable captions to produce engaging video content automatically.

## Features Overview

### 🎯 Core Features

- **AI Text-to-Speech**: Multiple TTS providers (Kokoro, Piper, Edge TTS, Kitten) with 100+ voices
- **Background Effects**: Ken Burns effect, pan, or static background images
- **Synchronized Captions**: Word-level timing with customizable styling
- **High-Quality Output**: Professional video output with embedded subtitles
- **Flexible Input**: Text input for TTS or pre-existing audio files
- **Custom Dimensions**: Support for various aspect ratios and resolutions

### 🎤 TTS Providers & Voices

| Provider | Quality | Speed | Voices | Languages |
|----------|---------|-------|--------|-----------|
| **Kokoro** (Default) | ⭐⭐⭐⭐⭐ | Fast | 50+ | English (US/GB) |
| **Piper** | ⭐⭐⭐⭐ | Fast | 1000+ | 20+ languages |
| **Edge TTS** | ⭐⭐⭐⭐⭐ | Medium | 200+ | 100+ languages |
| **Kitten** | ⭐⭐⭐⭐ | Medium | 50+ | English variants |

### 🎨 Background Effects

| Effect | Description | Best For |
|--------|-------------|----------|
| **Ken Burns** (Default) | Slow zoom and pan across image | Cinematic, storytelling |
| **Pan** | Horizontal/vertical movement | Product showcases |
| **None** | Static background | Simple presentations |

### 📝 Caption Styling

- **Font Size**: Customizable (default: 120px)
- **Colors**: Font, shadow, and stroke colors (hex format)
- **Position**: Top, center, or bottom placement
- **Timing**: Word-level synchronization with TTS audio

## API Endpoint

```http
POST /api/v1/videos/advanced/tts-captioned-video
```

## Request Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `background_url` | string | URL of the background image to use |

### Optional Parameters

#### Content Input (One Required)

| Parameter | Type | Description |
|-----------|------|-------------|
| `text` | string | Text to convert to speech (for TTS generation) |
| `audio_url` | string | URL of pre-existing audio file |

#### Video Dimensions

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `width` | integer | 1080 | Video width in pixels |
| `height` | integer | 1920 | Video height in pixels |

#### TTS Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `tts_provider` | string | "kokoro" | TTS provider: "kokoro", "piper", "edge", "kitten" |
| `voice` | string | "af_heart" | Voice name (provider-specific) |
| `speed` | float | 1.0 | Speech speed multiplier (0.5-2.0) |
| `volume_multiplier` | float | 1.0 | Volume adjustment (0.1-2.0) |

#### Caption Styling

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `caption_font_size` | integer | 120 | Font size in pixels |
| `caption_font_color` | string | "#ffffff" | Font color (hex format) |
| `caption_shadow_color` | string | "#000000" | Shadow color (hex format) |
| `caption_stroke_color` | string | "#000000" | Stroke/outline color (hex format) |
| `caption_position` | string | "bottom" | Caption position: "top", "center", "bottom" |

#### Background Effects

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `image_effect` | string | "ken_burns" | Background effect: "ken_burns", "pan", "none" |

#### Processing Mode

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sync` | boolean | false | Process synchronously and return result immediately (true) or use async job queue (false) |

## Request Examples

### Basic TTS Video

```json
{
  "background_url": "https://example.com/background.jpg",
  "text": "Welcome to our amazing product showcase!",
  "width": 1080,
  "height": 1920
}
```

### Advanced Configuration

```json
{
  "background_url": "https://example.com/scenic-image.jpg",
  "text": "Experience the beauty of nature in stunning detail.",
  "width": 1080,
  "height": 1920,
  "tts_provider": "kokoro",
  "voice": "af_bella",
  "speed": 0.9,
  "volume_multiplier": 1.2,
  "caption_font_size": 100,
  "caption_font_color": "#ff6b6b",
  "caption_shadow_color": "#000000",
  "caption_stroke_color": "#ffffff",
  "caption_position": "bottom",
  "image_effect": "ken_burns"
}
```

### Using Pre-existing Audio

```json
{
  "background_url": "https://example.com/background.jpg",
  "audio_url": "https://example.com/narration.mp3",
  "caption_font_size": 80,
  "caption_position": "center",
  "image_effect": "pan"
}
```

### Synchronous Processing (Immediate Response)

```json
{
  "background_url": "https://example.com/background.jpg",
  "text": "Quick test message",
  "width": 1080,
  "height": 1920,
  "sync": true
}
```

**Note:** Use `sync: true` for:

- Testing and development
- Short text (< 100 words)
- Immediate results needed
- Single user scenarios

**Avoid `sync: true` for:**

- Production with multiple users
- Long text content
- High traffic scenarios (causes request timeouts)

## Response Format

### Async Response (202 Accepted) - Default

When `sync: false` (default), the endpoint returns immediately with a job ID. The video generation happens asynchronously in the background.

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "TTS-captioned video job created successfully. Check job status for results."
}
```

### Sync Response (202 Accepted) - Immediate Result

When `sync: true`, the endpoint waits for processing to complete and returns the result immediately.

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "TTS-captioned video created successfully",
  "result": {
    "video_url": "https://your-bucket.nyc3.digitaloceanspaces.com/videos/tts_video_550e8400.mp4",
    "dimensions": [1080, 1920],
    "has_audio": true,
    "has_captions": true,
    "background_effect": "ken_burns"
  }
}
```

### Checking Job Status

Use the job ID to check the status and retrieve results:

```http
GET /api/v1/jobs/{job_id}
```

### Completed Job Response

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "video_url": "https://your-bucket.nyc3.digitaloceanspaces.com/videos/tts_video_550e8400.mp4",
    "dimensions": [1080, 1920],
    "has_audio": true,
    "has_captions": true,
    "background_effect": "ken_burns"
  },
  "created_at": "2025-10-14T06:19:49.115Z",
  "updated_at": "2025-10-14T06:21:15.342Z"
}
```

### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `job_id` / `id` | string | Unique identifier for tracking the job |
| `message` | string | Success message |
| `status` | string | Job status: "pending", "processing", "completed", "failed" (async only) |
| `result` | object | Complete result with video URL and metadata (sync or completed async) |
| `result.video_url` | string | URL of the generated video |
| `result.dimensions` | array | Video dimensions [width, height] |
| `result.has_audio` | boolean | Whether the video includes audio |
| `result.has_captions` | boolean | Whether the video includes captions |
| `result.background_effect` | string | Applied background effect |

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Background URL is required"
}
```

### 401 Unauthorized

```json
{
  "detail": "Invalid API key"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Failed to create video generation job"
}
```

## Common Use Cases

### 1. Social Media Content

Create engaging videos for TikTok, Instagram, or YouTube Shorts with AI narration and captions.

### 2. Educational Content

Generate tutorial videos with synchronized speech and highlighted captions.

### 3. Marketing Videos

Produce product showcases with professional voiceover and branded styling.

### 4. Personal Stories

Transform written stories into captivating videos with emotional TTS voices.

## Best Practices

### Content Optimization

- **Text Length**: Keep text concise (under 500 words) for better engagement
- **Voice Selection**: Choose voices that match your brand personality
- **Caption Timing**: Word-level captions work best for social media content

### Technical Optimization

- **Image Quality**: Use high-resolution background images (minimum 1920x1080)
- **Aspect Ratios**: 9:16 for mobile, 16:9 for desktop, 1:1 for square content
- **File Formats**: MP4 output with H.264 encoding for maximum compatibility

### Performance Tips

- **Sync vs Async**: Use `sync: true` for testing/development, `sync: false` (default) for production
- **Concurrent Jobs**: Limit to 1-2 concurrent TTS jobs to avoid memory issues
- **Voice Testing**: Test voices before production to ensure quality
- **Caption Preview**: Use shorter text for initial testing of caption styling
- **Timeout Management**: Sync requests may timeout for long text; use async for content > 200 words

## Rate Limits & Quotas

- **Concurrent Jobs**: Maximum 1 TTS-captioned video job at a time (due to Kokoro model memory constraints)
- **Queue Size**: Up to 15 jobs in queue per user
- **Processing Time**: 30-120 seconds depending on text length and complexity
- **API Rate Limits**: Standard API rate limits apply per API key

## Job Lifecycle

1. **Job Creation (202 Accepted)**: Endpoint returns immediately with `job_id`
2. **Processing**: Job is queued and processed asynchronously
3. **Status Checking**: Poll `/api/v1/jobs/{job_id}` for status updates
4. **Completion**: Video URL available in job result when status is "completed"

### Example Workflow

```bash
# 1. Create video job
curl -X POST https://your-api.com/api/v1/videos/advanced/tts-captioned-video \
  -H "x-api-key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "background_url": "https://example.com/bg.jpg",
    "text": "Your amazing content here"
  }'

# Response: {"job_id": "abc-123", "message": "..."}

# 2. Check job status (poll every 5-10 seconds)
curl https://your-api.com/api/v1/jobs/abc-123 \
  -H "x-api-key: YOUR_API_KEY"

# 3. When status is "completed", download video from result.video_url
```

## Troubleshooting

### Common Issues

**"Background URL is required"**

- Ensure you provide a valid `background_url` parameter
- Verify the URL is accessible and returns an image

**"Either text for TTS or audio_url must be provided"**

- Provide either `text` (for TTS generation) or `audio_url` (for existing audio)
- At least one is required to create the video

**"Job queue is full"**

- Wait for existing jobs to complete before submitting new ones
- Check job status to see if previous jobs have finished

**High Memory Usage / Slow Processing**

- Reduce concurrent jobs
- Use shorter text content (under 300 words recommended)
- Consider using pre-existing audio instead of TTS for longer content

**Caption Issues**

- Check caption styling parameters
- Ensure font colors have sufficient contrast with background
- Verify caption position settings don't overlap important visuals
- Use smaller font sizes for longer text

**Job Stuck in "processing"**

- Wait at least 2 minutes before considering it stuck
- Check system logs if you have access
- Contact support with the job_id

### Support

For additional help or custom requirements:

- Check job status endpoint: `/api/v1/jobs/{job_id}`
- Review related endpoints: `/api/v1/audio/generate`, `/api/v1/videos/caption`
- Contact the development team for custom implementations
