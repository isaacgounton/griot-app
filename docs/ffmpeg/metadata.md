# Metadata Extraction

The FFmpeg Compose API can extract metadata and generate thumbnails from your processed media files. This guide explains how to configure and use metadata extraction features.

## Metadata Configuration

Enable metadata extraction by adding a `metadata` section to your request:

```json
{
  "id": "metadata-example",
  "inputs": [
    {"file_url": "https://example.com/video.mp4"}
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

## Available Metadata Options

### Thumbnail Generation

Generate a thumbnail image from the video:

```json
{
  "metadata": {
    "thumbnail": true
  }
}
```

**Result:**
```json
{
  "outputs": [
    {
      "file_url": "https://s3.amazonaws.com/bucket/output_0.mp4",
      "thumbnail_url": "https://s3.amazonaws.com/bucket/thumbnail_0.jpg"
    }
  ]
}
```

### File Size

Include output file size in bytes:

```json
{
  "metadata": {
    "filesize": true
  }
}
```

**Result:**
```json
{
  "outputs": [
    {
      "file_url": "https://s3.amazonaws.com/bucket/output_0.mp4",
      "filesize": 15678234
    }
  ]
}
```

### Duration

Extract media duration in seconds:

```json
{
  "metadata": {
    "duration": true
  }
}
```

**Result:**
```json
{
  "outputs": [
    {
      "file_url": "https://s3.amazonaws.com/bucket/output_0.mp4",
      "duration": 120.5
    }
  ]
}
```

### Bitrate

Calculate average bitrate in bits per second:

```json
{
  "metadata": {
    "bitrate": true
  }
}
```

**Result:**
```json
{
  "outputs": [
    {
      "file_url": "https://s3.amazonaws.com/bucket/output_0.mp4",
      "bitrate": 1500000
    }
  ]
}
```

### Encoder Information

Include codec and encoder details:

```json
{
  "metadata": {
    "encoder": true
  }
}
```

**Result:**
```json
{
  "outputs": [
    {
      "file_url": "https://s3.amazonaws.com/bucket/output_0.mp4",
      "encoder": "libx264"
    }
  ]
}
```

## Complete Metadata Example

Request with all metadata options enabled:

```json
{
  "id": "complete-metadata",
  "inputs": [
    {"file_url": "https://example.com/source.mov"}
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 23},
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "128k"}
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

