# Audio Feedback Detection and Suppression

This section documents the audio feedback detection and suppression capabilities that can be implemented using the Griot's FFmpeg infrastructure.

> **Note:** Audio feedback detection is not currently implemented but can be added using the existing FFmpeg processing framework. This documentation outlines the proposed implementation and available FFmpeg filters.

## Overview

Audio feedback occurs when a microphone picks up sound from speakers, creating a loop that results in unwanted noise, whistling, or howling sounds. Feedback detection and suppression is crucial for:

- Live audio streaming and broadcasting
- Recording cleanup and post-processing
- Real-time audio processing in conferencing systems
- Podcast and content creation quality control

## Proposed Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/media/feedback/detect` | POST | Create a feedback detection job |
| `/v1/media/feedback/detect/{job_id}` | GET | Get the status of a feedback detection job |
| `/v1/media/feedback/suppress` | POST | Create a feedback suppression job |
| `/v1/media/feedback/suppress/{job_id}` | GET | Get the status of a feedback suppression job |

## FFmpeg Filters for Feedback Processing

The Griot's existing FFmpeg infrastructure supports various filters that can be used for feedback detection and suppression:

### Feedback Suppression Filters

#### 1. FFT Denoiser (`afftdn`)
Advanced noise reduction using FFT analysis.

```bash
ffmpeg -i input.wav -af "afftdn=nr=10:nf=-25" output.wav
```

**Parameters:**
- `nr`: Noise reduction amount (0-97, default: 12)
- `nf`: Noise floor in dB (default: -50)
- `tn`: Enable transient noise reduction
- `tr`: Transient threshold

#### 2. High-pass Filter (`highpass`)
Removes low-frequency feedback loops.

```bash
ffmpeg -i input.wav -af "highpass=f=300:p=1" output.wav
```

**Parameters:**
- `f`: Cutoff frequency in Hz
- `p`: Number of poles (1 or 2)
- `w`: Width type (h, q, o, s, k)

#### 3. Low-pass Filter (`lowpass`)
Removes high-frequency whistling and squealing.

```bash
ffmpeg -i input.wav -af "lowpass=f=8000:p=2" output.wav
```

#### 4. Notch Filter (`notch`)
Removes specific frequency feedback.

```bash
ffmpeg -i input.wav -af "notch=frequency=1000:width_type=h:width=200" output.wav
```

**Parameters:**
- `frequency`: Center frequency to remove
- `width_type`: Width measurement type
- `width`: Filter width

#### 5. Band-pass Filter (`bandpass`)
Keeps only desired frequency range.

```bash
ffmpeg -i input.wav -af "bandpass=f=1000:width_type=h:width=500" output.wav
```

#### 6. Dynamic Range Compressor (`compand`)
Reduces sudden volume spikes that can cause feedback.

```bash
ffmpeg -i input.wav -af "compand=0.1,0.2:-90/-90,-50/-25,-25/-15,-10/-10:6:0:-90:0.1" output.wav
```

## Proposed Implementation

### Feedback Detection

**Endpoint:** `POST /v1/media/feedback/detect`

**Request Body:**
```json
{
  "url": "https://example.com/audio.mp3",
  "sensitivity": "medium",
  "frequency_range": {
    "min": 100,
    "max": 8000
  },
  "analysis_window": 1.0
}
```

**Parameters:**
- `url` (string, required): URL of the audio file to analyze
- `sensitivity` (string, optional): Detection sensitivity ("low", "medium", "high")
- `frequency_range` (object, optional): Frequency range to analyze
- `analysis_window` (number, optional): Analysis window in seconds

**Response:**
```json
{
  "job_id": "feedback-abc123-def456",
  "status": "pending"
}
```

