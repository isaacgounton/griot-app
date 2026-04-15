# YouTube Shorts API Reference

## Base URL
```
https://your-api-domain.com/v1/yt-shorts
```

## Authentication
All endpoints require authentication via API key in the header:
```http
X-API-Key: your_api_key_here
```

## Endpoints

### 1. Create YouTube Shorts Job

**Endpoint**: `POST /v1/yt-shorts/`

**Description**: Create a comprehensive YouTube Shorts generation job with all advanced features.

#### Request Body

```json
{
  "video_url": "https://www.youtube.com/watch?v=example",
  "max_duration": 60,
  "quality": "high",
  "output_format": "mp4",
  "use_ai_highlight": true,
  "crop_to_vertical": true,
  "speaker_tracking": true,
  "custom_start_time": null,
  "custom_end_time": null,
  "enhance_audio": true,
  "smooth_transitions": true,
  "create_thumbnail": true,
  "target_resolution": "720x1280",
  "audio_enhancement_level": "speech",
  "face_tracking_sensitivity": "medium"
}
```

#### Parameters

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `video_url` | string | ✅ | - | YouTube video URL to process |
| `max_duration` | integer | ❌ | 60 | Maximum duration in seconds (5-300) |
| `quality` | string | ❌ | "high" | Quality preset: "low", "medium", "high", "ultra" |
| `output_format` | string | ❌ | "mp4" | Output format: "mp4", "webm", "mov" |
| `use_ai_highlight` | boolean | ❌ | true | Use AI to detect best highlight segment |
| `crop_to_vertical` | boolean | ❌ | true | Crop to vertical 9:16 format |
| `speaker_tracking` | boolean | ❌ | true | Enable advanced speaker tracking |
| `custom_start_time` | float | ❌ | null | Custom start time in seconds |
| `custom_end_time` | float | ❌ | null | Custom end time in seconds |
| `enhance_audio` | boolean | ❌ | true | Apply audio enhancement |
| `smooth_transitions` | boolean | ❌ | true | Add fade transitions |
| `create_thumbnail` | boolean | ❌ | true | Generate preview thumbnail |
| `target_resolution` | string | ❌ | "720x1280" | Target resolution (WxH) |
| `audio_enhancement_level` | string | ❌ | "speech" | Enhancement type: "speech", "music", "auto" |
| `face_tracking_sensitivity` | string | ❌ | "medium" | Sensitivity: "low", "medium", "high" |

#### Response

**Status**: `202 Accepted`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

#### Error Responses

**400 Bad Request**
```json
{
  "detail": "Invalid YouTube URL format"
}
```

**500 Internal Server Error**
```json
{
  "detail": "Failed to create YouTube Shorts job"
}
```

### 2. Get Job Status

**Endpoint**: `GET /v1/yt-shorts/{job_id}`

**Description**: Get the status and results of a YouTube Shorts generation job.

#### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `job_id` | string | ✅ | Job ID returned from create job |

#### Response

