# Audio Transcriptions

The transcriptions endpoint allows you to convert audio and video content into text and subtitles using faster_whisper for enhanced performance. This endpoint provides high-accuracy transcription with 4-10x faster processing, reduced memory usage, and multiple output formats for professional use.

## Create Transcription Job

Create a job to transcribe audio or video content into text.

### Endpoint

```
POST /v1/audio/transcriptions
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

```json
{
  "media_url": "https://example.com/media/recording.mp3",
  "include_text": true,
  "include_srt": true,
  "word_timestamps": false,
  "include_segments": false,
  "language": "en",
  "max_words_per_line": 10
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| media_url | string | Yes | URL of the media file to be transcribed |
| include_text | boolean | No | Include plain text transcription in the response (default: true) |
| include_srt | boolean | No | Include SRT format subtitles in the response (default: true) |
| word_timestamps | boolean | No | Include timestamps for individual words (default: false) |
| include_segments | boolean | No | Include timestamped segments in the response (default: false) |
| language | string | No | Source language code for transcription (optional, auto-detected if not provided) |
| max_words_per_line | integer | No | Maximum words per line in SRT (1-20, default: 10) |
| beam_size | integer | No | Beam search size for enhanced accuracy (1-10, default: 5) |

### Supported Languages

The transcription service supports a wide range of languages, including but not limited to:

| Language Code | Language |
|---------------|----------|
| en | English |
| fr | French |
| de | German |
| es | Spanish |
| it | Italian |
| ja | Japanese |
| ko | Korean |
| zh | Chinese |
| ru | Russian |
| pt | Portuguese |

### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

### Example

#### Request

```bash
curl -X POST \
  https://localhost:8000/v1/audio/transcriptions \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "media_url": "https://example.com/media/interview.mp4",
    "include_text": true,
    "include_srt": true,
    "word_timestamps": true,
    "include_segments": true,
    "language": "en",
    "max_words_per_line": 8,
    "beam_size": 7
  }'
```

#### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

## Get Job Status

Check the status of a transcription job.

### Endpoint

```
GET /v1/audio/transcriptions/{job_id}
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

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": {
    "text": "This is the full text transcription of the media file. It contains all the spoken content in plain text format without timestamps or formatting.",
    "srt_url": "https://cdn.localhost:8000/output/j-123e4567.srt",
    "words": [
      {
        "word": "This",
        "start": 0.5,
        "end": 0.7,
        "confidence": 0.98
      },
      {
        "word": "is",
        "start": 0.8,
        "end": 0.9,
        "confidence": 0.99
      }
    ],
    "segments": [
      {
        "id": 0,
        "start": 0.5,
        "end": 8.2,
        "text": "This is the full text transcription of the media file.",
        "tokens": [50364, 50464, 1212, 307, 264, 1577, 2487, 35288, 295, 264, 3021, 3013, 13, 50814],
        "temperature": 0.0,
        "avg_logprob": -0.21,
        "compression_ratio": 1.42,
        "no_speech_prob": 0.003
      },
      {
        "id": 1,
        "start": 8.2,
        "end": 15.5,
        "text": "It contains all the spoken content in plain text format.",
        "tokens": [50814, 51014, 467, 8306, 439, 264, 10759, 2701, 294, 11121, 2487, 7877, 13, 51214],
        "temperature": 0.0,
        "avg_logprob": -0.18,
        "compression_ratio": 1.38,
        "no_speech_prob": 0.001
      }
    ]
  },
  "error": null
}
```

#### Result Fields

| Field | Description |
|-------|-------------|
| text | Full text transcription (included if include_text was true) |
| srt_url | URL to download the SRT subtitle file (included if include_srt was true) |
| words | Array of word objects with timestamps (included if word_timestamps was true) |
| segments | Array of segment objects with timestamps and quality metrics (included if include_segments was true) |

#### Status Values

| Status | Description |
|--------|-------------|
| pending | Job is in the queue waiting to be processed |
| processing | Job is currently being processed |
| completed | Job has completed successfully |
| failed | Job has failed with an error |

### Example

```bash
curl -X GET \
  https://localhost:8000/v1/audio/transcriptions/j-123e4567-e89b-12d3-a456-426614174000 \
  -H 'X-API-Key: your-api-key'
```

### Error Responses

#### 404 Not Found

```json
{
  "detail": "Job with ID j-123e4567-e89b-12d3-a456-426614174000 not found"
}
```

#### 401 Unauthorized

```json
{
  "detail": "Invalid API key"
}
```

## Output Format Comparison

The transcription service provides multiple output formats to suit different use cases:

### Text Output (`include_text: true`)
- **Use Case**: Simple text processing, content analysis, searchable content
- **Format**: Plain text without timestamps
- **Example**: `"This is the full text transcription of the media file."`

### SRT Subtitles (`include_srt: true`)
- **Use Case**: Video subtitles, caption files, media players
- **Format**: Standard SRT format uploaded to S3
- **Features**: Configurable words per line, proper timing
- **Example**: Standard subtitle file with timestamps

### Word Timestamps (`word_timestamps: true`)
- **Use Case**: Precise timing alignment, karaoke-style applications, detailed analysis
- **Format**: Array of word objects with individual timing
- **Example**:
```json
{
  "word": "example",
  "start": 1.2,
  "end": 1.8,
  "confidence": 0.95
}
```

### Segments (`include_segments: true`)
- **Use Case**: Speech analysis, quality assessment, content segmentation
- **Format**: Array of segment objects with comprehensive metadata
- **Features**: Quality metrics, compression ratios, speech detection
- **Example**:
```json
{
  "id": 0,
  "start": 0.0,
  "end": 5.2,
  "text": "Complete sentence or phrase",
  "avg_logprob": -0.21,
  "compression_ratio": 1.42,
  "no_speech_prob": 0.003
}
```

## Model Information

### faster_whisper Model
- **Model Used**: OpenAI Whisper "base" model via faster_whisper
- **Performance**: 4-10x faster processing with 75% less memory usage
- **Accuracy**: Enhanced with beam search and voice activity detection
- **Languages**: 99+ languages with automatic detection

### Enhanced Quality Features
- **Beam Search**: Configurable beam size (1-10) for improved accuracy
- **Voice Activity Detection**: Automatic speech detection with silence filtering
- **Optimized Processing**: Int8 quantization for faster inference
- **Quality Metrics**: Detailed segment analysis with confidence scores

## Technical Details

### Performance
- **Processing Speed**: 4-10x faster than previous implementation
- **Processing Time**: Typically 10-25% of media duration (varies by length and complexity)
- **Memory Usage**: 75% reduction - base model requires ~500MB RAM
- **Concurrent Jobs**: Improved throughput with reduced resource usage

### File Support
- **Maximum File Size**: 1 GB
- **Maximum Duration**: 4 hours
- **Audio Formats**: MP3, WAV, M4A, AAC, FLAC, OGG
- **Video Formats**: MP4, MOV, AVI, MKV, WebM
- **Input Sources**: Direct URLs, S3 URLs, most public media URLs

### Accuracy Factors
- **Audio Quality**: Clear audio produces better results
- **Background Noise**: Minimal noise improves accuracy
- **Speaker Clarity**: Clear pronunciation helps recognition
- **Language**: Some languages perform better than others
- **Technical Content**: Specialized terminology may be less accurate

### Best Practices
- **Audio Quality**: Use high-quality audio files (>16kHz sample rate)
- **File Format**: WAV or FLAC for best quality, MP3 for convenience
- **Language Setting**: Specify language if known for better accuracy
- **Segments**: Enable segments for quality analysis and debugging
- **Words Per Line**: Use 6-10 words per line for readable subtitles 