**Completed Response:**
```json
{
  "job_id": "feedback-abc123-def456",
  "status": "completed",
  "result": {
    "feedback_detected": true,
    "feedback_segments": [
      {
        "start": 15.2,
        "end": 16.8,
        "frequency": 2400,
        "intensity": "high",
        "type": "whistling"
      },
      {
        "start": 32.1,
        "end": 33.5,
        "frequency": 800,
        "intensity": "medium",
        "type": "howling"
      }
    ],
    "dominant_frequencies": [2400, 800, 1200],
    "overall_severity": "medium",
    "recommendations": [
      "Apply notch filter at 2400Hz",
      "Use high-pass filter above 300Hz",
      "Consider compressor to reduce peaks"
    ]
  },
  "error": null
}
```

### Feedback Suppression

**Endpoint:** `POST /v1/media/feedback/suppress`

**Request Body:**
```json
{
  "url": "https://example.com/audio.mp3",
  "suppression_method": "adaptive",
  "target_frequencies": [2400, 800],
  "preserve_quality": true,
  "output_format": "wav"
}
```

**Parameters:**
- `url` (string, required): URL of the audio file to process
- `suppression_method` (string, optional): Method ("notch", "adaptive", "broadband")
- `target_frequencies` (array, optional): Specific frequencies to target
- `preserve_quality` (boolean, optional): Prioritize audio quality
- `output_format` (string, optional): Output format ("wav", "mp3", "m4a")

**Response:**
```json
{
  "job_id": "suppress-xyz789-abc123",
  "status": "pending"
}
```

**Completed Response:**
```json
{
  "job_id": "suppress-xyz789-abc123",
  "status": "completed",
  "result": {
    "processed_url": "https://s3.amazonaws.com/bucket/processed-audio.wav",
    "filters_applied": [
      "notch=frequency=2400:width=50",
      "highpass=f=300",
      "afftdn=nr=8"
    ],
    "feedback_reduction": "85%",
    "quality_preserved": true,
    "processing_time": 12.3
  },
  "error": null
}
```

## Detection Algorithms

### Spectral Analysis Method
1. **FFT Analysis**: Analyze frequency spectrum for sustained tones
2. **Peak Detection**: Identify narrow frequency peaks above threshold
3. **Temporal Analysis**: Check for persistence over time windows
4. **Harmonic Analysis**: Detect harmonic relationships indicating feedback

### Energy-based Detection
1. **RMS Monitoring**: Track sudden energy increases
2. **Frequency Tracking**: Monitor dominant frequency changes
3. **Onset Detection**: Identify sudden acoustic events
4. **Duration Analysis**: Distinguish feedback from natural sounds

### Machine Learning Approach
1. **Feature Extraction**: Spectral features, MFCCs, chroma
2. **Pattern Recognition**: Trained models for feedback patterns
3. **Real-time Classification**: Frame-by-frame feedback probability
4. **Context Awareness**: Consider audio content type

## Suppression Strategies

### Adaptive Filtering
- **Real-time Analysis**: Continuous frequency monitoring
- **Dynamic Response**: Adjust filters based on detected feedback
- **Minimal Impact**: Preserve audio quality in non-feedback regions

### Targeted Suppression
- **Notch Filtering**: Remove specific problematic frequencies
- **Bandwidth Limiting**: Restrict frequency range to safe zones
- **Gain Control**: Automatic gain reduction during feedback events

### Preventive Processing
- **Pre-emphasis**: Shape frequency response to prevent feedback
- **Compression**: Limit dynamic range to reduce feedback potential
- **EQ Adjustment**: Preemptive frequency shaping

## Use Cases

### Live Audio Processing
- **Streaming**: Real-time feedback suppression for live streams
- **Broadcasting**: Professional audio quality for radio/TV
- **Conferencing**: Clear audio in virtual meetings
- **Performance**: Live music and speaking events

### Post-Production
- **Podcast Cleanup**: Remove feedback from recordings
- **Video Production**: Clean audio tracks for videos
- **Archive Restoration**: Improve quality of historical recordings
- **Content Creation**: Professional-quality audio for creators