**Complete Response:**
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
        "duration": 120.5,
        "bitrate": 1500000,
        "encoder": "libx264"
      }
    ],
    "command": "ffmpeg -y -i input.mov -c:v libx264 -crf 23 -c:a aac -b:a 128k output.mp4",
    "processing_time": 45.2
  }
}
```

## Thumbnail Generation Details

### Default Thumbnail Settings

- **Format**: JPEG
- **Quality**: High quality
- **Timing**: Extracted from middle of video
- **Size**: Maintains aspect ratio

### Custom Thumbnail Timing

You can influence thumbnail timing by using input options:

```json
{
  "inputs": [
    {
      "file_url": "https://example.com/video.mp4",
      "options": [
        {"option": "-ss", "argument": "30"}
      ]
    }
  ],
  "metadata": {
    "thumbnail": true
  }
}
```

This will generate a thumbnail from the 30-second mark.

## Multiple Output Metadata

When generating multiple outputs, each gets its own metadata:

```json
{
  "id": "multi-output-metadata",
  "inputs": [
    {"file_url": "https://example.com/source.mp4"}
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 18}
      ]
    },
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 28},
        {"option": "-s", "argument": "1280x720"}
      ]
    }
  ],
  "metadata": {
    "thumbnail": true,
    "filesize": true,
    "duration": true
  }
}
```

**Response:**
```json
{
  "outputs": [
    {
      "file_url": "https://s3.amazonaws.com/bucket/output_0.mp4",
      "thumbnail_url": "https://s3.amazonaws.com/bucket/thumbnail_0.jpg",
      "filesize": 25678234,
      "duration": 120.5
    },
    {
      "file_url": "https://s3.amazonaws.com/bucket/output_1.mp4",
      "thumbnail_url": "https://s3.amazonaws.com/bucket/thumbnail_1.jpg",
      "filesize": 12345678,
      "duration": 120.5
    }
  ]
}
```

## Audio-Only Metadata

For audio-only outputs, thumbnails are not generated:

```json
{
  "outputs": [
    {
      "options": [
        {"option": "-c:a", "argument": "mp3"},
        {"option": "-vn"}
      ]
    }
  ],
  "metadata": {
    "thumbnail": true,
    "filesize": true,
    "duration": true,
    "bitrate": true
  }
}
```

**Response:**
```json
{
  "outputs": [
    {
      "file_url": "https://s3.amazonaws.com/bucket/output_0.mp3",
      "filesize": 3456789,
      "duration": 180.2,
      "bitrate": 128000
    }
  ]
}
```

## Performance Considerations

### Metadata Impact

Enabling metadata extraction adds minimal processing time:

- **Thumbnail**: +2-5 seconds
- **File size**: Instant
- **Duration**: Instant (from FFprobe)
- **Bitrate**: Instant (calculated)
- **Encoder**: Instant

### Optimization Tips

1. **Selective Metadata**: Only enable needed metadata options
2. **Thumbnail Timing**: Use `-ss` for faster thumbnail extraction
3. **Batch Processing**: Metadata extraction is done per output

## Use Cases

### Video Platforms

```json
{
  "metadata": {
    "thumbnail": true,
    "filesize": true,
    "duration": true,
    "bitrate": true
  }
}
```

Perfect for video hosting platforms that need preview images and file information.

### Media Analysis

```json
{
  "metadata": {
    "duration": true,
    "bitrate": true,
    "encoder": true
  }
}
```

Useful for analyzing media file characteristics.

### Storage Management

```json
{
  "metadata": {
    "filesize": true,
    "duration": true
  }
}
```

Essential for storage quota management and cost estimation.

### Quality Control

```json
{
  "metadata": {
    "thumbnail": true,
    "bitrate": true,
    "encoder": true
  }
}
```

Helpful for quality verification and format validation.

## Integration Examples

### Web Application

```javascript
async function processVideo(fileUrl) {
  const config = {
    id: `process-${Date.now()}`,
    inputs: [{file_url: fileUrl}],
    outputs: [{
      options: [
        {option: "-c:v", argument: "libx264"},
        {option: "-c:a", argument: "aac"}
      ]
    }],
    metadata: {
      thumbnail: true,
      filesize: true,
      duration: true
    }
  };
  
  const response = await fetch('/v1/ffmpeg/compose', {
    method: 'POST',
    headers: {
      'X-API-Key': 'your-api-key',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(config)
  });
  
  const {job_id} = await response.json();
  
  // Poll for completion
  while (true) {
    const statusResponse = await fetch(`/v1/ffmpeg/compose/${job_id}`, {
      headers: {'X-API-Key': 'your-api-key'}
    });
    const status = await statusResponse.json();
    
    if (status.status === 'completed') {
      const output = status.result.outputs[0];
      return {
        videoUrl: output.file_url,
        thumbnailUrl: output.thumbnail_url,
        fileSize: output.filesize,
        duration: output.duration
      };
    }
    
    await new Promise(resolve => setTimeout(resolve, 5000));
  }
}
```

### Python Integration

```python
import requests
import time

def process_with_metadata(file_url, api_key):
    config = {
        "id": f"process-{int(time.time())}",
        "inputs": [{"file_url": file_url}],
        "outputs": [{
            "options": [
                {"option": "-c:v", "argument": "libx264"},
                {"option": "-c:a", "argument": "aac"}
            ]
        }],
        "metadata": {
            "thumbnail": True,
            "filesize": True,
            "duration": True,
            "bitrate": True
        }
    }
    
    response = requests.post(
        "http://localhost:8000/v1/ffmpeg/compose",
        headers={"X-API-Key": api_key},
        json=config
    )
    job_id = response.json()["job_id"]
    
    while True:
        status_response = requests.get(
            f"http://localhost:8000/v1/ffmpeg/compose/{job_id}",
            headers={"X-API-Key": api_key}
        )
        status = status_response.json()
        
        if status["status"] == "completed":
            return status["result"]["outputs"][0]
        elif status["status"] == "failed":
            raise Exception(f"Job failed: {status.get('error')}")
        
        time.sleep(5)
```

## Error Handling

### Metadata Failures

If metadata extraction fails, the job continues but metadata fields are omitted:

```json
{
  "outputs": [
    {
      "file_url": "https://s3.amazonaws.com/bucket/output_0.mp4"
      // Missing metadata fields due to extraction failure
    }
  ]
}
```

### Thumbnail Failures

If thumbnail generation fails (e.g., audio-only file), the field is omitted:

```json
{
  "outputs": [
    {
      "file_url": "https://s3.amazonaws.com/bucket/output_0.mp3",
      "filesize": 3456789,
      "duration": 180.2
      // No thumbnail_url for audio files
    }
  ]
}
```

## Best Practices

1. **Enable Selectively**: Only request metadata you actually need
2. **Handle Missing Fields**: Always check if metadata fields exist in response
3. **Cache Results**: Store metadata to avoid repeated extraction
4. **Thumbnail Strategy**: Consider when thumbnails are most useful
5. **Monitor Performance**: Track metadata extraction impact on processing time

---

*Previous: [Stream Mapping](./stream-mapping.md) | Next: [Advanced Usage](./advanced.md)*