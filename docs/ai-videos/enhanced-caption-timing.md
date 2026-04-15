# Enhanced Caption Timing

Precise word-level caption timing using whisper-timestamped for superior synchronization and natural caption breaks.

## Overview

Enhanced Caption Timing provides more accurate and natural caption timing than standard Whisper transcription. It uses the whisper-timestamped library to achieve word-level precision and intelligent caption grouping for better readability.

## Features

- **🎯 Word-Level Precision**: Accurate timing for each word
- **📝 Smart Grouping**: Natural 2-4 second caption segments
- **🧠 Intelligent Breaks**: Punctuation-aware sentence splitting
- **⚡ High Performance**: Optimized for real-time processing
- **🔄 Interpolation**: Advanced timing for missing timestamps
- **📊 Multiple Formats**: SRT, word timestamps, and segment data

## Improvements Over Standard Whisper

| Feature | Standard Whisper | Enhanced Timing |
|---------|-----------------|-----------------|
| **Timing Precision** | Segment-level | Word-level |
| **Caption Grouping** | Basic splits | Smart 2-4s groups |
| **Punctuation Handling** | Limited | Sentence-aware |
| **Missing Timestamps** | Gaps | Interpolation |
| **Caption Length** | Variable | Optimized readability |
| **Processing Speed** | Fast | Slightly slower but better |

## Quick Start

### Basic Enhanced Transcription

```bash
curl -X POST "http://localhost:8000/v1/ai/enhanced-captions" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "audio_url": "https://s3.amazonaws.com/bucket/audio.wav",
    "model_size": "base",
    "max_words_per_line": 8
  }'
```

**Response:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

### Check Results

```bash
curl "http://localhost:8000/v1/ai/enhanced-captions/550e8400-e29b-41d4-a716-446655440000" \
  -H "X-API-Key: your_api_key"
```

**Response (when completed):**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "result": {
    "text": "The ocean is vast and mysterious. It contains incredible creatures that we're still discovering.",
    "srt_content": "1\n00:00:00,000 --> 00:00:02,500\nThe ocean is vast\n\n2\n00:00:02,500 --> 00:00:04,800\nand mysterious\n\n3\n00:00:04,800 --> 00:00:07,200\nIt contains incredible creatures\n\n4\n00:00:07,200 --> 00:00:09,500\nthat we're still discovering\n\n",
    "word_timestamps": [
      {"word": "The", "start": 0.0, "end": 0.2, "confidence": 0.98},
      {"word": "ocean", "start": 0.2, "end": 0.6, "confidence": 0.95},
      {"word": "is", "start": 0.6, "end": 0.8, "confidence": 0.99}
    ],
    "segments": [
      {"text": "The ocean is vast and mysterious.", "start": 0.0, "end": 4.8},
      {"text": "It contains incredible creatures that we're still discovering.", "start": 4.8, "end": 9.5}
    ],
    "model_used": "base",
    "total_duration": 9.5,
    "language_detected": "en"
  }
}
```

## API Reference

### POST `/v1/ai/enhanced-captions`

Generate enhanced caption timing for audio content.

#### Request Body

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `audio_url` | string | **required** | URL to audio file for transcription |
| `model_size` | string | `"base"` | Whisper model size |
| `max_words_per_line` | integer | `10` | Maximum words per caption line (1-20) |
| `consider_punctuation` | boolean | `false` | Split captions on sentence boundaries |
| `language` | string | `null` | Language hint for Whisper |

#### Model Size Options

| Model | Speed | Accuracy | Memory | Best For |
|-------|-------|----------|--------|----------|
| `"tiny"` | Fastest | Lower | ~39 MB | Quick testing |
| `"base"` | Fast | Good | ~74 MB | **Recommended default** |
| `"small"` | Medium | Better | ~244 MB | Higher accuracy needs |
| `"medium"` | Slow | High | ~769 MB | Professional quality |
| `"large"` | Slowest | Highest | ~1550 MB | Maximum accuracy |

### GET `/v1/ai/enhanced-captions/{job_id}`

Get enhanced caption timing job status and results.

#### Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `text` | string | Full transcription text |
| `srt_content` | string | Complete SRT subtitle file content |
| `word_timestamps` | array | Word-level timing and confidence data |
| `segments` | array | Larger speech segments with timing |
| `model_used` | string | Whisper model that was used |
| `total_duration` | float | Total audio duration in seconds |
| `language_detected` | string | Auto-detected language code |

#### Word Timestamps Format

```json
{
  "word": "ocean",
  "start": 0.2,
  "end": 0.6,
  "confidence": 0.95
}
```

#### Caption Pairs Format

```json
[
  [[0.0, 2.5], "The ocean is vast"],
  [[2.5, 4.8], "and mysterious"],
  [[4.8, 7.2], "It contains incredible creatures"]
]
```

## Advanced Usage

### High-Accuracy Transcription

```json
{
  "audio_url": "https://s3.amazonaws.com/bucket/professional_audio.wav",
  "model_size": "large",
  "max_words_per_line": 6,
  "consider_punctuation": true,
  "language": "en"
}
```

### Social Media Optimization

```json
{
  "audio_url": "https://s3.amazonaws.com/bucket/tiktok_audio.wav",
  "model_size": "base",
  "max_words_per_line": 4,
  "consider_punctuation": false
}
```

### Multilingual Content

```json
{
  "audio_url": "https://s3.amazonaws.com/bucket/spanish_audio.wav",
  "model_size": "medium",
  "language": "es",
  "max_words_per_line": 8
}
```

## Integration Examples

### Python: Enhanced Caption Processing

```python
import requests
import time

