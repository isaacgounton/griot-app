# Output Configuration

This guide explains how to configure output files for FFmpeg Compose operations, including codec selection, quality settings, and advanced output options.

## Basic Output Structure

Each output defines how the processed media should be encoded and saved:

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-crf", "argument": 23},
    {"option": "-c:a", "argument": "aac"}
  ],
  "stream_mappings": ["0:v:0", "0:a:0"]
}
```

## Output Options

### Video Codec Options

#### H.264 (libx264) - Most Compatible

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-crf", "argument": 23},
    {"option": "-preset", "argument": "medium"}
  ]
}
```

**CRF Values:**
- `18` - Visually lossless (large files)
- `23` - Default (good quality/size balance)
- `28` - Lower quality (smaller files)

**Presets:**
- `ultrafast` - Fastest encoding
- `fast` - Fast encoding
- `medium` - Default balance
- `slow` - Better compression
- `veryslow` - Best compression

#### H.265 (libx265) - Better Compression

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx265"},
    {"option": "-crf", "argument": 28},
    {"option": "-preset", "argument": "medium"}
  ]
}
```

#### VP9 (libvpx-vp9) - For WebM

```json
{
  "options": [
    {"option": "-c:v", "argument": "libvpx-vp9"},
    {"option": "-crf", "argument": 30},
    {"option": "-b:v", "argument": "0"}
  ]
}
```

#### Copy Video Stream

```json
{
  "options": [
    {"option": "-c:v", "argument": "copy"}
  ]
}
```

### Audio Codec Options

#### AAC - Most Compatible

```json
{
  "options": [
    {"option": "-c:a", "argument": "aac"},
    {"option": "-b:a", "argument": "128k"}
  ]
}
```

**Bitrates:**
- `96k` - Low quality
- `128k` - Standard quality
- `192k` - High quality
- `320k` - Very high quality

#### MP3

```json
{
  "options": [
    {"option": "-c:a", "argument": "mp3"},
    {"option": "-b:a", "argument": "192k"}
  ]
}
```

#### Opus - High Quality

```json
{
  "options": [
    {"option": "-c:a", "argument": "libopus"},
    {"option": "-b:a", "argument": "128k"}
  ]
}
```

#### Copy Audio Stream

```json
{
  "options": [
    {"option": "-c:a", "argument": "copy"}
  ]
}
```

## Quality Control

### Constant Rate Factor (CRF)

CRF provides consistent quality across the video:

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-crf", "argument": 20}
  ]
}
```

**Quality Guide:**
- `0` - Lossless (huge files)
- `18` - Visually lossless
- `23` - Default (recommended)
- `28` - Acceptable quality
- `35+` - Poor quality

### Bitrate Control

#### Constant Bitrate

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-b:v", "argument": "2M"}
  ]
}
```

#### Variable Bitrate (Two-Pass)

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-b:v", "argument": "2M"},
    {"option": "-pass", "argument": "1"}
  ]
}
```

### Target File Size

Calculate bitrate for target file size:

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-fs", "argument": "50MB"}
  ]
}
```

## Resolution and Frame Rate

### Set Output Resolution

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-s", "argument": "1920x1080"}
  ]
}
```

### Set Frame Rate

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-r", "argument": "30"}
  ]
}
```

### Maintain Aspect Ratio

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-aspect", "argument": "16:9"}
  ]
}
```

## Format-Specific Options

### MP4 Output

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-c:a", "argument": "aac"},
    {"option": "-movflags", "argument": "+faststart"}
  ]
}
```

### WebM Output

```json
{
  "options": [
    {"option": "-c:v", "argument": "libvpx-vp9"},
    {"option": "-c:a", "argument": "libopus"},
    {"option": "-f", "argument": "webm"}
  ]
}
```

### Audio-Only Output

```json
{
  "options": [
    {"option": "-c:a", "argument": "mp3"},
    {"option": "-vn"},
    {"option": "-b:a", "argument": "192k"}
  ]
}
```

### Video-Only Output

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-an"},
    {"option": "-crf", "argument": 23}
  ]
}
```

## Multiple Output Examples

### Different Quality Levels

```json
{
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
        {"option": "-s", "argument": "1280x720"},
        {"option": "-c:a", "argument": "aac"},
        {"option": "-b:a", "argument": "96k"}
      ]
    }
  ]
}
```

### Different Formats

```json
{
  "outputs": [
    {
      "options": [
        {"option": "-c:v", "argument": "libx264"},
        {"option": "-c:a", "argument": "aac"}
      ]
    },
    {
      "options": [
        {"option": "-c:v", "argument": "libvpx-vp9"},
        {"option": "-c:a", "argument": "libopus"},
        {"option": "-f", "argument": "webm"}
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

## Hardware Acceleration

### NVIDIA GPU (NVENC)

```json
{
  "options": [
    {"option": "-c:v", "argument": "h264_nvenc"},
    {"option": "-preset", "argument": "fast"},
    {"option": "-crf", "argument": 23}
  ]
}
```

### Intel Quick Sync (QSV)

```json
{
  "options": [
    {"option": "-c:v", "argument": "h264_qsv"},
    {"option": "-preset", "argument": "medium"},
    {"option": "-crf", "argument": 23}
  ]
}
```

### AMD GPU (AMF)

```json
{
  "options": [
    {"option": "-c:v", "argument": "h264_amf"},
    {"option": "-quality", "argument": "speed"},
    {"option": "-rc", "argument": "crf"},
    {"option": "-crf", "argument": 23}
  ]
}
```

## Advanced Options

### Custom Pixel Format

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-pix_fmt", "argument": "yuv420p"}
  ]
}
```

### Metadata Options

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-metadata", "argument": "title=My Video"},
    {"option": "-metadata", "argument": "artist=John Doe"}
  ]
}
```

### Subtitles

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-c:s", "argument": "mov_text"}
  ]
}
```

## Output File Naming

FFmpeg Compose automatically generates unique output filenames:

- Single output: `output_0.{ext}`
- Multiple outputs: `output_0.{ext}`, `output_1.{ext}`, etc.
- Extension determined by codec/format

## Performance Optimization

### Fast Encoding

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-preset", "argument": "ultrafast"},
    {"option": "-crf", "argument": 23}
  ]
}
```

### Quality Encoding

```json
{
  "options": [
    {"option": "-c:v", "argument": "libx264"},
    {"option": "-preset", "argument": "veryslow"},
    {"option": "-crf", "argument": 18}
  ]
}
```

### Stream Copy (Fastest)

```json
{
  "options": [
    {"option": "-c:v", "argument": "copy"},
    {"option": "-c:a", "argument": "copy"}
  ]
}
```

## Troubleshooting

### Common Issues

1. **Codec not found**: Check codec spelling and availability
2. **Quality too low**: Lower CRF value or increase bitrate
3. **File too large**: Increase CRF value or decrease bitrate
4. **Encoding too slow**: Use faster preset or hardware acceleration

### Compatibility Tips

1. **Web playback**: Use H.264 + AAC in MP4 container
2. **Mobile devices**: Keep resolution ≤ 1080p
3. **Streaming**: Use `-movflags +faststart` for MP4
4. **Old devices**: Use H.264 baseline profile

## Best Practices

1. **Use CRF for quality**: More consistent than bitrate
2. **Test with short clips**: Verify settings before long encodes
3. **Copy when possible**: Avoid re-encoding when not needed
4. **Choose appropriate presets**: Balance speed vs. compression
5. **Consider hardware acceleration**: For faster processing

---

*Previous: [Input Configuration](./inputs.md) | Next: [Stream Mapping](./stream-mapping.md)*