**Status**: `200 OK`

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "url": "https://s3.amazonaws.com/bucket/videos/yt-shorts/shorts_550e8400.mp4",
    "path": "videos/yt-shorts/shorts_550e8400.mp4",
    "duration": 58.5,
    "original_title": "Amazing YouTube Video Title",
    "original_duration": 1245.0,
    "highlight_start": 120.5,
    "highlight_end": 179.0,
    "is_vertical": true,
    "ai_generated": true,
    "quality": "high",
    "thumbnail_url": "https://s3.amazonaws.com/bucket/videos/yt-shorts/thumbnails/thumb_550e8400.jpg",
    "processing_stats": {
      "download_size": 52428800,
      "audio_extracted": true,
      "transcription_segments": 45,
      "ai_highlight_detected": true,
      "highlight_extracted": true,
      "dynamic_crop_applied": true,
      "optimized_for_shorts": true,
      "thumbnail_created": true,
      "uploaded_to_s3": true
    },
    "quality_check": {
      "file_size": 15728640,
      "duration": 58.5,
      "resolution": "720x1280",
      "bitrate": 2500000,
      "av_sync": true,
      "has_audio": true,
      "has_video": true
    },
    "features_used": {
      "speaker_tracking": true,
      "audio_enhancement": true,
      "smooth_transitions": true,
      "dynamic_cropping": true
    }
  },
  "error": null
}
```

#### Job Status Values

| Status | Description |
|--------|-------------|
| `pending` | Job is queued for processing |
| `processing` | Job is currently being processed |
| `completed` | Job completed successfully |
| `failed` | Job failed due to an error |

#### Error Responses

**404 Not Found**
```json
{
  "detail": "Job not found: 550e8400-e29b-41d4-a716-446655440000"
}
```

### 3. Get Endpoint Information

**Endpoint**: `GET /v1/yt-shorts/`

**Description**: Get comprehensive information about the YouTube Shorts generation endpoint.

#### Response

**Status**: `200 OK`

```json
{
  "endpoint": "/v1/yt-shorts",
  "method": "POST",
  "description": "Comprehensive AI-powered YouTube Shorts generation with all advanced features",
  "version": "2.0",
  "advanced_features": [
    "🎯 AI-powered highlight detection using GPT-4",
    "🔊 Voice Activity Detection (VAD) for precise speaker identification",
    "👤 DNN-based face detection with confidence scoring",
    "🎭 Audio-visual correlation for active speaker detection",
    "📱 Dynamic face-following crop with smooth transitions",
    "🎨 Professional video optimization for YouTube Shorts",
    "🔈 Advanced audio enhancement and speech optimization",
    "⚡ Real-time processing with quality verification",
    "🖼️ Automatic thumbnail generation",
    "📊 Comprehensive processing statistics and analytics"
  ],
  "supported_platforms": [
    "YouTube Shorts",
    "TikTok",
    "Instagram Reels",
    "Facebook Reels",
    "Snapchat Spotlight",
    "Pinterest Idea Pins"
  ],
  "technical_specifications": {
    "max_input_duration": "No limit (will be processed in segments)",
    "output_resolutions": ["720x1280", "1080x1920", "480x854"],
    "supported_qualities": ["low", "medium", "high", "ultra"],
    "audio_sample_rates": ["16kHz", "44.1kHz", "48kHz", "96kHz"],
    "video_codecs": ["H.264", "H.265 (HEVC)"],
    "audio_codecs": ["AAC", "MP3", "WAV"]
  },
  "examples": [
    {
      "name": "Basic AI-Powered Short",
      "description": "Standard YouTube Shorts generation with AI highlight detection",
      "request": {
        "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "max_duration": 60,
        "quality": "high",
        "use_ai_highlight": true,
        "crop_to_vertical": true
      }
    }
  ]
}
```

### 4. Analyze Video (Beta)

**Endpoint**: `POST /v1/yt-shorts/analyze`

**Description**: Analyze a YouTube video to provide insights for shorts generation.

#### Request Body

```json
{
  "video_url": "https://www.youtube.com/watch?v=example"
}
```

#### Response

**Status**: `200 OK`

```json
{
  "video_url": "https://www.youtube.com/watch?v=example",
  "analysis": {
    "duration": "12:34",
    "speaker_count": 2,
    "face_detection_confidence": 0.85,
    "audio_quality": "good",
    "recommended_segments": [
      {
        "start": 45,
        "end": 105,
        "reason": "High engagement, clear speaker"
      },
      {
        "start": 234,
        "end": 289,
        "reason": "Emotional peak, good audio"
      }
    ],
    "optimization_suggestions": [
      "Enable speaker tracking for better cropping",
      "Use audio enhancement for clarity",
      "Consider 45-60 second segments for optimal engagement"
    ]
  }
}
```

## Code Examples

### Python (requests)

```python
import requests
import time

