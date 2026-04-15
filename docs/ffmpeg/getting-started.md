# Getting Started with FFmpeg Compose

This guide will help you understand the basics of the FFmpeg Compose API and create your first media processing job.

## Basic Concepts

### Request Structure

Every FFmpeg Compose request has the following basic structure:

```json
{
  "id": "unique-request-identifier",
  "inputs": [/* input files */],
  "outputs": [/* output configurations */],
  "filters": [/* optional filters */],
  "stream_mappings": [/* optional stream mappings */],
  "metadata": {/* optional metadata extraction */}
}
```

### Job Processing Flow

1. **Submit Request**: POST to `/v1/ffmpeg/compose` with your configuration
2. **Get Job ID**: Receive a job ID for tracking the operation
3. **Poll Status**: Check job status using `/v1/ffmpeg/compose/{job_id}`
4. **Get Results**: When completed, retrieve output file URLs and metadata

## Your First FFmpeg Job

Let's start with a simple video conversion example:

### Example 1: Basic Video Conversion

Convert a video to H.264 with AAC audio:

```json
{
  "id": "my-first-conversion",
  "inputs": [
    {
      "file_url": "https://example.com/input.mov"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"},
        {"option": "-crf", "argument": 23}
      ]
    }
  ]
}
```

**What this does:**
- Takes one input file: `input.mov`
- Converts video to H.264 codec (`libx264`)
- Converts audio to AAC codec
- Sets video quality to CRF 23 (good quality)

### Example 2: Adding Metadata Extraction

Extract thumbnails and file information:

```json
{
  "id": "conversion-with-metadata",
  "inputs": [
    {
      "file_url": "https://example.com/input.mov"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ]
    }
  ],
  "metadata": {
    "thumbnail": true,
    "filesize": true,
    "duration": true,
    "bitrate": true,
    "encoder": true
  }
}
```

**Additional features:**
- Generates a thumbnail image
- Extracts file size, duration, bitrate, and encoder information

### Example 3: Input Options

Extract only a portion of the input video:

```json
{
  "id": "extract-segment",
  "inputs": [
    {
      "file_url": "https://example.com/long-video.mp4",
      "options": [
        {"option": "-ss", "argument": "00:01:30"},
        {"option": "-t", "argument": "00:00:30"}
      ]
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ]
    }
  ]
}
```

**What this does:**
- Starts extracting from 1 minute 30 seconds (`-ss 00:01:30`)
- Extracts 30 seconds of content (`-t 00:00:30`)
- Converts the extracted segment to H.264/AAC

## Making API Requests

### Using cURL

```bash
# Submit the job
curl -X POST "http://localhost:8000/v1/ffmpeg/compose" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d @your-config.json

# Response: {"job_id": "abc123-def456"}

# Check status
curl -X GET "http://localhost:8000/v1/ffmpeg/compose/abc123-def456" \
  -H "X-API-Key: your-api-key"
```

### Using Python

```python
import requests
import json
import time

API_BASE = "http://localhost:8000"
API_KEY = "your-api-key"
headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}

# Submit job
config = {
    "id": "python-example",
    "inputs": [{"file_url": "https://example.com/input.mp4"}],
    "outputs": [{
        "options": [
            {"option": "-c:v", "argument": "libx264"},
            {"option": "-c:a", "argument": "aac"}
        ]
    }]
}

response = requests.post(f"{API_BASE}/v1/ffmpeg/compose", 
                        headers=headers, json=config)
job_id = response.json()["job_id"]

# Poll for completion
while True:
    status_response = requests.get(f"{API_BASE}/v1/ffmpeg/compose/{job_id}", 
                                  headers=headers)
    status = status_response.json()
    
    if status["status"] == "completed":
        print("Job completed!")
        print(f"Output URL: {status['result']['outputs'][0]['file_url']}")
        break
    elif status["status"] == "failed":
        print(f"Job failed: {status.get('error', 'Unknown error')}")
        break
    else:
        print(f"Job status: {status['status']}")
        time.sleep(5)
```

## Understanding the Response

### Successful Job Response

```json
{
  "job_id": "abc123-def456",
  "status": "completed",
  "result": {
    "outputs": [
      {
        "file_url": "https://s3.amazonaws.com/bucket/ffmpeg_compose/abc123/output_0.mp4",
        "thumbnail_url": "https://s3.amazonaws.com/bucket/ffmpeg_compose/abc123/thumbnail_0.jpg",
        "filesize": 15678234,
        "duration": 30.5,
        "bitrate": 1500000,
        "encoder": "libx264"
      }
    ],
    "command": "ffmpeg -y -i input.mp4 -c:v libx264 -c:a aac output.mp4",
    "processing_time": 45.2
  }
}
```

### Job Status Values

- **`pending`**: Job is queued and waiting to start
- **`processing`**: Job is currently executing
- **`completed`**: Job finished successfully
- **`failed`**: Job failed with an error

## Common Input Formats

The API supports any format that FFmpeg can read:

**Video Formats:**
- MP4, MOV, AVI, MKV, WebM
- FLV, WMV, ASF
- And many more...

**Audio Formats:**
- MP3, WAV, FLAC, AAC
- OGG, WMA, M4A
- And many more...

**Image Formats:**
- JPG, PNG, GIF, BMP
- TIFF, WebP
- And many more...

## Common Output Codecs

**Video Codecs:**
- `libx264` - H.264 (most compatible)
- `libx265` - H.265 (better compression)
- `libvpx-vp9` - VP9 (for WebM)
- `copy` - Copy without re-encoding

**Audio Codecs:**
- `aac` - AAC (most compatible)
- `mp3` - MP3
- `libopus` - Opus (high quality)
- `copy` - Copy without re-encoding

## Next Steps

Now that you understand the basics:

1. [Input Configuration](./inputs.md) - Learn about advanced input options
2. [Output Configuration](./outputs.md) - Explore output settings and quality control
3. [Examples](./examples.md) - See more practical examples
4. [Filters](./filters.md) - Add video and audio effects

---

*Previous: [FFmpeg Compose](./README.md) | Next: [Input Configuration](./inputs.md)*