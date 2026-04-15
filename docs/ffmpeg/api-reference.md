# FFmpeg Compose API Reference

Complete API reference for the FFmpeg Compose endpoints.

## Endpoints

### POST /v1/ffmpeg/compose

Create a new FFmpeg compose job.

**Headers:**
- `X-API-Key`: Your API key (required)
- `Content-Type`: application/json

**Request Body:**

```json
{
  "id": "string",
  "inputs": [/* FFmpegInput */],
  "outputs": [/* FFmpegOutput */],
  "stream_mappings": ["string"],
  "filters": [/* FFmpegFilter */],
  "use_simple_video_filter": false,
  "use_simple_audio_filter": false,
  "global_options": [/* FFmpegOption */],
  "metadata": {/* FFmpegMetadata */},
  "webhook_url": "string"
}
```

**Response:**
```json
{
  "job_id": "string"
}
```

### GET /v1/ffmpeg/compose/{job_id}

Get the status and results of an FFmpeg compose job.

**Parameters:**
- `job_id` (path): The job ID returned from the compose endpoint

**Headers:**
- `X-API-Key`: Your API key (required)

**Response:**
```json
{
  "job_id": "string",
  "status": "pending|processing|completed|failed",
  "result": {/* FFmpegComposeResult */},
  "error": "string"
}
```

### GET /v1/ffmpeg/compose/examples

Get example configurations for common FFmpeg operations.

**Headers:**
- `X-API-Key`: Your API key (required)

**Response:**
```json
{
  "examples": {
    "video_conversion": {/* example */},
    "audio_mixing": {/* example */},
    "video_overlay": {/* example */}
  }
}
```

## Data Models

### FFmpegComposeRequest

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the request |
| `inputs` | Array[FFmpegInput] | Yes | List of input files (min: 1) |
| `outputs` | Array[FFmpegOutput] | Yes | List of output configurations (min: 1) |
| `stream_mappings` | Array[string] | No | Global stream mappings |
| `filters` | Array[FFmpegFilter] | No | List of filters to apply |
| `use_simple_video_filter` | boolean | No | Use -vf instead of complex filter graph |
| `use_simple_audio_filter` | boolean | No | Use -af instead of complex filter graph |
| `global_options` | Array[FFmpegOption] | No | Global FFmpeg options |
| `metadata` | FFmpegMetadata | No | Metadata extraction configuration |
| `webhook_url` | string | No | URL for completion notifications |

### FFmpegInput

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `file_url` | string (URL) | Yes | URL of the input file |
| `options` | Array[FFmpegOption] | No | Input-specific FFmpeg options |

### FFmpegOutput

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `options` | Array[FFmpegOption] | Yes | Output FFmpeg options |
| `stream_mappings` | Array[string] | No | Output-specific stream mappings |

### FFmpegFilter

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `filter` | string | Yes | FFmpeg filter name |
| `arguments` | Array[string] | No | Filter arguments |
| `input_labels` | Array[string] | No | Input stream labels |
| `output_label` | string | No | Output label for this filter |
| `type` | string | No | Filter type: "video" or "audio" |

### FFmpegOption

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `option` | string | Yes | FFmpeg option name (e.g., "-c:v") |
| `argument` | string/number | No | Option argument |

### FFmpegMetadata

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `thumbnail` | boolean | No | Generate thumbnail image |
| `filesize` | boolean | No | Include file size in response |
| `duration` | boolean | No | Include duration in response |
| `bitrate` | boolean | No | Include bitrate in response |
| `encoder` | boolean | No | Include encoder info in response |

### FFmpegComposeResult

| Field | Type | Description |
|-------|------|-------------|
| `outputs` | Array[FFmpegOutputResult] | List of output files and metadata |
| `command` | string | The FFmpeg command that was executed |
| `processing_time` | number | Time taken to process (seconds) |

### FFmpegOutputResult

| Field | Type | Description |
|-------|------|-------------|
| `file_url` | string (URL) | URL of the generated output file |
| `thumbnail_url` | string (URL) | URL of thumbnail (if requested) |
| `filesize` | number | File size in bytes (if requested) |
| `duration` | number | Duration in seconds (if requested) |
| `bitrate` | number | Bitrate in bps (if requested) |
| `encoder` | string | Encoder used (if requested) |

