# Media Routes Documentation

This section documents all media-related endpoints provided by the Media Master API.

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| [/v1/media/transcription](./transcription.md) | POST | Create a media transcription job |
| [/v1/media/transcription/{job_id}](./transcription.md#get-job-status) | GET | Get the status of a transcription job |
| [/v1/media/metadata](./metadata.md) | POST | Extract metadata from media files |
| [/v1/media/metadata/{job_id}](./metadata.md#job-status-response) | GET | Get the status of a metadata extraction job |
| [/v1/media/download](./download.md) | POST | Download media files from URLs |
| [/v1/media/download/{job_id}](./download.md#get-job-status) | GET | Get the status of a download job |
| [/v1/media/youtube-transcripts](./youtube_transcripts.md) | POST | Get YouTube video transcripts |
| [/v1/media/youtube-transcripts/{job_id}](./youtube_transcripts.md#get-job-status) | GET | Get the status of a YouTube transcript job |

## Common Use Cases

### Media Transcription

The transcription endpoint allows you to convert audio and video content into text. This is useful for:

- Creating subtitles for videos
- Generating searchable text from audio content
- Creating accessible content for users with hearing impairments
- Extracting information from recorded meetings or interviews

### Media Metadata Extraction

The metadata endpoint analyzes media files and returns comprehensive information about their properties:

- **Video Analysis**: Resolution, codec, frame rate, bitrate
- **Audio Analysis**: Codec, sample rate, channels, bitrate
- **Duration Calculation**: Precise timing for video synchronization
- **Format Detection**: Container format and codec information
- **Quality Control**: Verify media properties before processing

### Media Download

The download endpoint fetches media files from various sources:

- Download from HTTP/HTTPS URLs
- Support for streaming media URLs
- YouTube video/audio extraction
- S3 and cloud storage integration

### YouTube Transcripts

The YouTube transcripts endpoint extracts existing captions from YouTube videos:

- Get available transcript languages
- Download subtitle files in various formats
- Automatic translation to different languages
- Direct integration with video URLs

## Supported Media Types

The Media Master API supports transcription for various media types, including:

- Audio files (MP3, WAV, M4A, AAC, FLAC)
- Video files (MP4, MOV, AVI, MKV, WebM)

## Error Handling

All media endpoints follow standard HTTP status codes:
- 200: Successful operation
- 400: Bad request (invalid parameters)
- 401: Unauthorized (invalid API key)
- 404: Resource not found
- 500: Internal server error

Detailed error messages are provided in the response body. 