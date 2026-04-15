# Video Merge

The Video Merge endpoint combines video concatenation with audio overlay functionality, allowing you to merge multiple videos into a single video with optional background music or audio overlay in one operation.

## Endpoint

```
POST /v1/videos/merge
```

## Features

- ✅ **Video Concatenation**: Merge multiple videos with professional transition effects
- ✅ **Audio Overlay**: Optional background music/audio support  
- ✅ **Transition Effects**: fade, dissolve, slide, wipe, none
- ✅ **Audio Sync Modes**: replace, mix, overlay
- ✅ **Volume Control**: Separate video and audio volume levels
- ✅ **Fade Effects**: Audio fade-in/fade-out support
- ✅ **Job Queue Integration**: Async processing with status tracking

## Authentication

This endpoint requires authentication via API key in the request header:

```bash
X-API-Key: your_api_key_here
```

## Request Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `video_urls` | array | ✅ | - | List of video URLs to merge (minimum 2 required) |
| `background_audio_url` | string | ❌ | null | Optional background audio/music URL |
| `output_format` | string | ❌ | "mp4" | Output video format (mp4, webm, mov, avi, mkv) |
| `transition` | string | ❌ | "none" | Transition effect between segments |
| `transition_duration` | number | ❌ | 1.0 | Transition duration in seconds (0.1-5.0) |
| `max_segment_duration` | number | ❌ | null | Max duration per segment in seconds (0.5-300) |
| `total_duration_limit` | number | ❌ | null | Max total duration in seconds (1-3600) |
| `video_volume` | integer | ❌ | 100 | Volume level for original video tracks (0-100) |
| `audio_volume` | integer | ❌ | 20 | Volume level for background audio (0-100) |
| `sync_mode` | string | ❌ | "overlay" | Audio synchronization mode |
| `fade_in_duration` | number | ❌ | null | Audio fade-in duration in seconds (0.0-10.0) |
| `fade_out_duration` | number | ❌ | null | Audio fade-out duration in seconds (0.0-10.0) |

### Transition Effects

| Value | Description |
|-------|-------------|
| `none` | Instant cut between videos |
| `fade` | Fade in/out transitions |
| `dissolve` | Crossfade between videos |
| `slide` | Sliding transition effect |
| `wipe` | Wipe transition effect |

### Audio Sync Modes

| Value | Description |
|-------|-------------|
| `replace` | Replace original video audio completely |
| `mix` | Blend original and background audio |
| `overlay` | Layer background audio over original audio |

## Response

The endpoint returns a job ID that can be used to check the processing status:

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Job Status

Check the status of your merge job:

### Get Job Status

```
GET /v1/videos/merge/{job_id}
```

#### Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "url": "https://storage.example.com/videos/merged/merged_video.mp4",
    "path": "videos/merged/merged_video.mp4",
    "duration": 125.5,
    "segments_processed": 3,
    "has_background_audio": true
  },
  "error": null
}
```

#### Job Status Values

| Status | Description |
|--------|-------------|
| `pending` | Job is queued for processing |
| `processing` | Video merge is in progress |
| `completed` | Merge finished successfully |
| `failed` | Merge failed (check error field) |

## Examples

### Basic Video Merge

Merge videos without background audio:

```bash
curl -X POST "https://api.example.com/v1/videos/merge" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "video_urls": [
      "https://example.com/video1.mp4",
      "https://example.com/video2.mp4",
      "https://example.com/video3.mp4"
    ],
    "transition": "fade",
    "transition_duration": 1.5
  }'
```

### Video Merge with Background Music

Merge videos with background audio overlay:

```bash
curl -X POST "https://api.example.com/v1/videos/merge" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "video_urls": [
      "https://example.com/video1.mp4",
      "https://example.com/video2.mp4",
      "https://example.com/video3.mp4"
    ],
    "background_audio_url": "https://example.com/music.mp3",
    "transition": "dissolve",
    "transition_duration": 2.0,
    "sync_mode": "overlay",
    "video_volume": 80,
    "audio_volume": 30,
    "fade_in_duration": 2.0,
    "fade_out_duration": 2.0
  }'
```

### Professional Video Compilation

Create a professional video compilation with custom settings:

```bash
curl -X POST "https://api.example.com/v1/videos/merge" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your_api_key_here" \
  -d '{
    "video_urls": [
      "https://example.com/intro.mp4",
      "https://example.com/main_content.mp4",
      "https://example.com/conclusion.mp4"
    ],
    "background_audio_url": "https://example.com/background_music.mp3",
    "output_format": "mp4",
    "transition": "slide",
    "transition_duration": 1.0,
    "max_segment_duration": 60.0,
    "total_duration_limit": 300.0,
    "sync_mode": "mix",
    "video_volume": 75,
    "audio_volume": 25,
    "fade_in_duration": 3.0,
    "fade_out_duration": 3.0
  }'
```

## Error Responses

### Invalid Parameters

```json
{
  "detail": "At least 2 video URLs are required for merging"
}
```

### Unsupported Format

```json
{
  "detail": "Unsupported output format. Supported formats: mp4, webm, mov, avi, mkv"
}
```

### Invalid Transition

```json
{
  "detail": "Invalid transition effect. Supported transitions: none, fade, dissolve, slide, wipe"
}
```

### Job Processing Error

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "result": null,
  "error": "Failed to download video from URL: https://invalid-url.com/video.mp4"
}
```

## Use Cases

### Content Creation
- Merge video clips into complete stories
- Create video compilations with background music
- Combine different camera angles with soundtrack

### Social Media
- Create engaging content with smooth transitions
- Add trending music to video content
- Combine multiple clips for TikTok/Instagram Reels

### Educational Content
- Merge lesson segments with background music
- Create educational videos with smooth transitions
- Combine different video sources into courses

### Marketing & Advertising
- Create product demos with background audio
- Merge testimonial videos with music
- Combine marketing footage into campaigns

## Best Practices

### Video Quality
- Use videos with similar resolutions for best results
- Ensure consistent frame rates across input videos
- Use high-quality source videos for better output

### Audio Settings
- Keep background audio volume lower than video audio (20-40%)
- Use fade effects for smooth audio transitions
- Test different sync modes for optimal audio balance

### Performance
- Limit the number of videos to merge (recommended: ≤10)
- Use reasonable segment durations to avoid processing timeouts
- Monitor job status regularly for large merge operations

### File Management
- Use publicly accessible URLs for video/audio sources
- Ensure all source files are available during processing
- Keep source files available until job completion

## Supported Formats

### Input Video Formats
- MP4 (.mp4)
- WebM (.webm)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)

### Input Audio Formats
- MP3 (.mp3)
- WAV (.wav)
- M4A (.m4a)
- FLAC (.flac)
- AAC (.aac)
- OGG (.ogg)

### Output Video Formats
- MP4 (.mp4) - Recommended
- WebM (.webm)
- MOV (.mov)
- AVI (.avi)
- MKV (.mkv)

## Rate Limits

- Maximum 10 concurrent merge jobs per API key
- Maximum video segment duration: 300 seconds (5 minutes)
- Maximum total merged video duration: 3600 seconds (60 minutes)
- Maximum file size per video: 500MB

## Pricing

Video merge operations are billed based on:
- Total processing time (seconds of output video)
- Number of input videos processed
- Audio processing (if background audio is used)
- Transition effects complexity

See the [pricing page](../pricing.md) for detailed rates.