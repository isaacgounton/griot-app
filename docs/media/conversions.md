# Media Conversions

This endpoint provides a universal media conversion service using FFmpeg, supporting a wide range of audio, video, and image formats.

## Get Supported Formats

Get a comprehensive list of all supported conversion formats with codec details and quality presets.

### Endpoint

```
GET /v1/conversions/formats
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |

### Response

```json
{
  "object": "formats",
  "supported_formats": {
    "audio": {
      "mp3": {"codec": "libmp3lame", "description": "MP3 Audio"},
      "wav": {"codec": "pcm_s16le", "description": "WAV Audio"}
    },
    "video": {
      "mp4": {"codec": "libx264", "description": "MP4 Video"},
      "webm": {"codec": "libvpx-vp9", "description": "WebM Video"}
    },
    "image": {
      "jpg": {"description": "JPEG Image"},
      "png": {"description": "PNG Image"}
    }
  },
  "quality_presets": ["low", "medium", "high", "lossless"],
  "total_formats": 53
}
```

### Example

#### Request

```bash
cURL -X GET \
  https://localhost:8000/v1/conversions/formats \
  -H 'X-API-Key: your-api-key'
```

## Convert Media

Convert media files between formats using FFmpeg.

### Endpoint

```
POST /v1/conversions/
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | multipart/form-data or application/json |

### Request Body

This endpoint accepts both `multipart/form-data` and `application/json`.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | file | No* | Media file to convert (audio, video, or image) - either `file` OR `url` OR `file_data` required. |
| url | string | No* | URL of media file to convert - either `file` OR `url` OR `file_data` required. |
| file_data | string | No* | Base64-encoded file data for JSON requests - either `file` OR `url` OR `file_data` required. |
| filename | string | No | Original filename when using `file_data` (optional). |
| content_type | string | No | MIME content type when using `file_data` (optional). |
| output_format | string | Yes | Target format for conversion (e.g., `mp3`, `mp4`, `webp`). |
| quality | string | No | Quality preset for conversion (`low`, `medium`, `high`, `lossless`). Defaults to `medium`. |
| custom_options | string | No | Custom FFmpeg options (e.g., `-vf scale=1280:-1`). |

*Either `file`, `url`, or `file_data` must be provided.

### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

### Example

#### File Upload Request

```bash
cURL -X POST \
  https://localhost:8000/v1/conversions/ \
  -H 'Content-Type: multipart/form-data' \
  -H 'X-API-Key: your-api-key' \
  -F 'file=@/path/to/your/video.mp4' \
  -F 'output_format=mp3' \
  -F 'quality=high'
```

#### URL Conversion Request

```bash
cURL -X POST \
  https://localhost:8000/v1/conversions/ \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "url": "https://example.com/audio.wav",
    "output_format": "mp3",
    "quality": "medium"
  }'
```

#### JSON File Upload Request

```bash
cURL -X POST \
  https://localhost:8000/v1/conversions/ \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "file_data": "base64-encoded-file-data-here",
    "filename": "audio.wav",
    "content_type": "audio/wav",
    "output_format": "mp3",
    "quality": "high"
  }'
```

#### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

## Get Job Status

Check the status of a media conversion job.

### Endpoint

```
GET /v1/conversions/{job_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | string | Yes | ID of the job to get status for |

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |

### Response

#### Status: Processing

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "status": "processing",
  "result": null,
  "error": null
}
```

#### Status: Completed

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": {
    "file_url": "https://your-bucket.s3.your-region.amazonaws.com/conversions/converted.mp3",
    "original_format": "wav",
    "output_format": "mp3",
    "file_size_bytes": 2048576,
    "duration_seconds": 120.5,
    "processing_time_seconds": 5.2
  },
  "error": null
}
```

#### Status: Failed

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "status": "failed", 
  "result": null,
  "error": "Unsupported input format or corrupted file"
}
```

## Advanced Usage Examples

### Batch File Conversion

Convert multiple files by creating multiple jobs:

```bash
#!/bin/bash
# Batch convert multiple files to MP3
for file in *.wav; do
  echo "Converting $file..."
  cURL -X POST \
    https://localhost:8000/v1/conversions/ \
    -H 'Content-Type: multipart/form-data' \
    -H 'X-API-Key: your-api-key' \
    -F "file=@$file" \
    -F 'output_format=mp3' \
    -F 'quality=high'
done
```

### Video Processing with Custom Options

```bash
# Convert video to web-optimized MP4
cURL -X POST \
  https://localhost:8000/v1/conversions/ \
  -H 'Content-Type: multipart/form-data' \
  -H 'X-API-Key: your-api-key' \
  -F 'file=@input_video.mov' \
  -F 'output_format=mp4' \
  -F 'quality=high' \
  -F 'custom_options=-vf scale=1920:1080 -b:v 2M -b:a 128k'
```

