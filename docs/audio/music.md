# Music Generation

The music endpoint allows you to generate music from text descriptions using Meta's MusicGen model. This powerful AI model can create music in various genres and styles based on natural language descriptions.

## Create Music Generation Job

Generate music from a text description using Meta's MusicGen model.

### Endpoint

```
POST /v1/audio/music
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |
| Content-Type | Yes | application/json |

### Request Body

```json
{
  "description": "lo-fi music with a soothing melody",
  "duration": 8,
  "model_size": "small",
  "output_format": "wav"
}
```

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| description | string | Yes | Text description of the music to generate (max 500 characters) |
| duration | integer | No | Duration of generated music in seconds (1-30, default: 8) |
| model_size | string | No | Model size to use (`small`). Default: `small` |
| output_format | string | No | Output audio format (`wav` or `mp3`). Default: `wav` |

### Response

```json
{
  "job_id": "m-123e4567-e89b-12d3-a456-426614174000"
}
```

### Example

#### Request

```bash
curl -X POST \
  https://localhost:8000/v1/audio/music \
  -H 'Content-Type: application/json' \
  -H 'X-API-Key: your-api-key' \
  -d '{
    "description": "upbeat electronic dance music with synthesizers",
    "duration": 15,
    "model_size": "small",
    "output_format": "wav"
  }'
```

#### Response

```json
{
  "job_id": "m-123e4567-e89b-12d3-a456-426614174000"
}
```

## Get Job Status

Check the status of a music generation job.

### Endpoint

```
GET /v1/audio/music/{job_id}
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
  "job_id": "m-123e4567-e89b-12d3-a456-426614174000",
  "status": "completed",
  "result": {
    "audio_url": "https://cdn.example.com/audio/music/musicgen_m-123e4567.wav",
    "duration": 14.8,
    "model_used": "facebook/musicgen-stereo-small",
    "file_size": 2547891,
    "sampling_rate": 32000
  },
  "error": null
}
```

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
  https://localhost:8000/v1/audio/music/m-123e4567-e89b-12d3-a456-426614174000 \
  -H 'X-API-Key: your-api-key'
```

## Get Endpoint Information

Get detailed information about the music generation endpoint and its capabilities.

### Endpoint

```
GET /v1/audio/music/info
```

### Headers

| Name | Required | Description |
|------|----------|-------------|
| X-API-Key | Yes | Your API key for authentication |

### Response

```json
{
  "endpoint": "/v1/audio/music",
  "method": "POST",
  "description": "Generate music from text descriptions using Meta's MusicGen Stereo model",
  "model_info": {
    "name": "Meta MusicGen Stereo",
    "type": "Text-to-audio generation",
    "supported_models": ["small"],
    "max_duration": 30,
    "supported_formats": ["wav", "mp3"]
  },
  "parameters": {
    "description": {
      "type": "string",
      "required": true,
      "max_length": 500,
      "description": "Text description of the music to generate"
    },
    "duration": {
      "type": "integer",
      "required": false,
      "default": 8,
      "min": 1,
      "max": 30,
      "description": "Duration in seconds"
    },
    "model_size": {
      "type": "string",
      "required": false,
      "default": "small",
      "options": ["small"],
      "description": "Model size to use"
    },
    "output_format": {
      "type": "string",
      "required": false,
      "default": "wav",
      "options": ["wav", "mp3"],
      "description": "Output audio format"
    }
  },
  "examples": [
    {
      "description": "lo-fi music with a soothing melody",
      "duration": 8,
      "model_size": "small"
    },
    {
      "description": "upbeat electronic dance music",
      "duration": 15,
      "model_size": "small"
    }
  ],
  "tips": [
    "Be specific in your descriptions for better results",
    "Include genre, instruments, mood, and style",
    "Longer descriptions often produce more accurate results",
    "Consider tempo keywords like 'slow', 'fast', 'upbeat'"
  ]
}
```

## Music Description Examples

### Genre-Based Descriptions

| Genre | Example Description |
|-------|---------------------|
| Lo-fi | "lo-fi hip hop with mellow beats and vinyl crackle" |
| Electronic | "upbeat electronic dance music with synthesizers and bass drops" |
| Acoustic | "acoustic guitar melody in major key with gentle strumming" |
| Classical | "orchestral music with strings and piano, romantic style" |
| Jazz | "smooth jazz with saxophone solo and walking bassline" |
| Rock | "electric guitar rock music with drums, energetic and powerful" |
| Ambient | "ambient soundscape with ethereal pads and soft textures" |
| Folk | "folk music with acoustic guitar and harmonica, storytelling mood" |

