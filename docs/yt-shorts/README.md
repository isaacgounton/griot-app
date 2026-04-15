# YouTube Shorts Generator Documentation

## Overview

The YouTube Shorts Generator is a comprehensive AI-powered service that transforms long-form YouTube videos into engaging short-form content optimized for social media platforms. This implementation includes all advanced features from the AI-Youtube-Shorts-Generator project with professional-grade enhancements.

## 🚀 Key Features

### **🎯 AI-Powered Highlight Detection**
- **GPT-4 Integration**: Automatically identifies the most engaging segments from video transcriptions
- **Content Analysis**: Analyzes dialogue, emotional peaks, and key insights
- **Customizable Duration**: Supports segments from 5 seconds to 5 minutes
- **Fallback Options**: Custom time segments or manual selection

### **🔊 Advanced Audio Processing**
- **Voice Activity Detection (VAD)**: Precise speaker identification using webrtcvad
- **Speech Enhancement**: Noise reduction and clarity optimization
- **Audio-Visual Correlation**: Combines lip movement analysis with voice activity
- **Multiple Enhancement Levels**: Speech, music, and auto-detection modes

### **👤 Sophisticated Face Detection**
- **DNN-Based Detection**: Uses OpenCV Caffe models for high-accuracy face detection
- **Confidence Scoring**: Filters faces based on detection confidence
- **Multi-Face Tracking**: Supports videos with multiple speakers
- **Fallback System**: Haar cascade classifier as backup

### **📱 Dynamic Face Cropping**
- **Real-Time Tracking**: Smooth face-following across video frames
- **Speaker-Aware Cropping**: Centers on active speaker using audio-visual correlation
- **Intelligent Boundaries**: Prevents crop overflow with smart boundary handling
- **Smooth Transitions**: Reduces jittery movement with center-of-mass tracking

### **🎨 Professional Video Optimization**
- **Platform-Specific Formats**: Optimized for YouTube Shorts, TikTok, Instagram Reels
- **Quality Presets**: Low, medium, high, and ultra quality options
- **Aspect Ratio Optimization**: Perfect 9:16 vertical format
- **Encoding Standards**: H.264/H.265 with AAC audio

### **🔧 Advanced Processing Features**
- **Fade Transitions**: Smooth fade-in/fade-out effects
- **Thumbnail Generation**: Automatic preview thumbnails
- **Quality Verification**: Audio-video sync and integrity checks
- **Processing Analytics**: Comprehensive statistics and metadata

## 🛠️ Technical Architecture

### **Processing Pipeline**
1. **📥 Download**: High-quality YouTube video download with format selection
2. **🎵 Audio Enhancement**: Extract and enhance audio with speech optimization
3. **📝 Transcription**: Whisper-powered transcription with precise timestamps
4. **🤖 AI Analysis**: GPT-4 powered highlight detection and content analysis
5. **✂️ Segment Extraction**: Extract optimal video segments with transitions
6. **👤 Face Detection**: Advanced DNN-based face detection and tracking
7. **📱 Dynamic Cropping**: Real-time vertical cropping with speaker awareness
8. **🎨 Optimization**: Professional encoding for platform specifications
9. **🖼️ Thumbnail Generation**: Create engaging preview thumbnails
10. **☁️ Storage**: Upload to cloud storage with verification

### **Core Components**

#### **Speaker Detection** (`speaker_detection.py`)
```python
from app.utils.yt_shorts.speaker_detection import speaker_detector

# Track speakers in frame with audio correlation
speaker_info = speaker_detector.track_speakers(frame, audio_data, sample_rate)
active_speaker = speaker_detector.get_active_speaker(speaker_info)
```

#### **Dynamic Face Crop** (`face_crop.py`)
```python
from app.utils.yt_shorts.face_crop import face_cropper

# Process video with dynamic face tracking
face_cropper.process_video_with_dynamic_crop(video_path, output_path, audio_path)
```

#### **Enhanced Video Editor** (`video_editor.py`)
```python
from app.utils.yt_shorts.video_editor import video_editor

# Extract audio with enhancement
video_editor.extract_audio_enhanced(video_path, audio_path, quality='high')

# Optimize for YouTube Shorts
video_editor.optimize_for_shorts(video_path, output_path, quality='high')
```

## 📊 Supported Platforms

### **Primary Platforms**
- **YouTube Shorts** - 720x1280, 1080x1920 (9:16 aspect ratio)
- **TikTok** - 720x1280, 1080x1920 (9:16 aspect ratio)
- **Instagram Reels** - 1080x1920 (9:16 aspect ratio)
- **Facebook Reels** - 1080x1920 (9:16 aspect ratio)

