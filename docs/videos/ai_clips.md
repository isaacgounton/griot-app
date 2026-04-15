# AI-Powered Video Clips

The AI-powered video clips feature allows you to extract relevant video segments using natural language queries instead of manually specifying timestamps. This powerful functionality combines transcription technology with large language models to intelligently identify and extract the most relevant parts of your videos.

## Overview

The `/clips` endpoint now supports two modes:
1. **Manual Mode**: Traditional timestamp-based clip extraction
2. **AI Mode**: Intelligent clip detection using natural language queries

## AI Mode Features

- **Smart Transcription**: Uses Whisper for accurate speech-to-text with precise timestamps
- **LLM Analysis**: Leverages OpenAI or Groq models to understand context and relevance
- **Conversation Detection**: Automatically groups related segments for better context
- **Multi-Provider Support**: Works with OpenAI GPT models or Groq Llama models

## API Usage

### AI-Powered Clip Extraction

```http
POST /clips
Content-Type: application/json
X-API-Key: your-api-key

{
  "video_url": "https://example.com/video.mp4",
  "ai_query": "Find clips discussing machine learning and AI",
  "max_clips": 3,
  "output_format": "mp4",
  "quality": "medium"
}
```

### Manual Clip Extraction (Traditional)

```http
POST /clips
Content-Type: application/json
X-API-Key: your-api-key

{
  "video_url": "https://example.com/video.mp4",
  "segments": [
    {"start": 10.5, "end": 30.0, "name": "intro"},
    {"start": 60.0, "end": 90.5, "name": "highlight"}
  ],
  "output_format": "mp4",
  "quality": "medium"
}
```

## Request Parameters

### Required Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `video_url` | string (URL) | URL of the video file to process |

### Mode-Specific Parameters

#### AI Mode
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `ai_query` | string | - | Natural language description of desired clips |
| `max_clips` | integer | 5 | Maximum number of clips to extract (1-20) |

#### Manual Mode
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `segments` | array | - | Array of segment objects with start/end times |

### Optional Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `output_format` | string | "mp4" | Output video format (mp4, webm, avi, mov, mkv) |
| `quality` | string | "medium" | Quality preset (low, medium, high) |

## AI Query Examples

### Educational Content
```json
{
  "ai_query": "Find segments explaining key concepts or tutorials",
  "max_clips": 5
}
```

### Technical Discussions
```json
{
  "ai_query": "Extract parts discussing APIs, databases, or programming",
  "max_clips": 3
}
```

### Q&A Segments
```json
{
  "ai_query": "Find question and answer sessions or interviews",
  "max_clips": 4
}
```

### Emotional Moments
```json
{
  "ai_query": "Identify funny moments or dramatic scenes",
  "max_clips": 2
}
```

## Response Format

### Success Response (202 Accepted)
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Job Status Response
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "clip_urls": [
      "https://s3.example.com/clips/ai_clip_1.mp4",
      "https://s3.example.com/clips/ai_clip_2.mp4"
    ],
    "segments_processed": 2,
    "total_duration": 45.5
  },
  "error": null
}
```

## Environment Configuration

The AI clips feature requires at least one AI provider to be configured:

### OpenAI Configuration
```bash
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o  # Optional, defaults to gpt-4o
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional for custom endpoints
```

### Groq Configuration
```bash
GROQ_API_KEY=gsk-your-groq-api-key
GROQ_MODEL=llama-3.1-70b-versatile  # Optional, defaults to llama-3.1-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1  # Optional for custom endpoints
```

## Processing Flow

1. **Video Download**: Downloads the video file locally
2. **Audio Extraction**: Extracts audio for transcription using FFmpeg
3. **Transcription**: Uses Whisper to generate timestamped transcript
4. **AI Analysis**: LLM analyzes transcript to find relevant segments
5. **Validation**: Ensures segments are within video duration and valid
6. **Clip Generation**: Extracts video clips using FFmpeg
7. **Upload**: Uploads generated clips to S3 storage
8. **Cleanup**: Removes temporary files

## Quality Settings

| Quality | CRF | Preset | Description |
|---------|-----|--------|-------------|
| `low` | 28 | fast | Smaller file size, faster processing |
| `medium` | 23 | medium | Balanced quality and size |
| `high` | 18 | slow | Best quality, larger files |

## Limitations and Considerations

### Input Limitations
- Videos must be accessible via public URL
- Maximum clip duration: 10 minutes per segment
- Query length: 3-500 characters
- Maximum clips per request: 20

### Performance Considerations
- AI analysis adds 30-60 seconds to processing time
- Transcription time depends on video length
- Longer videos may require more processing time
- LLM response time varies by provider and model

### Language Support
- Whisper supports multiple languages but defaults to English
- AI analysis is optimized for English content
- Non-English videos may have reduced accuracy

## Error Handling

### Common Error Responses

#### Invalid Parameters
```json
{
  "detail": "Either 'segments' or 'ai_query' must be provided"
}
```

#### AI Provider Unavailable
```json
{
  "detail": "No AI provider available. Please set OPENAI_API_KEY or GROQ_API_KEY environment variable."
}
```

#### Processing Failures
- Transcription failures fall back to empty results
- AI analysis failures return empty segment list
- Individual clip generation failures are logged but don't stop the job

## Best Practices

### Writing Effective AI Queries
1. **Be Specific**: "Find technical explanations" vs "Find good parts"
2. **Use Keywords**: Include relevant terms from your video content
3. **Set Appropriate Limits**: Don't request more clips than needed
4. **Consider Context**: Queries work best with conversational content

### Performance Optimization
1. **Video Length**: Shorter videos process faster
2. **Quality Settings**: Use "low" quality for testing, "high" for final output
3. **Clip Limits**: Request fewer clips for faster processing
4. **Provider Choice**: Groq is typically faster, OpenAI may be more accurate

### Content Guidelines
- Works best with speech-heavy content (podcasts, interviews, lectures)
- Limited effectiveness with music-only or silent videos
- Performance varies with audio quality and clarity
- Multiple speakers may affect segment boundary detection

## Integration Examples

### Python Client Example
```python
import requests
import time

