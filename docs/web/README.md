# Web UI Documentation

The Griot includes a modern web interface for manual video creation, AI-powered content generation, and job monitoring.

## Overview

The Web UI provides:
- **Manual Video Creation**: Create videos with custom scenes, text, and timing
- **AI Research Mode**: Generate videos from topics with automated script generation
- **Real-time Job Tracking**: Monitor video processing with live status updates
- **Video Library**: Manage and download all created videos
- **TTS Voice Selection**: Choose from Kokoro and Edge TTS providers

## Access

### URL

```
http://localhost:8000/ui
```

### Authentication

The Web UI requires API key authentication:

1. Navigate to `/ui`
2. Enter your API key when prompted
3. Your session will be authenticated for subsequent requests

### Development Build

The Web UI is built with React and requires compilation:

```bash
cd frontend
npm install
npm run build
```

The built frontend will be served at `/ui`.

## Features

### 1. VideoCreator Component

Manual video creation with scene-by-scene control.

**Features:**
- Add/remove/edit scenes
- Set scene duration and text
- Configure search terms for stock footage
- Choose voice provider and voice
- Set video resolution and orientation
- Configure caption styling

**Usage:**
1. Navigate to VideoCreator tab
2. Add scenes with text content
3. Set duration for each scene
4. Configure video settings
5. Click "Create Video"
6. Monitor progress in real-time

**Configuration Options:**
- Voice Provider: Kokoro, Edge TTS, or KittenTTS
- Voice Name: Select specific voice from chosen provider
- Resolution: 1080x1920 (portrait), 1920x1080 (landscape), 1080x1080 (square)
- Add Captions: Toggle caption overlay
- Caption Style: classic, viral_bounce, typewriter, fade_in

### 2. AI Research Mode

Automated video generation from topics.

**Features:**
- Generate scripts from topics using AI
- Automatic scene breakdown
- Smart video search and selection
- Automatic TTS and caption generation
- One-click video creation

**Usage:**
1. Enter topic or research question
2. Choose video duration
3. Select voice provider and voice
4. Configure video settings
5. Click "Generate Video"
6. AI creates script, scenes, and final video

**Script Types:**
- `facts`: Educational facts and information
- `story`: Narrative storytelling
- `tutorial`: How-to and instructional content
- `news`: News and current events
- `entertainment`: Entertainment and viral content

### 3. Job Monitor

Real-time job status tracking.

**Features:**
- Live status updates
- Progress bars for long-running jobs
- Error messages and diagnostics
- Job result display
- Download links for completed jobs

**Job States:**
- `pending`: Job is queued
- `processing`: Job is being processed
- `completed`: Job completed successfully
- `failed`: Job failed with error

### 4. Video Library

Manage all created videos.

**Features:**
- List all created videos
- Preview thumbnails
- Download videos
- View job details
- Delete old videos
- Filter by status/date

### 5. Voice Selector

Choose from available TTS voices.

**Supported Providers:**

**Kokoro TTS:**
- `af_bella`: Female voice (US English)
- `am_michael`: Male voice (US English)
- `bf_emma`: Female voice (British English)
- `bm_george`: Male voice (British English)
- And more regional variants

**Edge TTS:**
- `en-US-AriaNeural`: Female (US)
- `en-US-GuyNeural`: Male (US)
- `en-GB-SoniaNeural`: Female (UK)
- `en-GB-RyanNeural`: Male (UK)
- And more languages/accents

**KittenTTS:**
- `expr-voice-2-m/f`: Expressive voice 2 (male/female)
- `expr-voice-3-m/f`: Expressive voice 3 (male/female)
- `expr-voice-4-m/f`: Expressive voice 4 (male/female)
- `expr-voice-5-m/f`: Expressive voice 5 (male/female)

## API Integration

### Backend Endpoints

The Web UI communicates with these backend endpoints:

**Video Creation:**
```bash
POST /api/v1/ai/scenes-to-video
Content-Type: application/json

{
  "scenes": [
    {
      "text": "Scene text here",
      "duration": 3.0,
      "searchTerms": ["term1", "term2"]
    }
  ],
  "voice_provider": "kokoro",
  "voice_name": "af_bella",
  "add_captions": true,
  "caption_style": "viral_bounce"
}
```

**AI Research:**
```bash
POST /api/v1/ai/footage-to-video
Content-Type: application/json

{
  "topic": "amazing space facts",
  "script_type": "facts",
  "voice_provider": "kokoro",
  "voice_name": "af_bella"
}
```

**Job Status:**
```bash
GET /api/v1/jobs/{job_id}/status
```

**Voice List:**
```bash
GET /api/v1/audio/providers
```

## Usage Examples

### Create Manual Video