### Real-time Applications
- **Hearing Aids**: Feedback suppression in assistive devices
- **PA Systems**: Prevent feedback in public address systems
- **Monitoring**: Studio monitor feedback prevention
- **Communication**: Clear audio in communication systems

## Technical Considerations

### Performance Impact
- **Processing Delay**: Real-time vs. quality trade-offs
- **CPU Usage**: Filter complexity affects processing load
- **Memory Requirements**: Spectral analysis buffer sizes
- **Quality Preservation**: Balance between suppression and fidelity

### Integration Points
- **Existing Infrastructure**: Leverage FFmpeg composer service
- **Job Queue System**: Async processing for large files
- **S3 Storage**: Secure handling of processed audio
- **API Consistency**: Follow existing endpoint patterns

### Configuration Options
- **Sensitivity Levels**: Adjustable detection thresholds
- **Filter Presets**: Common configurations for different scenarios
- **Custom Parameters**: Advanced users can specify filter details
- **Quality Modes**: Different processing modes for various use cases

## Example Filter Chains

### Basic Feedback Suppression
```bash
ffmpeg -i input.wav -af "highpass=f=80,afftdn=nr=10,compand=0.1,0.2:-90/-90,-50/-25,-25/-15,-10/-10:6:0:-90:0.1" output.wav
```

### Advanced Multi-stage Processing
```bash
ffmpeg -i input.wav -af "
  highpass=f=80,
  notch=f=1200:w=50,
  notch=f=2400:w=30,
  afftdn=nr=12:nf=-30,
  compand=0.1,0.2:-90/-90,-50/-25,-25/-15,-10/-10:6:0:-90:0.1,
  lowpass=f=8000
" output.wav
```

### Real-time Streaming
```bash
ffmpeg -f alsa -i hw:0 -af "
  highpass=f=100,
  afftdn=nr=8:tn=1,
  compand=0.05,0.1:-90/-90,-50/-30,-30/-20,-20/-20:6:0:-90:0.05
" -f flv rtmp://streaming-server/live/stream
```

## Error Handling

**Common Error Scenarios:**

**Unsupported Audio Format:**
```json
{
  "job_id": "feedback-abc123",
  "status": "failed",
  "error": "Unsupported audio format for feedback processing"
}
```

**Processing Failure:**
```json
{
  "job_id": "feedback-abc123",
  "status": "failed",
  "error": "Feedback suppression failed: insufficient audio data"
}
```

**Invalid Parameters:**
```json
{
  "detail": [
    {
      "loc": ["body", "frequency_range", "min"],
      "msg": "Minimum frequency must be positive",
      "type": "value_error"
    }
  ]
}
```

## Implementation Roadmap

### Phase 1: Basic Detection
- Implement spectral analysis for feedback detection
- Create basic API endpoints
- Add simple notch filtering for suppression

### Phase 2: Advanced Processing
- Add adaptive filtering algorithms
- Implement real-time processing capabilities
- Create filter preset configurations

### Phase 3: Machine Learning
- Train models for improved detection accuracy
- Add context-aware processing
- Implement predictive feedback prevention

### Phase 4: Real-time Integration
- WebSocket support for live audio processing
- Low-latency processing optimization
- Integration with streaming protocols

## Best Practices

### Detection Accuracy
- **Multiple Methods**: Combine spectral and energy-based detection
- **Temporal Validation**: Confirm feedback persistence over time
- **False Positive Reduction**: Distinguish feedback from legitimate audio
- **Calibration**: Adjust thresholds based on audio content type

### Quality Preservation
- **Minimal Processing**: Apply only necessary suppression
- **Frequency Precision**: Target specific problematic frequencies
- **Dynamic Adjustment**: Adapt processing intensity to feedback severity
- **Quality Monitoring**: Track processed audio quality metrics

### Performance Optimization
- **Efficient Algorithms**: Use optimized FFT implementations
- **Parallel Processing**: Process multiple frequency bands simultaneously
- **Caching**: Cache analysis results for repeated processing
- **Resource Management**: Balance quality with processing requirements