# Silence Detection

This section documents the silence detection and voice activity analysis capabilities provided by the Griot.

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| [/v1/media/silence/](#silence-detection) | POST | Create a silence detection job |
| [/v1/media/silence/{job_id}](#get-silence-job-status) | GET | Get the status of a silence detection job |
| [/v1/media/silence/analyze](#audio-analysis) | POST | Create an audio analysis job |
| [/v1/media/silence/analyze/{job_id}](#get-analysis-job-status) | GET | Get the status of an audio analysis job |

## Silence Detection

### Create Silence Detection Job

Analyzes audio or video files to detect silent segments or speech activity.

**Endpoint:** `POST /v1/media/silence/`

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com/audio.mp3",
  "noise_threshold": "-30dB",
  "min_duration": 0.5,
  "use_advanced_vad": true
}
```

**Parameters:**
- `url` (string, required): URL of the audio/video file to analyze
- `noise_threshold` (string, optional): Noise level threshold for silence detection (default: "-30dB")
- `min_duration` (number, optional): Minimum duration of silence in seconds (default: 0.5)
- `use_advanced_vad` (boolean, optional): Use advanced Voice Activity Detection (default: true)

**Response:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "pending"
}
```

### Get Silence Job Status

**Endpoint:** `GET /v1/media/silence/{job_id}`

**Headers:**
```
X-API-Key: your_api_key_here
```

**Response (Processing):**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "processing",
  "result": null,
  "error": null
}
```

**Response (Completed):**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "completed",
  "result": {
    "segments": [
      {
        "start": 0.0,
        "end": 2.5,
        "type": "speech"
      },
      {
        "start": 2.5,
        "end": 3.2,
        "type": "silence"
      },
      {
        "start": 3.2,
        "end": 8.7,
        "type": "speech"
      }
    ],
    "total_duration": 8.7,
    "speech_duration": 6.0,
    "silence_duration": 0.7,
    "speech_percentage": 68.97,
    "analysis_method": "advanced_vad"
  },
  "error": null
}
```

## Audio Analysis

### Create Audio Analysis Job

Provides comprehensive audio characteristics analysis including detailed metrics.

**Endpoint:** `POST /v1/media/silence/analyze`

**Headers:**
```
X-API-Key: your_api_key_here
Content-Type: application/json
```

**Request Body:**
```json
{
  "url": "https://example.com/audio.mp3"
}
```

**Parameters:**
- `url` (string, required): URL of the audio/video file to analyze

**Response:**
```json
{
  "job_id": "xyz789-abc123-def456",
  "status": "pending"
}
```

### Get Analysis Job Status

**Endpoint:** `GET /v1/media/silence/analyze/{job_id}`

**Headers:**
```
X-API-Key: your_api_key_here
```

**Response (Completed):**
```json
{
  "job_id": "xyz789-abc123-def456",
  "status": "completed",
  "result": {
    "duration": 8.7,
    "sample_rate": 44100,
    "channels": 2,
    "format": "mp3",
    "bitrate": 128000,
    "silence_percentage": 31.03,
    "speech_percentage": 68.97,
    "average_volume": -12.5,
    "peak_volume": -3.2,
    "dynamic_range": 9.3
  },
  "error": null
}
```

## Detection Methods

### Advanced Voice Activity Detection (VAD)

When `use_advanced_vad: true` (default):
- Uses librosa and scipy for sophisticated audio analysis
- Analyzes spectral features and energy patterns
- Provides more accurate speech/silence boundaries
- Better performance with noisy audio
- Returns speech segments with precise timing

**Features:**
- Spectral centroid analysis
- Energy-based detection with adaptive thresholds
- Noise-robust processing
- High precision segment boundaries

### Legacy FFmpeg Detection

When `use_advanced_vad: false`:
- Uses FFmpeg's `silencedetect` filter
- Simple threshold-based detection
- Faster processing for basic use cases
- Returns silence intervals only

**FFmpeg Filter Used:**
```
silencedetect=noise={noise_threshold}:d={min_duration}
```

## Supported Media Types

Both silence detection and audio analysis support:

**Audio Formats:**
- MP3, WAV, M4A, AAC, FLAC, OGG

**Video Formats:**
- MP4, MOV, AVI, MKV, WebM, FLV

**Sources:**
- Direct file URLs
- YouTube videos (audio extraction)
- S3 and cloud storage
- Streaming media URLs

## Use Cases

### Silence Detection
- **Video Editing**: Identify natural cut points for seamless transitions
- **Podcast Processing**: Remove dead air and long pauses automatically
- **Meeting Analysis**: Find speaking segments and participation patterns
- **Content Quality**: Assess audio engagement and flow
- **Accessibility**: Generate accurate timestamps for screen readers
- **Transcription Optimization**: Pre-segment audio for better accuracy

### Audio Analysis
- **Quality Control**: Verify audio levels and format specifications
- **Content Optimization**: Analyze speech-to-silence ratio for engagement
- **Transcription Prep**: Identify processable segments before transcription
- **Audio Validation**: Confirm file integrity and format compliance
- **Metadata Generation**: Extract comprehensive audio characteristics
- **Broadcasting**: Ensure audio meets broadcast standards

## Error Handling

All endpoints follow standard HTTP status codes:
- `200`: Successful operation
- `400`: Bad request (invalid parameters)
- `401`: Unauthorized (invalid API key)
- `404`: Resource not found
- `422`: Validation error
- `500`: Internal server error

**Common Error Responses:**

**Invalid URL:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "failed",
  "result": null,
  "error": "Failed to download media from URL"
}
```

**Unsupported Format:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "failed",
  "result": null,
  "error": "Unsupported media format"
}
```

**Processing Error:**
```json
{
  "job_id": "abc123-def456-ghi789",
  "status": "failed",
  "result": null,
  "error": "Audio analysis failed: insufficient audio data"
}
```

## Technical Implementation

### Architecture
- **Job Queue System**: Asynchronous processing with UUID-based job tracking
- **FFmpeg Integration**: Advanced audio processing and filter capabilities
- **S3 Storage**: Secure file handling and temporary storage
- **Redis Caching**: Efficient job status management and data persistence

### Dependencies
- **librosa**: Advanced audio analysis and feature extraction (optional)
- **scipy**: Signal processing algorithms for Voice Activity Detection
- **FFmpeg**: Core audio processing engine with extensive filter support
- **Whisper**: Underlying audio processing utilities and transcription support

### Performance Considerations
- **Advanced VAD**: Slower processing but significantly more accurate results
- **Legacy Detection**: Faster processing suitable for simple threshold-based detection
- **File Size**: Processing time scales with audio duration and complexity
- **Concurrent Jobs**: Multiple jobs processed simultaneously for optimal throughput
- **Memory Usage**: Advanced VAD requires more memory for spectral analysis

## Examples

### Python Example
```python
import requests
import time

# Create silence detection job with advanced VAD
response = requests.post(
    "http://localhost:8000/v1/media/silence/",
    headers={"X-API-Key": "your-api-key"},
    json={
        "url": "https://example.com/podcast-episode.mp3",
        "use_advanced_vad": True,
        "min_duration": 0.3,
        "noise_threshold": "-35dB"
    }
)

job_id = response.json()["job_id"]
print(f"Started silence detection job: {job_id}")

# Poll for results
while True:
    status_response = requests.get(
        f"http://localhost:8000/v1/media/silence/{job_id}",
        headers={"X-API-Key": "your-api-key"}
    )
    
    status_data = status_response.json()
    
    if status_data["status"] == "completed":
        result = status_data["result"]
        segments = result["segments"]
        
        print(f"Analysis complete!")
        print(f"Total duration: {result['total_duration']:.2f}s")
        print(f"Speech: {result['speech_percentage']:.1f}%")
        print(f"Silence: {100 - result['speech_percentage']:.1f}%")
        print(f"Found {len(segments)} segments")
        
        # Print first few segments
        for i, segment in enumerate(segments[:5]):
            print(f"  {i+1}. {segment['start']:.2f}s - {segment['end']:.2f}s: {segment['type']}")
        
        break
    elif status_data["status"] == "failed":
        print(f"Job failed: {status_data['error']}")
        break
    
    print("Processing...")
    time.sleep(2)
```

### JavaScript Example
```javascript
// Create silence detection job
async function detectSilence(audioUrl) {
    const response = await fetch('http://localhost:8000/v1/media/silence/', {
        method: 'POST',
        headers: {
            'X-API-Key': 'your-api-key',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            url: audioUrl,
            use_advanced_vad: true,
            min_duration: 0.5
        })
    });
    
    const { job_id } = await response.json();
    
    // Poll for completion
    while (true) {
        const statusResponse = await fetch(
            `http://localhost:8000/v1/media/silence/${job_id}`,
            {
                headers: { 'X-API-Key': 'your-api-key' }
            }
        );
        
        const statusData = await statusResponse.json();
        
        if (statusData.status === 'completed') {
            return statusData.result;
        } else if (statusData.status === 'failed') {
            throw new Error(statusData.error);
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

// Usage
detectSilence('https://example.com/audio.mp3')
    .then(result => {
        console.log('Silence detection complete:', result);
    })
    .catch(error => {
        console.error('Error:', error);
    });
```

### cURL Example
```bash
# Create silence detection job
curl -X POST "http://localhost:8000/v1/media/silence/" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/meeting-recording.wav",
    "noise_threshold": "-35dB",
    "min_duration": 0.5,
    "use_advanced_vad": true
  }'

# Response: {"job_id": "abc123-def456-ghi789", "status": "pending"}

# Get job status
curl -X GET "http://localhost:8000/v1/media/silence/abc123-def456-ghi789" \
  -H "X-API-Key: your-api-key"

# Create audio analysis job
curl -X POST "http://localhost:8000/v1/media/silence/analyze" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com/audio-sample.mp3"
  }'
```

## Best Practices

### Parameter Selection
- **Advanced VAD**: Use for high-quality analysis, especially with noisy audio
- **Legacy Detection**: Use for quick processing of clean audio
- **Noise Threshold**: Start with -30dB, adjust based on audio quality
- **Min Duration**: Use 0.3-0.5s for speech, 1-2s for music detection

### Performance Optimization
- **Batch Processing**: Submit multiple jobs for bulk analysis
- **File Format**: Use compressed formats (MP3, AAC) for faster upload
- **Duration Limits**: Consider splitting very long files (>1 hour)
- **Caching**: Results are cached for repeated requests

### Integration Tips
- **Polling Interval**: Use 1-2 second intervals for status checking
- **Error Handling**: Implement retry logic for network failures
- **Result Storage**: Download and store results locally if needed repeatedly
- **Rate Limiting**: Respect API rate limits for production usage