### **Secondary Platforms**
- **Snapchat Spotlight** - 1080x1920 (9:16 aspect ratio)
- **Pinterest Idea Pins** - 1080x1920 (9:16 aspect ratio)
- **LinkedIn Video** - 1080x1920 (9:16 aspect ratio)

## 🔧 Configuration

### **Environment Variables**
```env
# Required
API_KEY=your_api_key_here
S3_ACCESS_KEY=your_s3_access_key
S3_SECRET_KEY=your_s3_secret_key
S3_BUCKET_NAME=your_s3_bucket_name
S3_REGION=your_s3_region

# Optional
OPENAI_API_KEY=your_openai_api_key  # For AI highlight detection
S3_ENDPOINT_URL=your_s3_endpoint    # For non-AWS S3 services
REDIS_URL=redis://redis:6379/0      # For job queue
```

### **Model Files**
The following model files are required and automatically loaded:
- `models/yt_shorts/deploy.prototxt` - DNN model architecture
- `models/yt_shorts/res10_300x300_ssd_iter_140000_fp16.caffemodel` - Face detection model
- `models/yt_shorts/haarcascade_frontalface_default.xml` - Haar cascade fallback

## 🎯 Quality Presets

### **Low Quality**
- **CRF**: 28
- **Preset**: fast
- **Bitrate**: 1000k
- **Use Case**: Quick processing, smaller file sizes

### **Medium Quality** (Default)
- **CRF**: 23
- **Preset**: medium
- **Bitrate**: 2500k
- **Use Case**: Balanced quality and processing time

### **High Quality**
- **CRF**: 18
- **Preset**: slow
- **Bitrate**: 5000k
- **Use Case**: Professional quality output

### **Ultra Quality**
- **CRF**: 15
- **Preset**: slower
- **Bitrate**: 8000k
- **Use Case**: Maximum quality for premium content

## 📈 Performance Considerations

### **Processing Time**
- **Low Quality**: ~30-60 seconds per minute of input
- **Medium Quality**: ~1-2 minutes per minute of input
- **High Quality**: ~2-4 minutes per minute of input
- **Ultra Quality**: ~4-8 minutes per minute of input

### **Resource Usage**
- **CPU**: High during video processing and face detection
- **Memory**: 2-4GB depending on video resolution and duration
- **Storage**: Temporary files require 2-3x input video size
- **Network**: Download bandwidth depends on YouTube video quality

### **Optimization Tips**
1. **Use appropriate quality preset** for your use case
2. **Limit max_duration** to reduce processing time
3. **Enable speaker_tracking** only when needed
4. **Use custom time segments** to avoid AI processing overhead
5. **Configure Redis** for better job queue performance

## 🔒 Security & Privacy

### **Data Handling**
- **Temporary Processing**: All processing files are automatically cleaned up
- **No Data Retention**: Videos are not stored permanently on processing servers
- **S3 Security**: All uploads use secure S3 protocols
- **API Authentication**: All endpoints require valid API keys

### **Privacy Features**
- **No User Data Storage**: No personal information is stored
- **Temporary URLs**: S3 URLs can be configured with expiration
- **Secure Processing**: All processing happens in isolated containers
- **GDPR Compliant**: No personal data retention or tracking

## 🚨 Rate Limits & Quotas

### **API Rate Limits**
- **Requests per minute**: 60 per API key
- **Concurrent jobs**: 5 per API key
- **Maximum file size**: 2GB per video
- **Maximum duration**: 2 hours per video

### **Resource Quotas**
- **Daily processing**: 10 hours per API key
- **Monthly storage**: 100GB per account
- **Bandwidth**: 1TB monthly transfer per account

## 📚 Additional Resources

- **[API Reference](api-reference.md)** - Complete API documentation
- **[Examples](examples.md)** - Code examples and tutorials
- **[Troubleshooting](troubleshooting.md)** - Common issues and solutions
- **[Best Practices](best-practices.md)** - Optimization guidelines
- **[Model Information](models.md)** - Details about AI models used

## 🔄 Version History

### **Version 2.0** (Current)
- Complete rewrite with advanced features
- AI-powered highlight detection
- Dynamic face tracking
- Professional video optimization
- Comprehensive quality assurance

### **Version 1.0** (Legacy)
- Basic YouTube Shorts generation
- Simple face detection
- Limited customization options
- Basic quality presets

## 🤝 Support

For technical support, feature requests, or bug reports:
- **Documentation**: Check this documentation first
- **API Issues**: Verify your API key and request format
- **Processing Issues**: Check the troubleshooting guide
- **Feature Requests**: Submit enhancement requests through proper channels

---

*This documentation covers the comprehensive YouTube Shorts Generator implementation. For the most up-to-date information, please refer to the API documentation and examples.*