1. Open VideoCreator tab
2. Click "Add Scene"
3. Enter scene text: "Welcome to this amazing video"
4. Set duration: 3.0 seconds
5. Add search terms: "welcome", "amazing"
6. Repeat for additional scenes
7. Select voice: Kokoro → af_bella
8. Click "Create Video"
9. Monitor progress in Jobs tab
10. Download video when complete

### Create AI Video

1. Open AI Research tab
2. Enter topic: "The future of AI technology"
3. Select script type: "facts"
4. Set duration: 60 seconds
5. Select voice: Edge → en-US-AriaNeural
6. Click "Generate Video"
7. AI generates script automatically
8. Video processes automatically
9. Download when complete

### Monitor Job Progress

1. Navigate to Jobs tab
2. See all active and recent jobs
3. Click job for details
4. View real-time progress
5. See errors if any
6. Download result when complete

## Component Architecture

### Frontend Structure

```
frontend/
├── src/
│   ├── components/
│   │   ├── VideoCreator/
│   │   │   ├── index.jsx
│   │   │   ├── SceneEditor.jsx
│   │   │   ├── VoiceSelector.jsx
│   │   │   └── VideoSettings.jsx
│   │   ├── AIResearch/
│   │   │   ├── index.jsx
│   │   │   ├── TopicInput.jsx
│   │   │   └── ScriptGenerator.jsx
│   │   ├── JobMonitor/
│   │   │   ├── index.jsx
│   │   │   ├── JobList.jsx
│   │   │   └── JobDetails.jsx
│   │   └── VideoLibrary/
│   │       ├── index.jsx
│   │       ├── VideoGrid.jsx
│   │       └── VideoCard.jsx
│   ├── services/
│   │   └── api.js
│   └── App.jsx
```

### State Management

The Web UI uses React hooks for state management:
- `useState`: Component-level state
- `useEffect`: API calls and side effects
- `useContext`: Global state (API key, authentication)

### API Service

```javascript
// services/api.js
const API_BASE = 'http://localhost:8000/api/v1';

export const createVideo = async (scenes, config) => {
  const response = await fetch(`${API_BASE}/ai/scenes-to-video`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': getApiKey()
    },
    body: JSON.stringify({ scenes, ...config })
  });
  return response.json();
};

export const getJobStatus = async (jobId) => {
  const response = await fetch(`${API_BASE}/jobs/${jobId}/status`, {
    headers: {
      'X-API-Key': getApiKey()
    }
  });
  return response.json();
};
```

## Development

### Local Development

```bash
# Frontend development server with hot reload
cd frontend
npm install
npm run dev

# Backend development server
cd ..
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Build

```bash
# Build frontend
cd frontend
npm run build

# Serve with backend
cd ..
docker-compose up --build
```

### Environment Variables

```bash
# Frontend
VITE_API_BASE_URL=http://localhost:8000
VITE_APP_NAME=Griot Web UI

# Backend
API_KEY=your_api_key_here
```

## Troubleshooting

### Common Issues

**Authentication Failed:**
- Verify API key is correct
- Check backend is running
- Clear browser cache and cookies

**Video Creation Fails:**
- Check all required fields are filled
- Verify voice provider/voice combination is valid
- Check browser console for errors
- Ensure backend services are running

**Job Status Not Updating:**
- Refresh the page
- Check WebSocket connection
- Verify backend job queue is running

**Build Errors:**
- Clear node_modules and reinstall: `rm -rf node_modules && npm install`
- Check Node.js version (requires 18+)
- Verify all dependencies are installed

### Browser Compatibility

**Supported Browsers:**
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

**Required Features:**
- ES6 JavaScript
- Fetch API
- WebSocket API
- CSS Grid/Flexbox

## Best Practices

### For Users

1. **Start Simple**: Begin with short videos (2-3 scenes)
2. **Test Voices**: Preview different voices before creating
3. **Monitor Jobs**: Keep an eye on job progress
4. **Download Results**: Download videos promptly (storage limits)
5. **Provide Feedback**: Report issues and feature requests

### For Developers

1. **Component Reusability**: Create reusable components
2. **Error Handling**: Handle API errors gracefully
3. **Loading States**: Show loading indicators during API calls
4. **User Feedback**: Provide clear feedback for actions
5. **Performance**: Optimize for large video libraries

## Future Enhancements

Planned improvements:
- **Drag-and-Drop**: Reorder scenes with drag-and-drop
- **Video Preview**: Preview videos before download
- **Batch Operations**: Create multiple videos at once
- **Templates**: Save and reuse video templates
- **Collaboration**: Share videos with team members
- **Analytics**: View video creation statistics

## Resources

- **React Documentation**: [react.dev](https://react.dev)
- **FastAPI Documentation**: [fastapi.tiangolo.com](https://fastapi.tiangolo.com)
- **Main API Docs**: [../README.md](../README.md)

---

*Last updated: January 2025*
