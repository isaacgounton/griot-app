# Audio Routes Documentation

This section documents all audio-related endpoints provided by the Media Master API following OpenAI conventions.

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/audio/speech | POST | Generate speech from text using Kokoro TTS |
| /api/v1/audio/voices | GET | Get available voices for speech generation |
| /api/v1/audio/voices/formatted | GET | Get formatted list of available voices |
| /api/v1/audio/voices/all | GET | Get all available voices with details |
| /api/v1/audio/models | GET | Get available TTS models |
| /api/v1/audio/models/formatted | GET | Get formatted list of TTS models |
| /api/v1/audio/providers | GET | Get available TTS providers |
| /api/v1/audio/tts/providers | GET | Get TTS providers information |
| /api/v1/audio/tts/{provider}/voices | GET | Get voices for specific TTS provider |
| /api/v1/audio/music | POST | Generate music from text descriptions using MusicGen |
| /api/v1/audio/music/info | GET | Get information about music generation capabilities |
| /api/v1/audio/transcriptions | POST | Transcribe audio/video content to text |
| /api/v1/audio/pollinations/audio/tts | POST | Generate speech using Pollinations AI |
| /api/v1/audio/pollinations/audio/transcribe | POST | Transcribe audio using Pollinations AI |
| /api/v1/audio/pollinations/voices | GET | Get available voices from Pollinations AI |
| /api/v1/jobs/{job_id}/status | GET | Get the status of any audio processing job |

## Common Use Cases

### Speech Generation

The speech endpoint lets you convert any text into natural-sounding speech with various voices. This is useful for:

- Adding narration to videos
- Creating audio content for podcasts
- Generating voice-overs for presentations
- Creating accessible content for users with reading difficulties

### Music Generation

The music endpoint allows you to generate original music from text descriptions using AI. This is useful for:

- Creating background music for videos and presentations
- Generating musical ideas and inspiration for composers
- Producing royalty-free music for content creation
- Creating custom soundtracks for games and applications
- Generating music for podcasts and social media content

### Audio Transcription

The transcriptions endpoint converts audio and video content into text. This is useful for:

- Creating captions for videos
- Converting meetings and interviews to text
- Making audio content searchable
- Generating subtitles for accessibility

## Error Handling

All audio endpoints follow standard HTTP status codes:

- 200: Successful operation
- 400: Bad request (invalid parameters)
- 401: Unauthorized (invalid API key)
- 404: Resource not found
- 422: Validation error (invalid input parameters)
- 429: Rate limit exceeded
- 500: Internal server error

Detailed error messages are provided in the response body for debugging and error resolution.