class EnhancedCaptionProcessor:
    def __init__(self, api_key, base_url="http://localhost:8000"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key}
    
    def process_audio(self, audio_url, config=None):
        config = config or {}
        
        # Create job
        response = requests.post(
            f"{self.base_url}/v1/ai/enhanced-captions",
            headers=self.headers,
            json={"audio_url": audio_url, **config}
        )
        job_id = response.json()["job_id"]
        
        # Poll for completion
        while True:
            status_response = requests.get(
                f"{self.base_url}/v1/ai/enhanced-captions/{job_id}",
                headers=self.headers
            )
            status = status_response.json()
            
            if status["status"] == "completed":
                return status["result"]
            elif status["status"] == "failed":
                raise Exception(status["error"])
            
            time.sleep(3)
    
    def create_custom_srt(self, word_timestamps, max_duration=3.0):
        """Create custom SRT with specific timing rules."""
        captions = []
        current_words = []
        current_start = None
        
        for word_data in word_timestamps:
            word = word_data["word"]
            start = word_data["start"]
            end = word_data["end"]
            
            if current_start is None:
                current_start = start
            
            current_words.append(word)
            
            # Check if we should end this caption
            duration = end - current_start
            if (duration >= max_duration or 
                len(current_words) >= 8 or
                word.endswith('.') or word.endswith('!')):
                
                caption_text = ' '.join(current_words)
                captions.append({
                    'start': current_start,
                    'end': end,
                    'text': caption_text
                })
                
                current_words = []
                current_start = None
        
        # Handle remaining words
        if current_words:
            last_word = word_timestamps[-1]
            captions.append({
                'start': current_start,
                'end': last_word["end"],
                'text': ' '.join(current_words)
            })
        
        return self.format_srt(captions)
    
    def format_srt(self, captions):
        """Format captions as SRT content."""
        srt_content = ""
        
        for i, caption in enumerate(captions, 1):
            start_time = self.seconds_to_srt_time(caption['start'])
            end_time = self.seconds_to_srt_time(caption['end'])
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{caption['text']}\n\n"
        
        return srt_content
    
    def seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millis = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

# Usage
processor = EnhancedCaptionProcessor("your_api_key")

# Process audio with custom settings
result = processor.process_audio(
    "https://s3.amazonaws.com/bucket/podcast_episode.wav",
    {
        "model_size": "medium",
        "max_words_per_line": 6,
        "consider_punctuation": True
    }
)

# Create custom SRT with 2.5 second max duration
custom_srt = processor.create_custom_srt(
    result["word_timestamps"], 
    max_duration=2.5
)