### Mood-Based Descriptions

| Mood | Example Description |
|------|---------------------|
| Relaxing | "calming music with soft piano and gentle strings, peaceful atmosphere" |
| Energetic | "high-energy music with fast tempo and driving rhythm" |
| Melancholic | "sad and contemplative music with minor chords and slow tempo" |
| Uplifting | "happy and inspiring music with bright melodies and major keys" |
| Mysterious | "dark and mysterious music with haunting melodies and atmospheric sounds" |
| Romantic | "romantic ballad with emotional melody and warm instrumentation" |

### Instrument-Specific Descriptions

| Focus | Example Description |
|-------|---------------------|
| Piano | "solo piano piece with expressive dynamics and emotional phrasing" |
| Guitar | "fingerpicked acoustic guitar with intricate melodies and harmonics" |
| Strings | "string quartet with rich harmonies and classical composition style" |
| Synthesizer | "analog synthesizer music with vintage sounds and electronic textures" |
| Drums | "percussion-focused track with complex rhythms and tribal influences" |

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Description cannot be empty"
}
```

### 401 Unauthorized

```json
{
  "detail": "Missing API Key. Please provide a valid API key in the X-API-Key header."
}
```

### 404 Not Found

```json
{
  "detail": "Job with ID m-123e4567-e89b-12d3-a456-426614174000 not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Music generation dependencies not available. Please install: transformers, torch, scipy, numpy"
}
```

## Technical Details

### Model Information
- **Model**: Meta's MusicGen Stereo (facebook/musicgen-stereo-small)
- **Type**: Text-to-audio generation using transformer architecture
- **Training**: Trained on large-scale music datasets with text descriptions
- **Capabilities**: Multi-genre stereo music generation from natural language descriptions

### Audio Specifications
- **Output Format**: WAV (primary), MP3 (secondary)
- **Sample Rate**: 32 kHz
- **Bit Depth**: 16-bit
- **Channels**: Stereo (2 channels)
- **Quality**: High-fidelity stereo audio suitable for professional use

### Processing Details
- **Duration Limits**: 1-30 seconds per generation
- **Description Length**: Maximum 500 characters
- **Processing Time**: Approximately 30-60 seconds per 10 seconds of audio
- **Memory Requirements**: Significant GPU/CPU resources required for model inference
- **Storage**: Generated files are automatically uploaded to S3-compatible storage

### Performance Considerations
- **Model Loading**: First request may take longer due to model initialization
- **Caching**: Models are cached in memory for faster subsequent generations
- **Concurrency**: Jobs are processed asynchronously in a queue system
- **Resource Usage**: Each generation requires substantial computational resources

### Dependencies
The music generation feature requires the following Python packages:
- `transformers>=4.36.0` - Hugging Face Transformers library
- `torch>=2.0.0` - PyTorch framework
- `scipy>=1.11.0` - Scientific computing library
- `numpy>=1.24.0` - Numerical computing library

If these dependencies are not installed, the endpoint will return an error message with installation instructions.

## Best Practices

### Writing Effective Descriptions
1. **Be Specific**: Include genre, instruments, mood, and tempo
2. **Use Musical Terms**: Incorporate musical terminology for better results
3. **Describe the Feel**: Mention the emotional quality or atmosphere
4. **Include Instrumentation**: Specify key instruments or sounds you want
5. **Consider Structure**: Mention if you want intro, verse, chorus elements

### Optimal Usage
- **Duration**: 8-15 seconds provides the best quality-to-processing-time ratio
- **Model Size**: Use "small" for faster generation while maintaining good quality
- **Format**: Use WAV for highest quality, MP3 for smaller file sizes
- **Descriptions**: 50-200 characters often produce the best results

### Common Pitfalls
- **Overly Complex Descriptions**: Very long descriptions may confuse the model
- **Contradictory Terms**: Avoid conflicting instructions (e.g., "fast slow music")
- **Too Vague**: Generic descriptions like "good music" produce poor results
- **Technical Overload**: Don't include too many technical music production terms