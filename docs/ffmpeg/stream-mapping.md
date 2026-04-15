# Stream Mapping

Stream mapping is a powerful feature that allows you to control which input streams are included in which outputs and how they are combined. This guide explains the concepts and syntax for effective stream mapping.

## Basic Concepts

### What are Streams?

Media files contain different types of streams:
- **Video streams**: Visual content (0:v:0, 0:v:1, etc.)
- **Audio streams**: Audio tracks (0:a:0, 0:a:1, etc.)
- **Subtitle streams**: Text/subtitle tracks (0:s:0, 0:s:1, etc.)
- **Data streams**: Metadata or other data

### Stream Specifier Syntax

FFmpeg uses a specific syntax to identify streams:

```
[input_index]:[stream_type]:[stream_index]
```

Examples:
- `0:v:0` - First video stream from first input
- `1:a:0` - First audio stream from second input
- `0:v` - All video streams from first input
- `0:a` - All audio streams from first input

## Global vs Output-Specific Mappings

### Global Stream Mappings

Applied to all outputs (specified at request level):

```json
{
  "inputs": [/* inputs */],
  "stream_mappings": ["0:v:0", "1:a:0"],
  "outputs": [/* outputs */]
}
```

### Output-Specific Mappings

Applied only to specific outputs:

```json
{
  "outputs": [
    {
      "options": [/* options */],
      "stream_mappings": ["0:v:0", "0:a:0"]
    }
  ]
}
```

## Common Mapping Scenarios

### Replace Audio Track

Replace video's audio with external audio:

