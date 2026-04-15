# FFmpeg Compose Examples

This page contains practical examples for common media processing tasks using the FFmpeg Compose API.

## Video Processing Examples

### Basic Video Conversion

Convert any video to MP4 with H.264:

```json
{
  "id": "basic-video-conversion",
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
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "128k"}
      ]
    }
  ],
  "metadata": {
    "thumbnail": true,
    "filesize": true,
    "duration": true
  }
}
```

### Video Quality Control

Create multiple quality versions:

```json
{
  "id": "multi-quality-video",
  "inputs": [
    {
      "file_url": "https://example.com/source.mp4"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 18},
        {"option": "-c:a", "argument": "aac"}
      ]
    },
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 28},
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "96k"}
      ]
    }
  ]
}
```

### Video Scaling

Resize video to specific dimensions:

```json
{
  "id": "video-scaling",
  "inputs": [
    {
      "file_url": "https://example.com/large-video.mp4"
    }
  ],
  "filters": [
    {
      "filter": "scale",
      "arguments": ["1920", "1080"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true,
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "copy"}
      ]
    }
  ]
}
```

### Extract Video Segment

Extract a specific time range:

```json
{
  "id": "extract-segment",
  "inputs": [
    {
      "file_url": "https://example.com/long-video.mp4",
      "options": [
        {"option": "-ss", "argument": "00:02:30"},
        {"option": "-t", "argument": "00:01:00"}
      ]
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ]
    }
  ]
}
```

## Audio Processing Examples

### Audio Format Conversion

Convert audio to different formats:

```json
{
  "id": "audio-conversion",
  "inputs": [
    {
      "file_url": "https://example.com/audio.wav"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:a", "argument": "mp3"},
        {"option": "-b:a", "argument": "192k"}
      ]
    },
    {
      "options": [
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "128k"}
      ]
    }
  ]
}
```

### Audio Mixing

Mix multiple audio files:

```json
{
  "id": "audio-mixing",
  "inputs": [
    {
      "file_url": "https://example.com/music.mp3"
    },
    {
      "file_url": "https://example.com/voice.wav"
    }
  ],
  "filters": [
    {
      "filter": "volume",
      "arguments": ["0.3"],
      "input_labels": ["0:a"],
      "output_label": "music_low"
    },
    {
      "filter": "volume",
      "arguments": ["0.8"],
      "input_labels": ["1:a"],
      "output_label": "voice_clear"
    },
    {
      "filter": "amix",
      "arguments": ["inputs=2"],
      "input_labels": ["music_low", "voice_clear"],
      "output_label": "mixed"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "192k"}
      ],
      "stream_mappings": ["[mixed]"]
    }
  ]
}
```

### Audio Normalization

Normalize audio levels:

```json
{
  "id": "audio-normalization",
  "inputs": [
    {
      "file_url": "https://example.com/quiet-audio.mp3"
    }
  ],
  "filters": [
    {
      "filter": "loudnorm",
      "arguments": ["I=-16", "LRA=11", "TP=-1.5"],
      "type": "audio"
    }
  ],
  "use_simple_audio_filter": true,
  "outputs": [
    {
      "options": [
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "192k"}
      ]
    }
  ]
}
```

## Stream Mapping Examples

### Replace Video Audio

Replace video's audio with external audio:

```json
{
  "id": "replace-audio",
  "inputs": [
    {
      "file_url": "https://example.com/video.mp4"
    },
    {
      "file_url": "https://example.com/new-audio.mp3"
    }
  ],
  "stream_mappings": ["0:v:0", "1:a:0"],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "copy"},
        {"option": "-c:a", "argument": "aac"}
      ]
    }
  ]
}
```

### Extract Video and Audio Separately

Create separate video and audio files:

```json
{
  "id": "separate-video-audio",
  "inputs": [
    {
      "file_url": "https://example.com/movie.mp4"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "copy"},
        {"option": "-an"}
      ],
      "stream_mappings": ["0:v:0"]
    },
    {
      "options": [
        {"option": "-c:a", "argument": "mp3"},
        {"option": "-vn"}
      ],
      "stream_mappings": ["0:a:0"]
    }
  ]
}
```

## Complex Filter Examples

### Video Overlay

Overlay one video on top of another:

