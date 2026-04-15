# Input Configuration

This guide explains how to configure input files for FFmpeg Compose operations, including input options, supported formats, and advanced input handling.

## Basic Input Structure

Each input is defined with a URL and optional FFmpeg options:

```json
{
  "file_url": "https://example.com/video.mp4",
  "options": [
    {"option": "-ss", "argument": "10"},
    {"option": "-t", "argument": "30"}
  ]
}
```

## Supported Input Sources

### Direct File URLs

```json
{
  "file_url": "https://example.com/video.mp4"
}
```

### S3 URLs

Files stored in S3-compatible storage:

```json
{
  "file_url": "https://s3.amazonaws.com/bucket/video.mp4"
}
```

### DigitalOcean Spaces

```json
{
  "file_url": "https://bucket.nyc3.digitaloceanspaces.com/video.mp4"
}
```

### Local Files (if already uploaded)

```json
{
  "file_url": "/path/to/local/file.mp4"
}
```

## Common Input Options

### Time-based Options

#### Start Time (`-ss`)

Extract video starting from a specific time:

```json
{
  "file_url": "https://example.com/long-video.mp4",
  "options": [
    {"option": "-ss", "argument": "00:02:30"}
  ]
}
```

Time formats:
- Seconds: `90` (90 seconds)
- MM:SS: `02:30` (2 minutes 30 seconds)
- HH:MM:SS: `01:02:30` (1 hour 2 minutes 30 seconds)

#### Duration (`-t`)

Limit the duration of input:

```json
{
  "file_url": "https://example.com/video.mp4",
  "options": [
    {"option": "-ss", "argument": "30"},
    {"option": "-t", "argument": "60"}
  ]
}
```

#### End Time (`-to`)

Extract until a specific time:

```json
{
  "file_url": "https://example.com/video.mp4",
  "options": [
    {"option": "-ss", "argument": "10"},
    {"option": "-to", "argument": "70"}
  ]
}
```

### Format Options

#### Force Input Format (`-f`)

Specify the input format explicitly:

```json
{
  "file_url": "https://example.com/file.raw",
  "options": [
    {"option": "-f", "argument": "rawvideo"}
  ]
}
```

#### Frame Rate (`-r`)

Set input frame rate:

```json
{
  "file_url": "https://example.com/images%d.jpg",
  "options": [
    {"option": "-r", "argument": "25"}
  ]
}
```

### Video Options

#### Resolution (`-s`)

Set input resolution (for raw video):

```json
{
  "file_url": "https://example.com/raw-video.yuv",
  "options": [
    {"option": "-f", "argument": "rawvideo"},
    {"option": "-s", "argument": "1920x1080"}
  ]
}
```

#### Pixel Format (`-pix_fmt`)

Set pixel format for raw video:

```json
{
  "file_url": "https://example.com/raw-video.yuv",
  "options": [
    {"option": "-f", "argument": "rawvideo"},
    {"option": "-pix_fmt", "argument": "yuv420p"}
  ]
}
```

### Audio Options

#### Sample Rate (`-ar`)

Set audio sample rate:

```json
{
  "file_url": "https://example.com/audio.raw",
  "options": [
    {"option": "-f", "argument": "s16le"},
    {"option": "-ar", "argument": "44100"}
  ]
}
```

#### Audio Channels (`-ac`)

Set number of audio channels:

```json
{
  "file_url": "https://example.com/audio.raw",
  "options": [
    {"option": "-f", "argument": "s16le"},
    {"option": "-ac", "argument": "2"}
  ]
}
```

## Multiple Input Examples

### Video with Separate Audio

```json
{
  "inputs": [
    {
      "file_url": "https://example.com/video-only.mp4"
    },
    {
      "file_url": "https://example.com/audio-track.wav"
    }
  ]
}
```

### Multiple Video Sources

```json
{
  "inputs": [
    {
      "file_url": "https://example.com/intro.mp4"
    },
    {
      "file_url": "https://example.com/main.mp4",
      "options": [
        {"option": "-ss", "argument": "5"},
        {"option": "-t", "argument": "120"}
      ]
    },
    {
      "file_url": "https://example.com/outro.mp4"
    }
  ]
}
```

### Image Sequences

```json
{
  "inputs": [
    {
      "file_url": "https://example.com/frame%04d.png",
      "options": [
        {"option": "-r", "argument": "30"},
        {"option": "-start_number", "argument": "1"}
      ]
    }
  ]
}
```

