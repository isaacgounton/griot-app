# Speech Generation

The speech endpoint allows you to convert text into natural-sounding speech using multiple TTS providers, including Kokoro and Edge TTS. This endpoint supports both job-based processing and real-time streaming, with full OpenAI compatibility and enhanced features.

## Create Speech

Generate audio speech from text using the specified voice and provider. Supports both job-based processing and real-time streaming.

### Endpoint

```
POST /v1/audio/speech
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

#### Basic Example

```json
{
  "text": "This is the text that will be converted to speech.",
  "voice": "af_heart",
  "provider": "kokoro"
}
```

#### Advanced Kokoro Example

```json
{
  "text": "Hello [pause:1.0s] world! Visit https://example.com for more info.",
  "voice": "af_heart+af_bella",
  "provider": "kokoro",
  "response_format": "wav",
  "volume_multiplier": 1.5,
  "lang_code": "en",
  "return_timestamps": true,
  "normalization_options": {
    "url_normalization": true,
    "email_normalization": true,
    "phone_normalization": true,
    "unit_normalization": false,
    "replace_remaining_symbols": true
  }
}
```

#### Edge TTS Streaming Example

```json
{
  "input": "This will stream audio in real-time as it's generated.",
  "voice": "alloy",
  "provider": "edge",
  "stream": true,
  "stream_format": "audio",
  "speed": 1.2,
  "response_format": "mp3"
}
```

#### Server-Sent Events (SSE) Example

```json
{
  "text": "This will stream as JSON events with base64 audio chunks.",
  "voice": "nova",
  "provider": "edge",
  "stream": true,
  "stream_format": "sse",
  "remove_filter": false
}
```

#### OpenAI Compatibility Example

```json
{
  "input": "Alternative to text field for OpenAI compatibility",
  "voice": "af_heart",
  "model": "tts-1",
  "response_format": "mp3",
  "speed": 1.0
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| text | string | No* | Text to convert to speech (max 5000 characters). **Kokoro only**: supports pause tags like `[pause:1.5s]` |
| input | string | No* | Alternative to `text` for OpenAI compatibility. If both provided, `text` takes precedence |
| voice | string | No | Voice ID or combination. Default: `af_heart`. **Kokoro**: combinations like `af_heart+af_bella`. **Edge**: OpenAI voices (`alloy`, `ash`, `ballad`, `coral`, `echo`, `fable`, `nova`, `onyx`, `sage`, `shimmer`, `verse`) or native Edge voices |
| provider | string | No | TTS provider (`kokoro` or `edge`). Default: `kokoro` |
| response_format | string | No | Audio format. **Edge TTS**: `mp3`, `wav`, `opus`, `aac`, `flac`, `pcm`. **Kokoro**: `wav` only. Default: `mp3` |
| speed | float | No | Playback speed (0.0-2.0, **Edge TTS only**). Default: `1.0` |
| stream | boolean | No | Enable real-time streaming response (**Edge TTS only**). Default: `false` |
| stream_format | string | No | Streaming format: `audio` (raw audio) or `sse` (Server-Sent Events with JSON). Default: `audio` |
| model | string | No | TTS model (OpenAI compatibility): `tts-1`, `tts-1-hd`, `gpt-4o-mini-tts`. Default: `tts-1` |
| remove_filter | boolean | No | Skip text preprocessing (**Edge TTS only**). Default: `false` |
| volume_multiplier | float | No | Volume adjustment (0.1-3.0, **Kokoro only**). Default: `1.0` |
| lang_code | string | No | Language override (**Kokoro only**): `en`, `ja`, `zh`, `es`, `fr`, `de`, `it`, `pt`, `hi` |
| return_timestamps | boolean | No | Return word-level timestamps (**Kokoro only**). Default: `false` |
| normalization_options | object | No | Text processing options (**Kokoro only**). See below |
| voice_weights | array | No | Weights for voice combination (**Kokoro only**) |

*Either `text` or `input` must be provided

#### Normalization Options (Kokoro Only)

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| normalize | boolean | true | Enable general text normalization |
| url_normalization | boolean | true | Convert URLs to pronounceable text |
| email_normalization | boolean | true | Convert emails to pronounceable text |
| phone_normalization | boolean | true | Convert phone numbers to pronounceable text |
| unit_normalization | boolean | false | Convert units (10KB → 10 kilobytes) |
| replace_remaining_symbols | boolean | true | Replace symbols with words (&→and, %→percent) |

### Available Voices

The available voices depend on the selected provider. You can also query `/v1/audio/voices` to get the full list programmatically.

#### Kokoro TTS Voices

Kokoro voices support combinations using `+` (e.g., `af_heart+af_bella`) and weighted combinations using parentheses (e.g., `af_heart(0.7)+af_bella(0.3)`).

##### High-Quality American Female Voices (Grade A-B)

| Voice ID | Grade | Description |
|----------|-------|-------------|
| af_heart | A | Premium quality, natural |
| af_bella | A- | Warm, expressive |
| af_nicole | B- | Clear, professional |

##### Standard American Female Voices (Grade C)

| Voice ID | Grade | Description |
|----------|-------|-------------|
| af_alloy | C | Neutral, consistent |
| af_aoede | C+ | Melodic |
| af_kore | C+ | Balanced |
| af_nova | C | Steady |
| af_sarah | C+ | Friendly |

##### American Male Voices

| Voice ID | Grade | Description |
|----------|-------|-------------|
| am_michael | C+ | Professional |
| am_fenrir | C+ | Deep, strong |
| am_puck | C+ | Versatile |
| am_echo | D | Clear |
| am_eric | D | Standard |
| am_onyx | D | Deep |

##### British Voices

| Voice ID | Gender | Grade | Description |
|----------|--------|-------|-------------|
| bf_emma | Female | B- | Clear British accent |
| bf_isabella | Female | C | Standard British |
| bm_george | Male | C | Professional British |
| bm_fable | Male | C | Narrative style |
| bm_lewis | Male | D+ | Standard British |

##### International Voices

| Voice ID | Language | Gender | Grade |
|----------|----------|--------|-------|
| ff_siwis | French | Female | B- |
| jf_alpha | Japanese | Female | C+ |
| jf_gongitsune | Japanese | Female | C |
| jm_kumo | Japanese | Male | C- |
| hf_alpha | Hindi | Female | C |
| hf_beta | Hindi | Female | C |
| hm_omega | Hindi | Male | C |
| if_sara | Italian | Female | C |
| im_nicola | Italian | Male | C |
| zf_xiaobei | Chinese | Female | D |
| zf_xiaoni | Chinese | Female | D |
| zm_yunxi | Chinese | Male | D |

##### Voice Combination Examples

```json
{
  "voice": "af_heart+af_bella",          // Equal mix
  "voice": "af_heart(0.7)+af_bella(0.3)", // Weighted mix
  "voice": "af_heart+bf_emma+ff_siwis"    // Multi-voice blend
}
```

#### Edge TTS Voices

Edge TTS offers a wide range of voices across many languages. For a full list, you can query the `/v1/audio/voices?provider=edge` endpoint.

##### OpenAI-Compatible Voices (Updated)

| Voice ID | Mapped To | Language | Description |
|----------|-----------|----------|-------------|
| alloy | en-US-JennyNeural | English (US) | Clear, versatile female voice |
| ash | en-US-AndrewNeural | English (US) | Professional male voice |
| ballad | en-GB-ThomasNeural | English (UK) | Narrative British male voice |
| coral | en-AU-NatashaNeural | English (AU) | Friendly Australian female voice |
| echo | en-US-GuyNeural | English (US) | Clear male voice |
| fable | en-GB-SoniaNeural | English (UK) | Storytelling British female voice |
| nova | en-US-AriaNeural | English (US) | Natural female voice |
| onyx | en-US-EricNeural | English (US) | Deep male voice |
| sage | en-US-JennyNeural | English (US) | Wise-sounding female voice |
| shimmer | en-US-EmmaNeural | English (US) | Bright female voice |
| verse | en-US-BrianNeural | English (US) | Poetic male voice |

##### Native Edge TTS Voices (Examples)

| Voice ID | Language |
|----------|----------|
| en-US-AvaNeural | English (US) |
| en-GB-SoniaNeural | English (UK) |
| fr-FR-DeniseNeural | French |
| de-DE-AmalaNeural | German |
| es-ES-ElviraNeural | Spanish |
| ja-JP-KeitaNeural | Japanese |

### Response

#### Job-Based Response (stream=false, default)

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

#### Streaming Response (stream=true, stream_format="audio")

Returns raw audio data directly as `audio/mpeg`, `audio/wav`, etc. Can be piped to audio players:

```bash
curl -X POST /v1/audio/speech \
  -d '{"text": "Hello world", "stream": true}' | ffplay -i -
```

#### SSE Streaming Response (stream=true, stream_format="sse")

Returns Server-Sent Events with JSON data:

```
data: {"type": "speech.audio.delta", "audio": "base64-encoded-audio-chunk"}

data: {"type": "speech.audio.delta", "audio": "base64-encoded-audio-chunk"}

data: {"type": "speech.audio.done", "usage": {"input_tokens": 12, "output_tokens": 0, "total_tokens": 12}}
```

### Example

#### Basic Request (Edge TTS)

```bash
curl -X POST \
  https://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "text": "Welcome to the enhanced TTS API with streaming support.",
    "voice": "alloy",
    "provider": "edge"
  }'
```

#### Streaming Audio Request (Edge TTS)

```bash
curl -X POST \
  https://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "input": "This will stream audio in real-time as it is generated.",
    "voice": "nova",
    "provider": "edge",
    "stream": true,
    "stream_format": "audio",
    "speed": 1.2
  }' | ffplay -autoexit -nodisp -i -
```

#### SSE Streaming Request (Edge TTS)

```bash
curl -X POST \
  https://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "text": "This returns JSON events with base64 audio chunks for web applications.",
    "voice": "sage",
    "provider": "edge",
    "stream": true,
    "stream_format": "sse",
    "remove_filter": false
  }'
```

#### Advanced Kokoro Request

```bash
curl -X POST \
  https://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "text": "Hello [pause:1.0s] world! Visit https://example.com for more info.",
    "voice": "af_heart(0.7)+af_bella(0.3)",
    "provider": "kokoro",
    "response_format": "wav",
    "volume_multiplier": 1.2,
    "return_timestamps": true,
    "normalization_options": {
      "url_normalization": true,
      "replace_remaining_symbols": true
    }
  }'
```

#### OpenAI Compatible Request

```bash
curl -X POST \
  https://localhost:8000/v1/audio/speech \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "input": "Using OpenAI compatible syntax with new voices.",
    "voice": "coral",
    "model": "tts-1-hd",
    "response_format": "mp3",
    "speed": 1.5
  }'
```

#### Response

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000"
}
```

## Get Job Status

Check the status of a speech generation job.

### Endpoint

```
GET /v1/audio/speech/{job_id}
```

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | string | Yes | ID of the job to get status for |

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |

### Basic Response (Edge TTS)

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": {
    "audio_url": "https://cdn.localhost:8000/output/j-123e4567.mp3",
    "tts_engine": "edge",
    "voice": "en-US-AvaNeural",
    "response_format": "mp3",
    "speed": 1.0,
    "estimated_duration": 12.5,
    "word_count": 25
  },
  "error": null
}
```