## Stream Mapping Syntax

Stream mappings use FFmpeg's stream specifier syntax:

| Syntax | Description | Example |
|--------|-------------|---------|
| `N:v:M` | M-th video stream from N-th input | `0:v:0` (first video from first input) |
| `N:a:M` | M-th audio stream from N-th input | `1:a:0` (first audio from second input) |
| `N:v` | All video streams from N-th input | `0:v` |
| `N:a` | All audio streams from N-th input | `0:a` |
| `[label]` | Output from filter with label | `[scaled]` |

## Common FFmpeg Options

### Video Options

| Option | Description | Example Values |
|--------|-------------|----------------|
| `-c:v` | Video codec | `libx264`, `libx265`, `copy` |
| `-crf` | Constant Rate Factor (quality) | `18` (high), `23` (default), `28` (lower) |
| `-b:v` | Video bitrate | `1000k`, `2M` |
| `-r` | Frame rate | `30`, `60` |
| `-s` | Resolution | `1920x1080`, `1280x720` |
| `-aspect` | Aspect ratio | `16:9`, `4:3` |

### Audio Options

| Option | Description | Example Values |
|--------|-------------|----------------|
| `-c:a` | Audio codec | `aac`, `mp3`, `copy` |
| `-b:a` | Audio bitrate | `128k`, `192k`, `320k` |
| `-ar` | Sample rate | `44100`, `48000` |
| `-ac` | Channel count | `1` (mono), `2` (stereo) |

### Global Options

| Option | Description | Example Values |
|--------|-------------|----------------|
| `-y` | Overwrite output files | (no argument) |
| `-t` | Duration | `30`, `00:01:30` |
| `-ss` | Start time | `10`, `00:02:30` |
| `-f` | Format | `mp4`, `webm`, `mp3` |

## Common Filters

### Video Filters

| Filter | Description | Arguments | Example |
|--------|-------------|-----------|---------|
| `scale` | Resize video | `width:height` | `scale=1920:1080` |
| `crop` | Crop video | `w:h:x:y` | `crop=640:480:100:50` |
| `rotate` | Rotate video | `angle` | `rotate=PI/4` |
| `hflip` | Horizontal flip | (none) | `hflip` |
| `vflip` | Vertical flip | (none) | `vflip` |
| `overlay` | Overlay video | `x:y` | `overlay=10:10` |
| `eq` | Color adjustment | `brightness:contrast:saturation` | `eq=0.1:1.2:1.3` |

### Audio Filters

| Filter | Description | Arguments | Example |
|--------|-------------|-----------|---------|
| `volume` | Adjust volume | `level` | `volume=0.5` |
| `amix` | Mix audio streams | `inputs=N` | `amix=inputs=2` |
| `aresample` | Resample audio | `sample_rate` | `aresample=44100` |
| `loudnorm` | Normalize loudness | `I:LRA:TP` | `loudnorm=I=-16:LRA=11:TP=-1.5` |
| `highpass` | High-pass filter | `frequency` | `highpass=f=200` |
| `lowpass` | Low-pass filter | `frequency` | `lowpass=f=3000` |

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 400 | Bad Request - Invalid parameters or request structure |
| 401 | Unauthorized - Invalid or missing API key |
| 404 | Not Found - Job ID not found |
| 422 | Validation Error - Request validation failed |
| 500 | Internal Server Error - Processing failed |

## Rate Limits

The API is subject to rate limiting based on your API key. If you encounter rate limit errors, implement exponential backoff in your retry logic.

## Best Practices

1. **Use Appropriate CRF Values**: 18-28 for most use cases
2. **Copy When Possible**: Use `copy` codec when re-encoding isn't needed
3. **Monitor Job Status**: Poll job status every 5-10 seconds
4. **Handle Errors Gracefully**: Implement proper error handling for failed jobs
5. **Optimize for Speed**: Use hardware acceleration when available
6. **Test Small First**: Test with short clips before processing long videos

---

*Previous: [Examples](./examples.md) | Next: [Error Handling](./error-handling.md)*