## Advanced Input Configurations

### Loop Input

Loop a short video:

```json
{
  "file_url": "https://example.com/short-loop.mp4",
  "options": [
    {"option": "-stream_loop", "argument": "10"}
  ]
}
```

### Generate Test Patterns

Generate test video (useful for testing):

```json
{
  "file_url": "testsrc2=duration=10:size=1920x1080:rate=30",
  "options": [
    {"option": "-f", "argument": "lavfi"}
  ]
}
```

### Generate Test Audio

Generate test audio:

```json
{
  "file_url": "sine=frequency=1000:duration=10",
  "options": [
    {"option": "-f", "argument": "lavfi"}
  ]
}
```

## Input Synchronization

### Different Frame Rates

When inputs have different frame rates:

```json
{
  "inputs": [
    {
      "file_url": "https://example.com/30fps-video.mp4"
    },
    {
      "file_url": "https://example.com/60fps-video.mp4"
    }
  ]
}
```

### Audio/Video Sync

Adjust audio/video synchronization:

```json
{
  "file_url": "https://example.com/out-of-sync.mp4",
  "options": [
    {"option": "-itsoffset", "argument": "0.5"}
  ]
}
```

## Performance Considerations

### Seeking Accuracy

For precise seeking, use:

```json
{
  "file_url": "https://example.com/video.mp4",
  "options": [
    {"option": "-accurate_seek"},
    {"option": "-ss", "argument": "123.456"}
  ]
}
```

### Hardware Decoding

Enable hardware acceleration for input:

```json
{
  "file_url": "https://example.com/h264-video.mp4",
  "options": [
    {"option": "-hwaccel", "argument": "auto"}
  ]
}
```

## Common Input Patterns

### Extract Specific Segments

Extract multiple segments from one source:

```json
{
  "inputs": [
    {
      "file_url": "https://example.com/source.mp4",
      "options": [
        {"option": "-ss", "argument": "0"},
        {"option": "-t", "argument": "30"}
      ]
    },
    {
      "file_url": "https://example.com/source.mp4",
      "options": [
        {"option": "-ss", "argument": "60"},
        {"option": "-t", "argument": "30"}
      ]
    }
  ]
}
```

### Scale at Input Level

Scale video during input (can be more efficient):

```json
{
  "file_url": "https://example.com/large-video.mp4",
  "options": [
    {"option": "-vf", "argument": "scale=1280:720"}
  ]
}
```

### Audio Input Normalization

Normalize audio at input:

```json
{
  "file_url": "https://example.com/audio.wav",
  "options": [
    {"option": "-af", "argument": "loudnorm"}
  ]
}
```

## Error Handling

### Network Timeouts

For slow network sources:

```json
{
  "file_url": "https://slow-server.com/video.mp4",
  "options": [
    {"option": "-timeout", "argument": "30000000"}
  ]
}
```

### Retry on Failure

Configure retries for network inputs:

```json
{
  "file_url": "https://unreliable-server.com/video.mp4",
  "options": [
    {"option": "-reconnect", "argument": "1"},
    {"option": "-reconnect_streamed", "argument": "1"}
  ]
}
```

## Input Validation

The API validates inputs before processing:

- URL accessibility
- File format support
- Basic file integrity

If an input fails validation, the entire job will fail with a descriptive error message.

## Supported Formats

### Video Formats
- MP4, MOV, AVI, MKV, WebM
- FLV, WMV, ASF, OGV
- MTS, M2TS, VOB
- And many more...

### Audio Formats
- MP3, WAV, FLAC, AAC
- OGG, WMA, M4A, AIFF
- AC3, DTS, AMR
- And many more...

### Image Formats
- JPG, PNG, GIF, BMP
- TIFF, WebP, SVG
- And many more...

## Best Practices

1. **Use Precise Seeking**: Use `-ss` before `-i` for faster seeking
2. **Limit Duration**: Use `-t` to process only what you need
3. **Check Input Quality**: Ensure inputs are good quality before processing
4. **Use Appropriate Formats**: Choose formats that match your processing needs
5. **Test Network Sources**: Verify network sources are reliable and accessible

---

*Previous: [Getting Started](./getting-started.md) | Next: [Output Configuration](./outputs.md)*