# Configuration
API_KEY = "your_api_key_here"
BASE_URL = "https://your-api-domain.com/v1/yt-shorts"

headers = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

# Create job
create_data = {
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "max_duration": 60,
    "quality": "high",
    "speaker_tracking": True,
    "enhance_audio": True
}

response = requests.post(f"{BASE_URL}/", json=create_data, headers=headers)
job_id = response.json()["job_id"]

# Poll for completion
while True:
    response = requests.get(f"{BASE_URL}/{job_id}", headers=headers)
    job_data = response.json()
    
    if job_data["status"] == "completed":
        print(f"Video URL: {job_data['result']['url']}")
        print(f"Thumbnail: {job_data['result']['thumbnail_url']}")
        break
    elif job_data["status"] == "failed":
        print(f"Job failed: {job_data['error']}")
        break
    
    time.sleep(10)  # Wait 10 seconds before checking again
```

### JavaScript (fetch)

```javascript
const API_KEY = 'your_api_key_here';
const BASE_URL = 'https://your-api-domain.com/v1/yt-shorts';

const headers = {
    'X-API-Key': API_KEY,
    'Content-Type': 'application/json'
};

// Create job
const createJob = async () => {
    const response = await fetch(`${BASE_URL}/`, {
        method: 'POST',
        headers: headers,
        body: JSON.stringify({
            video_url: 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            max_duration: 60,
            quality: 'high',
            speaker_tracking: true,
            enhance_audio: true
        })
    });
    
    const data = await response.json();
    return data.job_id;
};

// Poll for completion
const pollJob = async (jobId) => {
    while (true) {
        const response = await fetch(`${BASE_URL}/${jobId}`, {
            headers: headers
        });
        
        const jobData = await response.json();
        
        if (jobData.status === 'completed') {
            console.log('Video URL:', jobData.result.url);
            console.log('Thumbnail:', jobData.result.thumbnail_url);
            break;
        } else if (jobData.status === 'failed') {
            console.error('Job failed:', jobData.error);
            break;
        }
        
        await new Promise(resolve => setTimeout(resolve, 10000)); // Wait 10 seconds
    }
};

// Usage
(async () => {
    const jobId = await createJob();
    await pollJob(jobId);
})();
```

### cURL

```bash
# Create job
curl -X POST "https://your-api-domain.com/v1/yt-shorts/" \
  -H "X-API-Key: your_api_key_here" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "max_duration": 60,
    "quality": "high",
    "speaker_tracking": true,
    "enhance_audio": true
  }'

# Check job status
curl -X GET "https://your-api-domain.com/v1/yt-shorts/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key_here"
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- **60 requests per minute** per API key
- **5 concurrent jobs** per API key
- **Rate limit headers** included in responses:
  - `X-RateLimit-Limit`: Total requests allowed per window
  - `X-RateLimit-Remaining`: Remaining requests in current window
  - `X-RateLimit-Reset`: Time when rate limit resets

## Error Handling

### HTTP Status Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 202 | Accepted (job created) |
| 400 | Bad Request (invalid parameters) |
| 401 | Unauthorized (invalid API key) |
| 404 | Not Found (job not found) |
| 429 | Too Many Requests (rate limited) |
| 500 | Internal Server Error |

### Error Response Format

```json
{
  "detail": "Error description",
  "error_code": "SPECIFIC_ERROR_CODE",
  "timestamp": "2023-12-07T10:30:00Z"
}
```

## Webhooks (Coming Soon)

Future versions will support webhook notifications for job completion:

```json
{
  "webhook_url": "https://your-domain.com/webhook",
  "events": ["job.completed", "job.failed"]
}
```

## SDK Libraries (Coming Soon)

Official SDKs will be available for:
- Python
- JavaScript/Node.js
- PHP
- Java
- Go

---

*For more examples and detailed tutorials, see the [Examples](examples.md) documentation.*