print("Enhanced SRT:")
print(custom_srt)
```

### JavaScript: Real-time Caption Preview

```javascript
class CaptionPreview {
  constructor(apiKey, baseUrl = 'http://localhost:8000') {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
    this.headers = {
      'X-API-Key': apiKey,
      'Content-Type': 'application/json'
    };
  }

  async processAudio(audioUrl, config = {}) {
    // Create job
    const response = await fetch(`${this.baseUrl}/v1/ai/enhanced-captions`, {
      method: 'POST',
      headers: this.headers,
      body: JSON.stringify({ audio_url: audioUrl, ...config })
    });
    
    const { job_id } = await response.json();
    
    // Poll for completion
    while (true) {
      const statusResponse = await fetch(
        `${this.baseUrl}/v1/ai/enhanced-captions/${job_id}`,
        { headers: { 'X-API-Key': this.apiKey } }
      );
      
      const status = await statusResponse.json();
      
      if (status.status === 'completed') {
        return status.result;
      } else if (status.status === 'failed') {
        throw new Error(status.error);
      }
      
      await new Promise(resolve => setTimeout(resolve, 3000));
    }
  }

  createTimedCaptions(wordTimestamps, maxWordsPerLine = 6) {
    const captions = [];
    let currentWords = [];
    let currentStart = null;

    for (const wordData of wordTimestamps) {
      const { word, start, end } = wordData;

      if (currentStart === null) {
        currentStart = start;
      }

      currentWords.push(word);

      // End caption conditions
      const shouldEnd = (
        currentWords.length >= maxWordsPerLine ||
        word.match(/[.!?]$/) ||
        (end - currentStart) >= 3.0
      );

      if (shouldEnd) {
        captions.push({
          start: currentStart,
          end: end,
          text: currentWords.join(' ')
        });

        currentWords = [];
        currentStart = null;
      }
    }

    // Handle remaining words
    if (currentWords.length > 0) {
      const lastWord = wordTimestamps[wordTimestamps.length - 1];
      captions.push({
        start: currentStart,
        end: lastWord.end,
        text: currentWords.join(' ')
      });
    }

    return captions;
  }

  renderCaptionPreview(captions, containerId) {
    const container = document.getElementById(containerId);
    container.innerHTML = '';

    captions.forEach((caption, index) => {
      const captionEl = document.createElement('div');
      captionEl.className = 'caption-item';
      captionEl.innerHTML = `
        <div class="caption-timing">
          ${this.formatTime(caption.start)} → ${this.formatTime(caption.end)}
        </div>
        <div class="caption-text">${caption.text}</div>
      `;
      
      container.appendChild(captionEl);
    });
  }

  formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${minutes}:${secs.padStart(4, '0')}`;
  }

  exportSRT(captions) {
    let srt = '';
    
    captions.forEach((caption, index) => {
      const start = this.toSRTTime(caption.start);
      const end = this.toSRTTime(caption.end);
      
      srt += `${index + 1}\n`;
      srt += `${start} --> ${end}\n`;
      srt += `${caption.text}\n\n`;
    });
    
    return srt;
  }

  toSRTTime(seconds) {
    const date = new Date(seconds * 1000);
    const hours = Math.floor(seconds / 3600);
    const mins = date.getUTCMinutes();
    const secs = date.getUTCSeconds();
    const ms = date.getUTCMilliseconds();
    
    return `${hours.toString().padStart(2, '0')}:${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${ms.toString().padStart(3, '0')}`;
  }
}

// Usage
const captionPreview = new CaptionPreview('your_api_key');

document.getElementById('processBtn').addEventListener('click', async () => {
  const audioUrl = document.getElementById('audioUrl').value;
  const maxWords = parseInt(document.getElementById('maxWords').value) || 6;
  
  try {
    document.getElementById('status').textContent = 'Processing...';
    
    const result = await captionPreview.processAudio(audioUrl, {
      model_size: 'base',
      max_words_per_line: maxWords,
      consider_punctuation: true
    });
    
    const captions = captionPreview.createTimedCaptions(
      result.word_timestamps, 
      maxWords
    );
    
    captionPreview.renderCaptionPreview(captions, 'captionPreview');
    
    document.getElementById('downloadSRT').onclick = () => {
      const srt = captionPreview.exportSRT(captions);
      const blob = new Blob([srt], { type: 'text/plain' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'captions.srt';
      a.click();
    };
    
    document.getElementById('status').textContent = 'Completed!';
    
  } catch (error) {
    document.getElementById('status').textContent = `Error: ${error.message}`;
  }
});
```

### React: Caption Editor Component

```jsx
import React, { useState, useEffect } from 'react';

function CaptionEditor({ audioUrl, onCaptionsReady }) {
  const [captions, setCaptions] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [wordTimestamps, setWordTimestamps] = useState([]);
  const [settings, setSettings] = useState({
    maxWordsPerLine: 6,
    maxDuration: 3.0,
    considerPunctuation: true
  });

  const processAudio = async () => {
    setIsProcessing(true);
    
    try {
      const processor = new CaptionPreview('your_api_key');
      const result = await processor.processAudio(audioUrl, {
        model_size: 'base',
        max_words_per_line: settings.maxWordsPerLine,
        consider_punctuation: settings.considerPunctuation
      });
      
      setWordTimestamps(result.word_timestamps);
      regenerateCaptions(result.word_timestamps);
      
    } catch (error) {
      console.error('Caption processing failed:', error);
    } finally {
      setIsProcessing(false);
    }
  };

  const regenerateCaptions = (timestamps = wordTimestamps) => {
    const newCaptions = [];
    let currentWords = [];
    let currentStart = null;

    for (const wordData of timestamps) {
      const { word, start, end } = wordData;

      if (currentStart === null) {
        currentStart = start;
      }

      currentWords.push(word);

      const duration = end - currentStart;
      const shouldEnd = (
        currentWords.length >= settings.maxWordsPerLine ||
        duration >= settings.maxDuration ||
        (settings.considerPunctuation && word.match(/[.!?]$/))
      );

      if (shouldEnd) {
        newCaptions.push({
          id: newCaptions.length,
          start: currentStart,
          end: end,
          text: currentWords.join(' ')
        });

        currentWords = [];
        currentStart = null;
      }
    }

    // Handle remaining words
    if (currentWords.length > 0) {
      const lastWord = timestamps[timestamps.length - 1];
      newCaptions.push({
        id: newCaptions.length,
        start: currentStart,
        end: lastWord.end,
        text: currentWords.join(' ')
      });
    }

    setCaptions(newCaptions);
    if (onCaptionsReady) {
      onCaptionsReady(newCaptions);
    }
  };

  const updateCaption = (id, newText) => {
    setCaptions(prev => prev.map(cap => 
      cap.id === id ? { ...cap, text: newText } : cap
    ));
  };

  const formatTime = (seconds) => {
    const minutes = Math.floor(seconds / 60);
    const secs = (seconds % 60).toFixed(1);
    return `${minutes}:${secs.padStart(4, '0')}`;
  };

  useEffect(() => {
    if (wordTimestamps.length > 0) {
      regenerateCaptions();
    }
  }, [settings]);

  return (
    <div className="caption-editor">
      <div className="controls">
        <button 
          onClick={processAudio} 
          disabled={isProcessing || !audioUrl}
        >
          {isProcessing ? 'Processing...' : 'Generate Captions'}
        </button>
        
        <div className="settings">
          <label>
            Max Words Per Line:
            <input
              type="number"
              min="1"
              max="15"
              value={settings.maxWordsPerLine}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                maxWordsPerLine: parseInt(e.target.value)
              }))}
            />
          </label>
          
          <label>
            Max Duration (seconds):
            <input
              type="number"
              min="1"
              max="8"
              step="0.5"
              value={settings.maxDuration}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                maxDuration: parseFloat(e.target.value)
              }))}
            />
          </label>
          
          <label>
            <input
              type="checkbox"
              checked={settings.considerPunctuation}
              onChange={(e) => setSettings(prev => ({
                ...prev,
                considerPunctuation: e.target.checked
              }))}
            />
            Split on punctuation
          </label>
        </div>
      </div>

      <div className="caption-list">
        {captions.map((caption) => (
          <div key={caption.id} className="caption-item">
            <div className="caption-timing">
              {formatTime(caption.start)} → {formatTime(caption.end)}
            </div>
            <textarea
              value={caption.text}
              onChange={(e) => updateCaption(caption.id, e.target.value)}
              className="caption-text-input"
            />
          </div>
        ))}
      </div>
    </div>
  );
}

export default CaptionEditor;
```

## Performance Optimization

### Model Selection Strategy

```python
def select_optimal_model(audio_duration, quality_requirement):
    """Select the best Whisper model based on requirements."""
    
    if quality_requirement == "preview":
        return "tiny"  # Fastest for quick previews
    elif quality_requirement == "standard":
        if audio_duration < 60:
            return "base"  # Good balance for short audio
        else:
            return "small"  # Better accuracy for longer audio
    elif quality_requirement == "professional":
        if audio_duration < 120:
            return "medium"  # High quality for medium length
        else:
            return "large"   # Best quality for long content
    
    return "base"  # Default safe choice
```

### Batch Processing

```python
async def process_multiple_audio_files(audio_urls, config):
    """Process multiple audio files efficiently."""
    
    # Group by similar characteristics for batch processing
    short_files = [url for url in audio_urls if estimate_duration(url) < 60]
    long_files = [url for url in audio_urls if estimate_duration(url) >= 60]
    
    # Process short files with base model
    short_results = await asyncio.gather(*[
        process_audio_enhanced(url, {**config, "model_size": "base"})
        for url in short_files
    ])
    
    # Process long files with small model for better accuracy
    long_results = await asyncio.gather(*[
        process_audio_enhanced(url, {**config, "model_size": "small"})
        for url in long_files
    ])
    
    return short_results + long_results
```

## Environment Variables

```bash
# Optional: Custom Whisper model cache directory
WHISPER_CACHE_DIR=/path/to/cache

# Optional: Enable GPU acceleration (if available)
WHISPER_DEVICE=cuda

# Optional: Maximum concurrent transcription jobs
MAX_TRANSCRIPTION_JOBS=2
```

## Best Practices

### Audio Quality

1. **Sample Rate**: 16kHz or higher for best results
2. **Format**: WAV, FLAC, or high-quality MP3
3. **Noise**: Minimal background noise improves accuracy
4. **Length**: Avoid extremely long files (>10 minutes)

### Caption Optimization

1. **Reading Speed**: 2-4 words per second max
2. **Line Length**: 6-8 words for social media
3. **Timing**: 2-4 second display duration
4. **Punctuation**: Use for natural breaks

### Model Selection

1. **Tiny**: Quick tests and previews
2. **Base**: Default for most use cases
3. **Small**: Better accuracy for important content
4. **Medium/Large**: Professional quality needs

## Troubleshooting

### Common Issues

**Slow Processing:**
- Use smaller model size for testing
- Check system memory availability
- Verify audio file accessibility

**Poor Timing Accuracy:**
- Use higher quality audio
- Try larger model size
- Enable punctuation consideration

**Memory Errors:**
- Reduce model size
- Process shorter audio segments
- Close other applications

### Quality Validation

```python
def validate_caption_quality(word_timestamps, min_confidence=0.8):
    """Validate caption quality based on confidence scores."""
    
    low_confidence_words = [
        word for word in word_timestamps 
        if word.get('confidence', 1.0) < min_confidence
    ]
    
    if len(low_confidence_words) > len(word_timestamps) * 0.1:
        return {
            'quality': 'poor',
            'recommendation': 'Consider using higher quality audio or larger model',
            'low_confidence_count': len(low_confidence_words)
        }
    
    return {
        'quality': 'good',
        'confidence_score': sum(w.get('confidence', 1.0) for w in word_timestamps) / len(word_timestamps)
    }
```

## Next Steps

- Use enhanced captions with [Video Captions](videos/add_captions.md)
- Integrate with [Topic-to-Video Pipeline](footage-to-video-pipeline.md)
- Combine with [AI Script Generation](ai-script-generation.md)
- Export to video editing software via SRT files

---

*For more examples and advanced usage, see the [examples directory](examples/).*