```json
{
  "inputs": [
    {"file_url": "https://example.com/video.mp4"},
    {"file_url": "https://example.com/new-audio.wav"}
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

### Extract Specific Streams

Create video-only and audio-only files:

```json
{
  "inputs": [
    {"file_url": "https://example.com/movie.mp4"}
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

### Multiple Audio Tracks

Select specific audio tracks:

```json
{
  "inputs": [
    {"file_url": "https://example.com/multi-audio.mkv"}
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["0:v:0", "0:a:0", "0:a:2"]
    }
  ]
}
```

## Filter Output Mapping

When using filters, map filter outputs using labels:

### Simple Filter Output

```json
{
  "inputs": [
    {"file_url": "https://example.com/video.mp4"}
  ],
  "filters": [
    {
      "filter": "scale",
      "arguments": ["1280", "720"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true,
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"}
      ],
      "stream_mappings": ["0:a:0"]
    }
  ]
}
```

### Complex Filter Output

```json
{
  "inputs": [
    {"file_url": "https://example.com/video1.mp4"},
    {"file_url": "https://example.com/video2.mp4"}
  ],
  "filters": [
    {
      "filter": "hstack",
      "arguments": ["inputs=2"],
      "input_labels": ["0:v", "1:v"],
      "output_label": "combined"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"}
      ],
      "stream_mappings": ["[combined]", "0:a:0"]
    }
  ]
}
```

## Advanced Mapping Examples

### Multi-Input, Multi-Output

Process multiple inputs into different outputs:

```json
{
  "inputs": [
    {"file_url": "https://example.com/intro.mp4"},
    {"file_url": "https://example.com/main.mp4"},
    {"file_url": "https://example.com/outro.mp4"}
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["1:v:0", "1:a:0"]
    },
    {
      "options": [
        {"option": "-c:a", "argument": "mp3"},
        {"option": "-vn"}
      ],
      "stream_mappings": ["0:a:0", "1:a:0", "2:a:0"]
    }
  ]
}
```

### Subtitle Mapping

Include subtitle streams:

```json
{
  "inputs": [
    {"file_url": "https://example.com/movie.mkv"}
  ],
  "stream_mappings": ["0:v:0", "0:a:0", "0:s:0", "0:s:1"],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"},
        {"option": "-c:s", "argument": "mov_text"}
      ]
    }
  ]
}
```

### Language-Specific Audio

Map audio by language (requires metadata):

```json
{
  "inputs": [
    {"file_url": "https://example.com/multilang.mkv"}
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "copy"},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["0:v:0", "0:a:m:language:eng"]
    },
    {
      "options": [
        {"option": "-c:v", "argument": "copy"},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["0:v:0", "0:a:m:language:spa"]
    }
  ]
}
```

## Stream Selection Options

### Automatic Selection

Let FFmpeg choose the best streams:

```json
{
  "stream_mappings": ["0"],
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

### Disable Streams

Exclude specific stream types:

```json
{
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-an"}
      ]
    },
    {
      "options": [
        {"option": "-c:a", "argument": "mp3"},
        {"option": "-vn"}
      ]
    }
  ]
}
```

## Complex Mapping Scenarios

### Picture-in-Picture with Audio Mixing

```json
{
  "inputs": [
    {"file_url": "https://example.com/main.mp4"},
    {"file_url": "https://example.com/pip.mp4"}
  ],
  "filters": [
    {
      "filter": "scale",
      "arguments": ["320", "180"],
      "input_labels": ["1:v"],
      "output_label": "pip_small"
    },
    {
      "filter": "overlay",
      "arguments": ["W-w-10", "10"],
      "input_labels": ["0:v", "pip_small"],
      "output_label": "video_out"
    },
    {
      "filter": "amix",
      "arguments": ["inputs=2", "duration=longest"],
      "input_labels": ["0:a", "1:a"],
      "output_label": "audio_out"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["[video_out]", "[audio_out]"]
    }
  ]
}
```

### Multi-Camera Sync

Synchronize multiple camera angles:

```json
{
  "inputs": [
    {"file_url": "https://example.com/camera1.mp4"},
    {"file_url": "https://example.com/camera2.mp4"},
    {"file_url": "https://example.com/audio.wav"}
  ],
  "filters": [
    {
      "filter": "scale",
      "arguments": ["640", "360"],
      "input_labels": ["0:v"],
      "output_label": "cam1_scaled"
    },
    {
      "filter": "scale",
      "arguments": ["640", "360"],
      "input_labels": ["1:v"],
      "output_label": "cam2_scaled"
    },
    {
      "filter": "hstack",
      "arguments": ["inputs=2"],
      "input_labels": ["cam1_scaled", "cam2_scaled"],
      "output_label": "combined_video"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ],
      "stream_mappings": ["[combined_video]", "2:a:0"]
    }
  ]
}
```

## Mapping Best Practices

### 1. Be Explicit

Always specify exact streams when possible:

```json
// Good
"stream_mappings": ["0:v:0", "0:a:0"]

// Less predictable
"stream_mappings": ["0"]
```

### 2. Check Input Streams

Use metadata extraction to understand input structure:

```json
{
  "metadata": {
    "encoder": true
  }
}
```

### 3. Test with Simple Cases

Start with basic mappings before complex scenarios:

```json
// Start simple
"stream_mappings": ["0:v:0", "0:a:0"]

// Then add complexity
"stream_mappings": ["[filtered_video]", "[mixed_audio]"]
```

### 4. Use Copy When Possible

Avoid re-encoding compatible streams:

```json
{
  "options": [
    {"option": "-c:v", "argument": "copy"},
    {"option": "-c:a", "argument": "copy"}
  ]
}
```

### 5. Handle Missing Streams

Gracefully handle inputs without expected streams:

```json
{
  "stream_mappings": ["0:v:0?", "0:a:0?"]
}
```

## Troubleshooting

### Common Issues

1. **"Stream not found"**: Check input file structure
2. **"No video/audio"**: Verify stream mappings
3. **"Sync issues"**: Check timestamp alignment
4. **"Wrong track selected"**: Use explicit stream indices

### Debug Tips

1. Use metadata extraction to inspect inputs
2. Start with simple mappings
3. Test one stream type at a time
4. Check FFmpeg logs for detailed errors

---

*Previous: [Output Configuration](./outputs.md) | Next: [Metadata Extraction](./metadata.md)*