### Enhanced Response (Kokoro TTS with Advanced Features)

```json
{
  "job_id": "j-123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": {
    "audio_url": "https://cdn.localhost:8000/output/j-123e4567.wav",
    "audio_path": "audio/j-123e4567.wav",
    "tts_engine": "kokoro",
    "voice": "af_heart+af_bella",
    "response_format": "wav",
    "speed": 1.2,
    "volume_multiplier": 1.5,
    "lang_code": "en",
    "estimated_duration": 8.7,
    "word_count": 22,
    "word_timestamps": [
      {"word": "Hello", "start": 0.0, "end": 0.5},
      {"word": "world", "start": 1.5, "end": 2.0}
    ]
  },
  "error": null
}
```

#### Status Values

| Status | Description |
|--------|-------------|
| queued | Job is in the queue waiting to be processed |
| processing | Job is currently being processed |
| completed | Job has completed successfully |
| failed | Job has failed with an error |

### Example

```bash
curl -X GET \
  https://localhost:8000/v1/audio/speech/j-123e4567-e89b-12d3-a456-426614174000 \
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

## Technical Details

### General Specifications

- **Maximum text length**: 5000 characters
- **Processing time**: 1-3 seconds per 100 characters (varies by provider)
- **Audio quality**: 128 kbps (MP3), 16-bit/24kHz (WAV)
- **Authentication**: X-API-Key header required
- **Rate limiting**: Applied per API key

### Provider-Specific Features

#### Kokoro TTS (Advanced Features)

- **Audio formats**: WAV only (high quality)
- **Sample rate**: 24 kHz, 16-bit
- **Voice combinations**: ✅ Supports mixing multiple voices (e.g., `af_heart+af_bella`)
- **Weighted combinations**: ✅ Custom weights with `af_heart(0.7)+af_bella(0.3)` syntax
- **Text processing**: ✅ Advanced normalization with configurable options
- **Pause control**: ✅ `[pause:1.5s]` tags for inserting silence
- **Volume control**: ✅ 0.1-3.0x multiplier range
- **Language override**: ✅ Explicit language code support
- **Word timestamps**: ✅ Optional word-level timing data
- **Voice grades**: ✅ A-D quality ratings for voices
- **Speed control**: ❌ Fixed speed only
- **Streaming**: ❌ Job-based processing only

#### Edge TTS (Microsoft Azure + Enhanced Features)

- **Audio formats**: ✅ MP3, WAV, OPUS, AAC, FLAC, PCM
- **Sample rate**: 24 kHz, 16-bit
- **Speed control**: ✅ 0.0-2.0x playback speed (updated range)
- **Voice selection**: ✅ 400+ voices across 140+ languages
- **OpenAI compatibility**: ✅ Full compatibility with updated OpenAI voices
- **Real-time streaming**: ✅ Raw audio and SSE streaming support
- **Streaming formats**: ✅ Raw audio (`stream_format: "audio"`) and SSE (`stream_format: "sse"`)
- **Text processing**: ✅ Enhanced Markdown cleaning and contextual processing
- **Voice combinations**: ❌ Single voice only
- **Volume control**: ❌ Not supported
- **Pause tags**: ❌ Not supported (use streaming for pauses)
- **Word timestamps**: ❌ Not supported

### Advanced Features (Kokoro Only)

#### Voice Combination System

```json
{
  "voice": "af_heart+af_bella",          // Equal 50/50 mix
  "voice": "af_heart(0.7)+af_bella(0.3)", // Weighted 70/30 mix  
  "voice": "af_heart+bf_emma+ff_siwis"   // Multi-voice blend
}
```

#### Text Normalization Options

- **URL normalization**: Converts URLs to pronounceable text
- **Email normalization**: Converts email addresses to speech
- **Phone normalization**: Handles phone number pronunciation
- **Unit normalization**: Expands units (10KB → "10 kilobytes")
- **Symbol replacement**: Converts symbols (&→"and", %→"percent")

#### Pause Tag System

- Format: `[pause:X.Xs]` where X.X is duration in seconds
- Examples: `[pause:0.5s]`, `[pause:2.0s]`, `[pause:1.25s]`
- Integrated into natural speech flow

### Streaming Capabilities (Edge TTS Only)

#### Raw Audio Streaming

- **Real-time generation**: Audio chunks streamed as they're generated
- **Low latency**: Immediate playback without waiting for complete generation
- **Pipe-friendly**: Compatible with `ffplay`, `sox`, and other audio tools
- **Format support**: All Edge TTS formats (MP3, WAV, OPUS, AAC, FLAC, PCM)

#### Server-Sent Events (SSE) Streaming

- **Web-compatible**: Perfect for browser-based applications
- **Structured events**: JSON format with event types and metadata
- **Base64 encoding**: Audio chunks encoded for web transport
- **Progress tracking**: Real-time generation progress and completion events

#### Streaming Event Types

- `speech.audio.delta`: Contains base64-encoded audio chunk
- `speech.audio.done`: Generation complete with usage statistics
- `error`: Error information if generation fails

### Performance Benchmarks

- **Kokoro TTS**: ~2-4x real-time generation speed (job-based)
- **Edge TTS**: ~1-2x real-time generation speed (job-based)
- **Edge TTS Streaming**: Near real-time with ~100-200ms first chunk latency
- **Memory usage**: 2-4GB RAM for Kokoro model loading
- **Concurrent jobs**: Up to 10 simultaneous generations
- **Streaming connections**: Up to 50 concurrent streams

### Error Handling

- **Model initialization**: Automatic retry with fallback
- **Network failures**: Graceful degradation between providers
- **Invalid voices**: Clear error messages with suggested alternatives
- **Resource limits**: Queue management for high-load scenarios
- **Streaming errors**: SSE error events for failed streams
- **Connection handling**: Automatic cleanup of interrupted streams

## Additional API Endpoints

### Models and Voices Information

#### Get Available Models

```
GET /v1/models
GET /v1/audio/models
```

Returns list of available TTS models in OpenAI-compatible format:

```json
{
  "models": [
    {"id": "tts-1"},
    {"id": "tts-1-hd"},
    {"id": "gpt-4o-mini-tts"},
    {"id": "kokoro-v1.0"}
  ]
}
```

#### Get Available Voices

```
GET /v1/audio/voices?provider=edge&language=en-US
GET /v1/voices/formatted?provider=kokoro
GET /v1/voices/all
```

Returns voice information with optional filtering by provider and language.

### Third-Party API Compatibility

#### ElevenLabs Compatibility

```
POST /v1/elevenlabs/text-to-speech/{voice_id}
```

ElevenLabs-compatible endpoint that uses Edge TTS:

```bash
curl -X POST /v1/elevenlabs/text-to-speech/en-US-JennyNeural \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{"text": "Hello from ElevenLabs compatibility mode!"}'
```

#### Azure Cognitive Services Compatibility

```
POST /v1/azure/cognitiveservices/v1
```

Accepts SSML payloads like Azure TTS:

```bash
curl -X POST /v1/azure/cognitiveservices/v1 \
  -H 'Content-Type: application/ssml+xml' \
  -H 'X-API-Key: your-api-key' \
  -d '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis">
        <voice name="en-US-JennyNeural">Hello from Azure compatibility!</voice>
      </speak>'