### Image Format Conversion

```bash
# Convert PNG to WebP with compression
cURL -X POST \
  https://localhost:8000/v1/conversions/ \
  -H 'Content-Type: multipart/form-data' \
  -H 'X-API-Key: your-api-key' \
  -F 'file=@image.png' \
  -F 'output_format=webp' \
  -F 'quality=high' \
  -F 'custom_options=-q:v 80'
```

## Integration with Other Services

### Automatic Social Media Upload

Combine conversions with Postiz for social media publishing:

```bash
# 1. Convert video for social media
JOB_RESPONSE=$(cURL -s -X POST \
  https://localhost:8000/v1/conversions/ \
  -H 'Content-Type: multipart/form-data' \
  -H 'X-API-Key: your-api-key' \
  -F 'file=@long_video.mp4' \
  -F 'output_format=mp4' \
  -F 'custom_options=-t 60 -vf scale=1080:1920')

JOB_ID=$(echo $JOB_RESPONSE | jq -r '.job_id')

# 2. Wait for completion and schedule to social media
cURL -X POST \
  https://localhost:8000/api/v1/postiz/schedule-job \
  -H 'X-API-Key: your-api-key' \
  -H 'Content-Type: application/json' \
  -d "{
    \"job_id\": \"$JOB_ID\",
    \"integrations\": [\"instagram_123\"],
    \"post_type\": \"now\"
  }"
```

## Supported Conversion Matrix

### Audio Conversions

| Input | Output | Quality Options | Notes |
|-------|--------|----------------|--------|
| WAV | MP3 | low, medium, high | Most common audio conversion |
| MP3 | WAV | lossless | Useful for audio editing |
| FLAC | MP3 | low, medium, high | Lossy compression from lossless |
| OGG | MP3 | low, medium, high | Cross-format compatibility |
| M4A | WAV | lossless | Apple format to universal |

### Video Conversions

| Input | Output | Quality Options | Notes |
|-------|--------|----------------|--------|
| MOV | MP4 | low, medium, high | Apple to universal format |
| AVI | MP4 | low, medium, high | Legacy to modern format |
| MKV | MP4 | low, medium, high | Container conversion |
| MP4 | WebM | low, medium, high | Web optimization |
| Any | GIF | low, medium, high | Video to animated GIF |

### Image Conversions

| Input | Output | Quality Options | Notes |
|-------|--------|----------------|--------|
| PNG | JPG | low, medium, high | Transparency removed |
| JPG | PNG | lossless | Add transparency support |
| Any | WebP | low, medium, high | Web optimization |
| Any | AVIF | low, medium, high | Next-gen format |
| PDF | PNG | low, medium, high | Document to image |

## Error Handling

### Common Error Scenarios

**Invalid File Format:**

```json
{
  "job_id": "j-123...",
  "status": "failed",
  "error": "Input format not supported or file is corrupted"
}
```

**Processing Timeout:**

```json
{
  "job_id": "j-123...", 
  "status": "failed",
  "error": "Processing timeout - file too large or complex"
}
```

**Storage Error:**

```json
{
  "job_id": "j-123...",
  "status": "failed", 
  "error": "Failed to upload converted file to S3 storage"
}
```

### Retry Logic

Implement exponential backoff for job status polling:

```python
import time
import requests

def wait_for_completion(job_id, api_key, max_retries=30):
    for attempt in range(max_retries):
        response = requests.get(
            f'https://localhost:8000/v1/conversions/{job_id}',
            headers={'X-API-Key': api_key}
        )
        
        result = response.json()
        status = result['status']
        
        if status == 'completed':
            return result['result']['file_url']
        elif status == 'failed':
            raise Exception(f"Conversion failed: {result['error']}")
        
        # Exponential backoff: 2^attempt seconds
        wait_time = min(2 ** attempt, 60)
        time.sleep(wait_time)
    
    raise Exception("Timeout waiting for conversion to complete")
```

## Performance Tips

### File Size Limits

- **Images**: Up to 50MB
- **Audio**: Up to 500MB
- **Video**: Up to 2GB

### Optimization Recommendations

1. **Pre-processing**: Compress large files before upload when possible
2. **Format Selection**: Choose appropriate output formats for your use case
3. **Quality Settings**: Use 'medium' quality for most applications
4. **Custom Options**: Leverage FFmpeg parameters for specific optimizations
5. **Monitoring**: Track conversion times and adjust file sizes accordingly
