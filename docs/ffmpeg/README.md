# FFmpeg Compose Documentation

Welcome to the FFmpeg Compose documentation. This powerful feature allows you to create complex media processing workflows using JSON configuration instead of writing FFmpeg commands manually.

## Overview

The FFmpeg Compose API endpoint provides a flexible and powerful way to compose complex FFmpeg commands by providing input files, filters, and output options through a simple JSON interface. This eliminates the need to understand complex FFmpeg command-line syntax while still providing access to the full power of FFmpeg.

## Quick Start

### Basic Video Conversion

```bash
curl -X POST "http://localhost:8000/v1/ffmpeg/compose" \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "my-conversion-job",
    "inputs": [
      {
        "file_url": "https://example.com/input.mov"
      }
    ],
    "outputs": [
      {
        "options": [
          {"option": "-c:v", "argument": "libx264"},
          {"option": "-crf", "argument": 23},
          {"option": "-c:a", "argument": "aac"}
        ]
      }
    ]
  }'
```

### Check Job Status

```bash
curl -X GET "http://localhost:8000/v1/ffmpeg/compose/{job_id}" \
  -H "X-API-Key: your-api-key"
```

## Key Features

- **Multiple Input Support**: Process multiple input files with individual FFmpeg options
- **Complex Filter Graphs**: Apply both simple filters and complex filter graphs
- **Stream Mapping**: Control which streams go to which outputs
- **Metadata Extraction**: Generate thumbnails, extract duration, bitrate, and other metadata
- **Background Processing**: All operations run asynchronously with job tracking
- **S3 Integration**: Output files are automatically uploaded to S3

## Documentation Sections

1. [Getting Started](./getting-started.md) - Basic concepts and your first FFmpeg compose job
2. [Input Configuration](./inputs.md) - How to configure input files and their options
3. [Output Configuration](./outputs.md) - Setting up outputs with codecs, quality, and formats
4. [Filters](./filters.md) - Complete guide to video and audio filters
5. [Stream Mapping](./stream-mapping.md) - Understanding and using stream mapping
6. [Metadata Extraction](./metadata.md) - Extracting thumbnails, duration, and file information
7. [Examples](./examples.md) - Common use cases and example configurations
8. [Advanced Usage](./advanced.md) - Complex scenarios and best practices
9. [Error Handling](./error-handling.md) - Understanding and debugging common issues
10. [API Reference](./api-reference.md) - Complete API documentation

## Common Use Cases

- **Video Conversion**: Convert between different video formats and codecs
- **Audio Processing**: Mix, normalize, and convert audio files
- **Video Effects**: Apply filters, scaling, rotation, and color correction
- **Stream Manipulation**: Combine video from one source with audio from another
- **Thumbnail Generation**: Extract frames from videos for thumbnails
- **Quality Optimization**: Adjust bitrates, resolution, and compression settings

## Support

- Check the [Examples](./examples.md) section for common use cases
- Review [Error Handling](./error-handling.md) for troubleshooting
- See the complete [API Reference](./api-reference.md) for all available options

---

*Next: [Getting Started](./getting-started.md)*