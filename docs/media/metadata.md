# Media Metadata Extraction

Extract comprehensive metadata from media files including video and audio properties using FFprobe.

## Overview

The metadata extraction service analyzes media files and returns detailed information about their properties, including:
- File size and format
- Duration and bitrate
- Video properties (codec, resolution, frame rate)
- Audio properties (codec, channels, sample rate)

## Endpoint

```
POST /v1/media/metadata
GET /v1/media/metadata/{job_id}
```

## Authentication

All requests require an API key in the `X-API-Key` header.

## Request Format

### Create Metadata Extraction Job

```http
POST /v1/media/metadata
Content-Type: application/json
X-API-Key: your-api-key

{
  "media_url": "https://example.com/video.mp4"
}
```

### Request Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `media_url` | string (URL) | Yes | URL of the media file to analyze |

### Supported Media Types

- **Video**: MP4, AVI, MOV, WMV, FLV, WebM, MKV, etc.
- **Audio**: MP3, WAV, AAC, FLAC, OGG, M4A, etc.
- **Streaming**: Most HTTP/HTTPS URLs with direct media content

## Response Format

### Job Creation Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Metadata extraction job created successfully"
}
```

### Job Status Response

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "filesize": 15728640,
    "filesize_mb": 15.0,
    "duration": 30.5,
    "duration_formatted": "00:00:30.50",
    "format": "mp4",
    "overall_bitrate": 4123456,
    "overall_bitrate_mbps": 4.12,
    "has_video": true,
    "has_audio": true,
    "video_codec": "h264",
    "video_codec_long": "H.264 / AVC / MPEG-4 AVC / MPEG-4 part 10",
    "width": 1920,
    "height": 1080,
    "resolution": "1920x1080",
    "fps": 30.0,
    "video_bitrate": 3900000,
    "video_bitrate_mbps": 3.9,
    "pixel_format": "yuv420p",
    "audio_codec": "aac",
    "audio_codec_long": "AAC (Advanced Audio Coding)",
    "audio_channels": 2,
    "audio_sample_rate": 44100,
    "audio_sample_rate_khz": 44.1,
    "audio_bitrate": 128000,
    "audio_bitrate_kbps": 128
  }
}
```

## Response Properties

### Basic Properties

| Property | Type | Description |
|----------|------|-------------|
| `filesize` | integer | File size in bytes |
| `filesize_mb` | float | File size in megabytes |
| `duration` | float | Duration in seconds |
| `duration_formatted` | string | Duration in HH:MM:SS.mm format |
| `format` | string | Container format (mp4, avi, etc.) |
| `overall_bitrate` | integer | Total bitrate in bits per second |
| `overall_bitrate_mbps` | float | Total bitrate in megabits per second |
| `has_video` | boolean | Whether the file contains video |
| `has_audio` | boolean | Whether the file contains audio |

### Video Properties

| Property | Type | Description |
|----------|------|-------------|
| `video_codec` | string | Video codec (h264, h265, etc.) |
| `video_codec_long` | string | Full codec name |
| `width` | integer | Video width in pixels |
| `height` | integer | Video height in pixels |
| `resolution` | string | Video resolution (e.g., "1920x1080") |
| `fps` | float | Frame rate in frames per second |
| `video_bitrate` | integer | Video bitrate in bits per second |
| `video_bitrate_mbps` | float | Video bitrate in megabits per second |
| `pixel_format` | string | Pixel format (yuv420p, etc.) |

### Audio Properties

| Property | Type | Description |
|----------|------|-------------|
| `audio_codec` | string | Audio codec (aac, mp3, etc.) |
| `audio_codec_long` | string | Full codec name |
| `audio_channels` | integer | Number of audio channels |
| `audio_sample_rate` | integer | Sample rate in Hz |
| `audio_sample_rate_khz` | float | Sample rate in kHz |
| `audio_bitrate` | integer | Audio bitrate in bits per second |
| `audio_bitrate_kbps` | float | Audio bitrate in kilobits per second |

## Examples

### Basic Video Analysis

```bash
curl -X POST "https://api.example.com/v1/media/metadata" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "media_url": "https://example.com/sample-video.mp4"
  }'
```

### Audio File Analysis

```bash
curl -X POST "https://api.example.com/v1/media/metadata" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "media_url": "https://example.com/audio-file.mp3"
  }'
```

### Check Job Status

```bash
curl -X GET "https://api.example.com/v1/media/metadata/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your-api-key"
```

## Integration with Topic-to-Video Pipeline

The metadata service is automatically integrated with the Topic-to-Video Pipeline to provide precise audio duration calculation instead of estimations. This ensures:

- **Accurate Video Timing**: Background videos match actual audio duration
- **Perfect Caption Sync**: Captions are timed to actual audio
- **Better Quality**: No timing mismatches in generated videos

### Pipeline Usage

```python
# In Topic-to-Video Pipeline
audio_metadata = await metadata_service.get_metadata(audio_url, "pipeline_duration")
actual_duration = audio_metadata.get('duration', estimated_duration)

# Uses actual duration for:
# - Background video composition
# - Caption timing
# - Final video duration
```

## Error Handling

### Common Error Responses

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "error": "Failed to download media file: HTTP 404"
}
```

### Error Types

- **Download Errors**: Invalid URL, network issues, file not found
- **Format Errors**: Unsupported media format, corrupted file
- **Processing Errors**: FFprobe failures, system resource issues

## Performance Considerations

- **Processing Time**: Typically 1-5 seconds for most media files
- **File Size**: Supports files up to several GB
- **Concurrent Jobs**: Multiple jobs can be processed simultaneously
- **Caching**: Metadata results are cached for faster subsequent requests

## Use Cases

1. **Video Validation**: Verify media properties before processing
2. **Quality Control**: Check resolution, bitrate, and codec compliance
3. **Duration Calculation**: Get precise timing for video synchronization
4. **Format Detection**: Identify media types and properties
5. **Batch Processing**: Analyze multiple files for content management

## Related Endpoints

- [`/v1/media/transcription`](../media/transcriptions.md) - Audio transcription
- [`/v1/media/download`](../media/download.md) - Media file download
- [`/v1/ai/footage-to-video`](../ai-videos/footage-to-video-pipeline.md) - Full video generation pipeline

## Technical Details

### FFprobe Integration

The service uses FFprobe (part of FFmpeg) to extract metadata:

```bash
ffprobe -v quiet -print_format json -show_format -show_streams input.mp4
```

### Supported Protocols

- HTTP/HTTPS URLs
- S3 URLs (with proper authentication)
- Direct file URLs
- Most streaming media URLs

### Quality Assurance

- **Fallback Handling**: Graceful degradation if metadata extraction fails
- **Validation**: Input URL validation and format checking
- **Logging**: Comprehensive logging for debugging and monitoring
- **Error Recovery**: Automatic retry for transient failures