```

### Provider Information

```
GET /v1/audio/providers
```

Returns comprehensive information about all TTS providers:

```json
{
  "providers": ["kokoro", "edge"],
  "formats": {
    "kokoro": ["wav"],
    "edge": ["mp3", "wav", "opus", "aac", "flac", "pcm"]
  },
  "models": {
    "edge": [{"id": "tts-1"}, {"id": "tts-1-hd"}],
    "kokoro": [{"id": "kokoro-v1.0"}]
  },
  "default_provider": "kokoro"
}
```

---

## Request Validation & Error Handling

### Automatic Request Validation

All TTS requests are automatically validated for:

- **Text content**: Non-empty, within length limits
- **Provider**: Must be one of: `kokoro`, `piper`, `edge`
- **Audio format**: Must be supported by the selected provider
- **Speed**: Must be within valid range for the provider
- **Voice**: Must be available for the selected provider
- **Volume multiplier**: Must be between 0.1 and 2.0

### Request Length Limits

| Request Type | Max Characters | Description |
|--------------|----------------|-------------|
| Synchronous | 5,000 | For sync=true requests |
| Streaming | 10,000 | For stream=true requests |
| Job-based | 15,000 | For regular job requests |

### Provider Speed Ranges

| Provider | Min | Max | Default |
|----------|-----|-----|---------|
| Edge TTS | 0.25x | 2.0x | 1.0x |
| Kokoro | 0.5x | 2.0x | 1.0x |
| Piper | 0.5x | 1.5x | 1.0x |

### Provider Format Support

| Provider | Supported Formats |
|----------|------------------|
| Edge TTS | mp3, wav, opus, aac, flac, pcm |
| Kokoro | wav, mp3 |
| Piper | wav, mp3 |

### Error Response Examples

#### Invalid Speed (Out of Range)

```bash
POST /v1/audio/speech
{
  "text": "Hello",
  "provider": "edge",
  "speed": 5.0  # Out of range!
}
```

**Response** (400 Bad Request):

```json
{
  "detail": "Validation error: Speed must be between 0.25 and 2.0 for provider 'edge' (provided: 5.0)"
}
```

#### Unsupported Format

```bash
POST /v1/audio/speech
{
  "text": "Hello",
  "provider": "kokoro",
  "response_format": "mp3"  # Kokoro only supports wav!
}
```

**Response** (400 Bad Request):

```json
{
  "detail": "Validation error: Audio format 'mp3' not supported for provider 'kokoro'. Supported formats: wav"
}
```

#### Invalid Provider

```bash
POST /v1/audio/speech
{
  "text": "Hello",
  "provider": "invalid_provider"
}
```

**Response** (400 Bad Request):

```json
{
  "detail": "Validation error: Unsupported provider 'invalid_provider'. Supported providers: edge, kokoro, piper"
}
```

#### Text Too Long

```bash
POST /v1/audio/speech
{
  "text": "[very long text - 20,000 characters]",
  "stream": false
}
```

**Response** (400 Bad Request):

```json
{
  "detail": "Validation error: Text exceeds maximum length of 5000 characters for sync requests (provided: 20000 characters)"
}
```

---

## Advanced Voice Discovery

### Voice Discovery Endpoint

Discover and filter available voices using advanced criteria.

### Endpoint

```
GET /audio/voices/discover
```

### Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| provider | string | null | Filter by provider (`edge`, `kokoro`, `piper`) |
| gender | string | null | Filter by gender (`Male`, `Female`, `Neutral`) |
| language | string | null | Filter by language code (e.g., `en-US`, `fr-FR`, `ja-JP`) |
| use_case | string | null | Get recommendations for use case (see below) |
| search | string | null | Full-text search on voice names |
| limit | integer | 20 | Maximum number of results (1-100) |

### Use Case Presets

| Use Case | Description |
|----------|-------------|
| professional | Professional-sounding voices for business/formal contexts |
| casual | Friendly, casual voices for conversational content |
| energetic | Upbeat, energetic voices for engaging content |
| calm | Calm, soothing voices for relaxation/meditation |
| male | All male voices |
| female | All female voices |

### Voice Discovery Examples

#### Get Female English Voices

```bash
curl "https://localhost:8000/audio/voices/discover?gender=Female&language=en-US&limit=10"
```

Response:

```json
{
  "success": true,
  "data": {
    "total": 10,
    "limit": 10,
    "voices": {
      "edge": [
        {
          "name": "en-US-JennyNeural",
          "gender": "Female",
          "language": "en-US",
          "display_name": "Jenny"
        },
        {
          "name": "en-US-EmmaNeural",
          "gender": "Female",
          "language": "en-US",
          "display_name": "Emma"
        }
      ]
    }
  }
}
```

#### Get Professional Voices

```bash
curl "https://localhost:8000/audio/voices/discover?use_case=professional&limit=5"
```

#### Search for Voices

```bash
curl "https://localhost:8000/audio/voices/discover?search=aria&limit=10"
```

#### Get Edge TTS Voices Only

```bash
curl "https://localhost:8000/audio/voices/discover?provider=edge&limit=20"
```

#### Combine Multiple Filters

```bash
curl "https://localhost:8000/audio/voices/discover?provider=edge&gender=Male&language=en-US&limit=5"
```

---

## Audio Format Information

### Get All Audio Formats

```
GET /audio/audio-formats
```

Returns information about all supported audio formats:

```json
{
  "success": true,
  "formats": {
    "mp3": {
      "format": "mp3",
      "extension": ".mp3",
      "mime_type": "audio/mpeg",
      "alternative_mimes": ["audio/mp3"],
      "bitrate": 128,
      "browser_compatible": true,
      "ffmpeg_supported": true
    },
    "wav": {
      "format": "wav",
      "extension": ".wav",
      "mime_type": "audio/wav",
      "bitrate": 1411,
      "browser_compatible": true,
      "ffmpeg_supported": true
    },
    "opus": {
      "format": "opus",
      "extension": ".opus",
      "mime_type": "audio/ogg",
      "bitrate": 64,
      "browser_compatible": true,
      "ffmpeg_supported": true
    },
    "aac": {
      "format": "aac",
      "extension": ".aac",
      "mime_type": "audio/aac",
      "bitrate": 128,
      "browser_compatible": true,
      "ffmpeg_supported": true
    },
    "flac": {
      "format": "flac",
      "extension": ".flac",
      "mime_type": "audio/flac",
      "bitrate": 600,
      "browser_compatible": false,
      "ffmpeg_supported": true
    },
    "pcm": {
      "format": "pcm",
      "extension": ".pcm",
      "mime_type": "audio/L16",
      "browser_compatible": false,
      "ffmpeg_supported": true
    }
  },
  "compatibility_matrix": {
    "mp3": {"browser": true, "ffmpeg": true, "bitrate": 128},
    "wav": {"browser": true, "ffmpeg": true, "bitrate": 1411},
    "opus": {"browser": true, "ffmpeg": true, "bitrate": 64},
    "aac": {"browser": true, "ffmpeg": true, "bitrate": 128},
    "flac": {"browser": false, "ffmpeg": true, "bitrate": 600},
    "pcm": {"browser": false, "ffmpeg": true, "bitrate": null}
  }
}
```

### Get Specific Format Information

```
GET /audio/audio-formats/{format_name}
```

Example: Get MP3 format details

```bash
curl "https://localhost:8000/audio/audio-formats/mp3"
```

Response:

```json
{
  "success": true,
  "format": {
    "format": "mp3",
    "extension": ".mp3",
    "mime_type": "audio/mpeg",
    "alternative_mimes": ["audio/mp3"],
    "bitrate": 128,
    "browser_compatible": true,
    "ffmpeg_supported": true
  }
}
```

### Audio Format Comparison Table

| Format | MIME Type | Bitrate | Browser | FFmpeg | Use Case |
|--------|-----------|---------|---------|--------|----------|
| MP3 | audio/mpeg | 128 kbps | ✅ | ✅ | Web, general purpose |
| WAV | audio/wav | 1411 kbps | ✅ | ✅ | High quality, editing |
| Opus | audio/ogg | 64 kbps | ✅ | ✅ | Low bandwidth |
| AAC | audio/aac | 128 kbps | ✅ | ✅ | Apple devices |
| FLAC | audio/flac | 600 kbps | ❌ | ✅ | Lossless archival |
| PCM | audio/L16 | varies | ❌ | ✅ | Raw audio data |

---

## TTS Capabilities Endpoint

### Get Complete TTS Capabilities

```
GET /audio/capabilities
```

Returns comprehensive information about all TTS providers, their capabilities, and supported formats:

```json
{
  "success": true,
  "capabilities": {
    "providers": ["edge", "kokoro", "piper"],
    "formats": {
      "edge": {"mp3", "wav", "opus", "aac", "flac", "pcm"},
      "kokoro": {"wav", "mp3"},
      "piper": {"wav", "mp3"}
    },
    "speed_ranges": {
      "edge": {"min": 0.25, "max": 2.0, "default": 1.0},
      "kokoro": {"min": 0.5, "max": 2.0, "default": 1.0},
      "piper": {"min": 0.5, "max": 1.5, "default": 1.0}
    },
    "audio_formats": {
      "mp3": {...},
      "wav": {...},
      "opus": {...}
    }
  }
}
```

---

## Integration Examples

### Example 1: Using Voice Discovery in Your Application

```javascript
// Get professional female voices in English
const response = await fetch(
  'https://localhost:8000/audio/voices/discover?gender=Female&use_case=professional&language=en-US'
);
const data = await response.json();
const voices = data.data.voices;