# Create AI clips job
response = requests.post(
    "https://your-api.com/clips",
    headers={"X-API-Key": "your-api-key"},
    json={
        "video_url": "https://example.com/video.mp4",
        "ai_query": "Find the most important takeaways and conclusions",
        "max_clips": 3,
        "quality": "high"
    }
)

job_id = response.json()["job_id"]

# Poll for completion
while True:
    status_response = requests.get(
        f"https://your-api.com/clips/{job_id}",
        headers={"X-API-Key": "your-api-key"}
    )
    
    status_data = status_response.json()
    if status_data["status"] == "completed":
        clip_urls = status_data["result"]["clip_urls"]
        print(f"Generated {len(clip_urls)} clips")
        break
    elif status_data["status"] == "failed":
        print(f"Job failed: {status_data['error']}")
        break
    
    time.sleep(5)
```

### JavaScript/Node.js Example
```javascript
const axios = require('axios');

async function createAIClips(videoUrl, query, maxClips = 3) {
  try {
    // Create job
    const response = await axios.post('https://your-api.com/clips', {
      video_url: videoUrl,
      ai_query: query,
      max_clips: maxClips,
      quality: 'medium'
    }, {
      headers: { 'X-API-Key': 'your-api-key' }
    });

    const jobId = response.data.job_id;
    console.log(`Job created: ${jobId}`);

    // Poll for completion
    while (true) {
      const statusResponse = await axios.get(
        `https://your-api.com/clips/${jobId}`,
        { headers: { 'X-API-Key': 'your-api-key' } }
      );

      const status = statusResponse.data;
      
      if (status.status === 'completed') {
        console.log('Clips generated:', status.result.clip_urls);
        return status.result.clip_urls;
      } else if (status.status === 'failed') {
        throw new Error(`Job failed: ${status.error}`);
      }

      await new Promise(resolve => setTimeout(resolve, 5000));
    }
  } catch (error) {
    console.error('Error creating AI clips:', error.message);
    throw error;
  }
}

// Usage
createAIClips(
  'https://example.com/video.mp4',
  'Find clips about product features and benefits',
  4
).then(urls => {
  console.log('Generated clip URLs:', urls);
});
```

## Troubleshooting

### Common Issues

1. **No clips generated**: Check if video contains speech content
2. **AI query too broad**: Make queries more specific to your content
3. **Processing timeout**: Reduce video length or max_clips parameter
4. **Transcription failures**: Ensure audio quality is sufficient

### Debug Information

Check job status for detailed error messages:
```bash
curl -H "X-API-Key: your-key" \
  https://your-api.com/clips/{job_id}
```

### Log Analysis

Server logs include:
- Transcription word count and duration
- AI provider and model used
- Segment detection results
- Individual clip generation status

For support or feature requests, refer to the main API documentation or contact your system administrator.