```json
{
  "id": "video-overlay",
  "inputs": [
    {
      "file_url": "https://example.com/background.mp4"
    },
    {
      "file_url": "https://example.com/overlay.mp4"
    }
  ],
  "filters": [
    {
      "filter": "scale",
      "arguments": ["320", "240"],
      "input_labels": ["1:v"],
      "output_label": "overlay_scaled"
    },
    {
      "filter": "overlay",
      "arguments": ["W-w-10", "H-h-10"],
      "input_labels": ["0:v", "overlay_scaled"],
      "output_label": "final_video"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "copy"}
      ],
      "stream_mappings": ["[final_video]", "0:a"]
    }
  ]
}
```

### Side-by-Side Video

Place two videos side by side:

```json
{
  "id": "side-by-side",
  "inputs": [
    {
      "file_url": "https://example.com/left-video.mp4"
    },
    {
      "file_url": "https://example.com/right-video.mp4"
    }
  ],
  "filters": [
    {
      "filter": "scale",
      "arguments": ["640", "480"],
      "input_labels": ["0:v"],
      "output_label": "left_scaled"
    },
    {
      "filter": "scale",
      "arguments": ["640", "480"],
      "input_labels": ["1:v"],
      "output_label": "right_scaled"
    },
    {
      "filter": "hstack",
      "arguments": ["inputs=2"],
      "input_labels": ["left_scaled", "right_scaled"],
      "output_label": "combined"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["[combined]", "0:a"]
    }
  ]
}
```

### Color Grading

Apply color correction:

```json
{
  "id": "color-grading",
  "inputs": [
    {
      "file_url": "https://example.com/raw-footage.mp4"
    }
  ],
  "filters": [
    {
      "filter": "eq",
      "arguments": ["brightness=0.1", "contrast=1.2", "saturation=1.3"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true,
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 20},
        {"option": "-c:a", "argument": "copy"}
      ]
    }
  ]
}
```

## Optimization Examples

### Fast Processing (Copy Streams)

When possible, copy streams without re-encoding:

```json
{
  "id": "fast-copy",
  "inputs": [
    {
      "file_url": "https://example.com/input.mp4",
      "options": [
        {"option": "-ss", "argument": "00:01:00"},
        {"option": "-t", "argument": "00:02:00"}
      ]
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "copy"},
        {"option": "-c:a", "argument": "copy"}
      ]
    }
  ]
}
```

### Hardware Acceleration

Use hardware encoding for faster processing:

```json
{
  "id": "hardware-encoding",
  "inputs": [
    {
      "file_url": "https://example.com/large-video.mov"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "h264_nvenc"},
        {"option": "-preset", "argument": "fast"},
        {"option": "-crf", "argument": 23},
        {"option": "-c:a", "argument": "aac"}
      ]
    }
  ]
}
```

## Batch Processing Examples

### Multiple Format Outputs

Create multiple formats in one job:

```json
{
  "id": "multi-format-output",
  "inputs": [
    {
      "file_url": "https://example.com/source.mov"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-crf", "argument": 23},
        {"option": "-c:a", "argument": "aac"}
      ]
    },
    {
      "options": [
        {"option": "-c:v", "argument": "libvpx-vp9"},
        {"option": "-crf", "argument": 30},
        {"option": "-c:a", "argument": "libopus"}
      ]
    },
    {
      "options": [
        {"option": "-c:a", "argument": "mp3"},
        {"option": "-vn"}
      ]
    }
  ],
  "metadata": {
    "thumbnail": true,
    "filesize": true,
    "duration": true,
    "bitrate": true
  }
}
```

## Getting Examples Programmatically

You can also retrieve examples using the API:

```bash
curl -X GET "http://localhost:8000/v1/ffmpeg/compose/examples" \
  -H "X-API-Key: your-api-key"
```

This will return a JSON object with example configurations you can modify and use.

## Tips for Creating Your Own Examples

1. **Start Simple**: Begin with basic conversions and add complexity gradually
2. **Test Filters**: Use simple filters before complex filter graphs
3. **Monitor Quality**: Use CRF values between 18-28 for good quality/size balance
4. **Copy When Possible**: Use `copy` codec to avoid re-encoding when formats are compatible
5. **Use Metadata**: Enable metadata extraction to get useful information about outputs

---

*Previous: [Getting Started](./getting-started.md) | Next: [Input Configuration](./inputs.md)*