// Use first recommended voice
const selectedVoice = voices.edge[0].name;
```

### Example 2: Checking Format Compatibility Before Request

```javascript
// Get format info
const formatResponse = await fetch('https://localhost:8000/audio/audio-formats/opus');
const formatData = await formatResponse.json();

if (formatData.format.browser_compatible) {
  // Safe to use in browser
  const ttsRequest = {
    text: "Hello world",
    response_format: "opus",
    provider: "edge"
  };
}
```

### Example 3: Handling Validation Errors Gracefully

```javascript
try {
  const response = await fetch('https://localhost:8000/v1/audio/speech', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      text: "Hello world",
      provider: "edge",
      speed: 1.5
    })
  });
  
  if (!response.ok) {
    const error = await response.json();
    console.error('Validation error:', error.detail);
    // Show user-friendly error message
  }
} catch (e) {
  console.error('Request failed:', e);
}
```

### Example 4: Getting Capabilities Before Setup

```bash
# Get all capabilities on app startup
curl "https://localhost:8000/audio/capabilities" | jq .capabilities

# Use this to:
# - Build voice selector UI
# - Validate user input
# - Show supported formats
# - Display speed ranges
```

---

## Best Practices

### ✅ Do's

1. **Validate Early**: Check capabilities endpoint on app startup
2. **Use Voice Discovery**: Let users choose from discovered voices
3. **Check Format Support**: Use format info before generating
4. **Handle Validation Errors**: Provide helpful error messages to users
5. **Cache Capabilities**: Store provider info to reduce API calls

### ❌ Don'ts

1. **Don't hardcode voice names**: Use discovery API instead
2. **Don't ignore validation errors**: They provide clear guidance
3. **Don't use unsupported format/provider combinations**: Check first
4. **Don't exceed speed limits**: Validation will reject them
5. **Don't send empty text**: Always validate before sending

---

## Troubleshooting

### "Speed out of range" error

**Problem**: Speed value exceeds provider limits
**Solution**: Use `/audio/capabilities` to check valid range for your provider

```bash
# Check valid ranges
curl "https://localhost:8000/audio/capabilities" | jq .capabilities.speed_ranges.edge
# Response: {"min": 0.25, "max": 2.0, "default": 1.0}
```

### "Format not supported" error

**Problem**: Selected format not supported by provider
**Solution**: Check supported formats for your provider

```bash
# Check what formats are supported
curl "https://localhost:8000/audio/capabilities" | jq .capabilities.formats.kokoro
# Response: ["wav", "mp3"]
```

### "No voices found" in discovery

**Problem**: Filters too restrictive
**Solution**: Broaden filters or check provider availability

```bash
# Try without filters
curl "https://localhost:8000/audio/voices/discover?provider=edge&limit=5"

# Or check specific language
curl "https://localhost:8000/audio/voices/discover?language=en-US&limit=10"
```

### Cannot determine which format to use

**Problem**: Unsure about format compatibility
**Solution**: Use format comparison table

```bash
# Get format info
curl "https://localhost:8000/audio/audio-formats"

# Recommendation for web apps: Use MP3 or WAV (browser compatible)
# Recommendation for archival: Use FLAC (lossless)
# Recommendation for low bandwidth: Use Opus (smallest file size)
```

````
