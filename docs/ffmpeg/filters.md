# FFmpeg Filters Guide

Filters are one of the most powerful features of FFmpeg, allowing you to apply effects, transformations, and processing to video and audio streams. This guide covers how to use filters in the FFmpeg Compose API.

## Filter Types

### Simple Filters

Simple filters apply to a single input and produce a single output. They use the `-vf` (video filter) or `-af` (audio filter) syntax.

**Configuration:**
- Set `use_simple_video_filter: true` for video filters
- Set `use_simple_audio_filter: true` for audio filters
- Set `type: "video"` or `type: "audio"` on filter objects

### Complex Filters

Complex filters can have multiple inputs and outputs, allowing for advanced operations like overlays, mixing, and splitting streams.

**Configuration:**
- Use `input_labels` and `output_label` for stream routing
- Don't set `use_simple_video_filter` or `use_simple_audio_filter`

## Video Filters

### Scaling and Resizing

#### Basic Scaling

```json
{
  "filters": [
    {
      "filter": "scale",
      "arguments": ["1920", "1080"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

#### Scale with Aspect Ratio Preservation

```json
{
  "filters": [
    {
      "filter": "scale",
      "arguments": ["1920", "-1"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

#### Scale to Fit Within Dimensions

```json
{
  "filters": [
    {
      "filter": "scale",
      "arguments": ["'min(1920,iw)'", "'min(1080,ih)'"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

### Cropping

#### Crop to Specific Size

```json
{
  "filters": [
    {
      "filter": "crop",
      "arguments": ["640", "480", "100", "50"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

#### Crop to Center

```json
{
  "filters": [
    {
      "filter": "crop",
      "arguments": ["640", "480", "(iw-640)/2", "(ih-480)/2"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

### Rotation and Flipping

#### Rotate Video

```json
{
  "filters": [
    {
      "filter": "rotate",
      "arguments": ["PI/4"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

#### Flip Horizontally

```json
{
  "filters": [
    {
      "filter": "hflip",
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

#### Flip Vertically

```json
{
  "filters": [
    {
      "filter": "vflip",
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

### Color and Effects

#### Brightness, Contrast, Saturation

```json
{
  "filters": [
    {
      "filter": "eq",
      "arguments": ["brightness=0.1", "contrast=1.2", "saturation=1.3"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

#### Blur Effect

```json
{
  "filters": [
    {
      "filter": "boxblur",
      "arguments": ["5", "1"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

#### Sharpen Video

```json
{
  "filters": [
    {
      "filter": "unsharp",
      "arguments": ["5", "5", "1.0", "5", "5", "0.0"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

#### Black and White

```json
{
  "filters": [
    {
      "filter": "colorchannelmixer",
      "arguments": [".3", ".4", ".3", "0", ".3", ".4", ".3", "0", ".3", ".4", ".3"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

### Frame Rate and Speed

#### Change Frame Rate

```json
{
  "filters": [
    {
      "filter": "fps",
      "arguments": ["30"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

#### Speed Up Video (2x)

```json
{
  "filters": [
    {
      "filter": "setpts",
      "arguments": ["0.5*PTS"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

#### Slow Down Video (0.5x)

```json
{
  "filters": [
    {
      "filter": "setpts",
      "arguments": ["2.0*PTS"],
      "type": "video"
    }
  ],
  "use_simple_video_filter": true
}
```

## Audio Filters

### Volume Control

#### Adjust Volume

```json
{
  "filters": [
    {
      "filter": "volume",
      "arguments": ["0.5"],
      "type": "audio"
    }
  ],
  "use_simple_audio_filter": true
}
```

#### Normalize Audio

```json
{
  "filters": [
    {
      "filter": "loudnorm",
      "arguments": ["I=-16", "LRA=11", "TP=-1.5"],
      "type": "audio"
    }
  ],
  "use_simple_audio_filter": true
}
```

### Frequency Filters

#### High-Pass Filter

```json
{
  "filters": [
    {
      "filter": "highpass",
      "arguments": ["f=200"],
      "type": "audio"
    }
  ],
  "use_simple_audio_filter": true
}
```

#### Low-Pass Filter

```json
{
  "filters": [
    {
      "filter": "lowpass",
      "arguments": ["f=3000"],
      "type": "audio"
    }
  ],
  "use_simple_audio_filter": true
}
```

### Audio Enhancement

#### Remove Noise

```json
{
  "filters": [
    {
      "filter": "afftdn",
      "arguments": ["nf=-25"],
      "type": "audio"
    }
  ],
  "use_simple_audio_filter": true
}
```

#### Compressor

```json
{
  "filters": [
    {
      "filter": "acompressor",
      "arguments": ["threshold=0.089", "ratio=9", "attack=200", "release=1000"],
      "type": "audio"
    }
  ],
  "use_simple_audio_filter": true
}
```

## Complex Filter Examples

### Video Overlay

Overlay one video on top of another:

```json
{
  "inputs": [
    {"file_url": "https://example.com/background.mp4"},
    {"file_url": "https://example.com/overlay.mp4"}
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
      "arguments": ["10", "10"],
      "input_labels": ["0:v", "overlay_scaled"],
      "output_label": "final_video"
    }
  ],
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"}
      ],
      "stream_mappings": ["[final_video]", "0:a"]
    }
  ]
}
```

### Side-by-Side Videos

Place two videos next to each other:

```json
{
  "inputs": [
    {"file_url": "https://example.com/left.mp4"},
    {"file_url": "https://example.com/right.mp4"}
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
      "stream_mappings": ["[combined]", "0:a"]
    }
  ]
}
```

### Audio Mixing

Mix multiple audio sources with different volumes:

```json
{
  "inputs": [
    {"file_url": "https://example.com/music.mp3"},
    {"file_url": "https://example.com/voice.wav"}
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
      "arguments": ["inputs=2", "duration=longest"],
      "input_labels": ["music_low", "voice_clear"],
      "output_label": "mixed_audio"
    }
  ],
  "outputs": [
    {
      "stream_mappings": ["[mixed_audio]"]
    }
  ]
}
```

### Picture-in-Picture

Create a picture-in-picture effect:

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
      "output_label": "pip_result"
    }
  ],
  "outputs": [
    {
      "stream_mappings": ["[pip_result]", "0:a"]
    }
  ]
}
```

## Filter Chains

You can chain multiple filters together:

### Video Filter Chain

```json
{
  "filters": [
    {
      "filter": "scale",
      "arguments": ["1280", "720"],
      "input_labels": ["0:v"],
      "output_label": "scaled"
    },
    {
      "filter": "eq",
      "arguments": ["brightness=0.1", "contrast=1.2"],
      "input_labels": ["scaled"],
      "output_label": "color_corrected"
    },
    {
      "filter": "unsharp",
      "arguments": ["5", "5", "1.0"],
      "input_labels": ["color_corrected"],
      "output_label": "sharpened"
    }
  ]
}
```

### Audio Filter Chain

```json
{
  "filters": [
    {
      "filter": "highpass",
      "arguments": ["f=80"],
      "input_labels": ["0:a"],
      "output_label": "highpassed"
    },
    {
      "filter": "lowpass",
      "arguments": ["f=8000"],
      "input_labels": ["highpassed"],
      "output_label": "filtered"
    },
    {
      "filter": "loudnorm",
      "arguments": ["I=-16"],
      "input_labels": ["filtered"],
      "output_label": "normalized"
    }
  ]
}
```

## Performance Tips

1. **Use Hardware Acceleration**: Some filters support GPU acceleration
2. **Scale Early**: Scale videos down before applying complex filters
3. **Avoid Unnecessary Filters**: Only apply filters that are needed
4. **Use Simple Filters When Possible**: Simple filters are often faster than complex ones
5. **Test with Short Clips**: Test filter combinations on short clips first

## Common Filter Parameters

### Video Filter Variables

- `iw`, `ih`: Input width and height
- `ow`, `oh`: Output width and height
- `dar`: Display aspect ratio
- `sar`: Sample aspect ratio
- `t`: Timestamp in seconds
- `n`: Frame number

### Audio Filter Variables

- `sr`: Sample rate
- `nb_channels`: Number of channels
- `tb`: Time base
- `t`: Timestamp in seconds

## Troubleshooting Filters

### Common Issues

1. **"No such filter"**: Check filter name spelling
2. **"Invalid argument"**: Verify filter parameter syntax
3. **"Graph setup failed"**: Check input/output label connections
4. **Performance issues**: Consider simplifying complex filter graphs

### Debug Tips

1. Use simple test inputs first
2. Build filter graphs incrementally
3. Check FFmpeg documentation for specific filter syntax
4. Test individual filters before combining them

---

*Previous: [Stream Mapping](./stream-mapping.md) | Next: [Metadata Extraction](./metadata.md)*