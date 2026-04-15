# Video Routes Documentation

This section documents all video-related endpoints provided by the Media Master API following OpenAI conventions.

## Available Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/v1/videos/generate | POST | Generate videos from text prompts using LTX-Video |
| /api/v1/videos/from_image | POST | Generate videos from images with text prompts using LTX-Video |
| /api/v1/videos/modern-text-overlay | POST | Add customizable text overlays to videos |
| /api/v1/videos/modern-presets | GET | Get available text overlay presets |
| /api/v1/videos/modern-preset/{preset_name} | POST | Add text overlay using a preset |
| /api/v1/videos/preview | POST | Preview text overlay effects |
| /api/v1/videos/all-presets | GET | Get all available text overlay presets |
| /api/v1/videos/concatenate | POST | Concatenate multiple videos into a single video |
| /api/v1/videos/add-audio | POST | Add audio to a video with volume control |
| /api/v1/videos/add-captions | POST | Add advanced captions with styling and animations |
| /api/v1/videos/thumbnails | POST | Generate thumbnails from videos |
| /api/v1/videos/clips | POST | Create video clips from source videos |
| /api/v1/videos/frames | POST | Extract frames from videos |
| /api/v1/videos/advanced/tts-captioned-video | POST | Create videos with TTS and captions |
| /api/v1/videos/advanced/colorkey-overlay | POST | Apply color key overlay effects |
| /api/v1/videos/ | GET | List all videos |
| /api/v1/videos/{video_id} | GET | Get video information |
| /api/v1/videos/{video_id} | PUT | Update video metadata |
| /api/v1/videos/{video_id} | DELETE | Delete a video |
| /api/v1/videos/{video_id}/download | GET | Download video file |
| /api/v1/videos/stats/overview | GET | Get video statistics overview |
| /api/v1/videos/caption-styles/presets | GET | Get caption style presets |
| /api/v1/videos/caption-styles/presets/{style_name} | GET | Get specific caption style preset |
| /api/v1/videos/caption-styles/apply-preset | POST | Apply caption style preset |
| /api/v1/videos/caption-styles/recommendations | GET | Get caption style recommendations |
| /api/v1/videos/caption-styles/best-practices | GET | Get caption best practices |
| /api/v1/jobs/{job_id}/status | GET | Get the status of any video processing job |

## Common Use Cases

### Video Concatenation

The video concatenation endpoint allows you to join multiple video files into a single continuous video. This is useful for:

- Combining multiple video clips into a single file
- Creating compilations from shorter video segments
- Merging different parts of a video that were recorded separately
- Creating sequential video content from separate scenes or shots

### Video Merge

The video merge endpoint combines video concatenation with audio overlay in a single operation. This is useful for:

- Creating complete video productions with background music
- Merging multiple clips with synchronized soundtrack
- Building social media content with smooth transitions and audio
- Creating professional video compilations with audio overlay
- Combining video segments with fade effects and background music
- One-step creation of finished videos from multiple sources

### Audio Addition

The add audio endpoint allows you to add background music or other audio to videos. This is useful for:

- Adding background music to silent videos
- Replacing or enhancing existing audio tracks
- Adding voiceovers to video content
- Creating multimedia presentations with synchronized audio
- Using YouTube audio sources directly with videos

### Video Captions

The video captions endpoint provides advanced captioning with modern styling and animation effects. This is useful for:

- Creating TikTok-style viral content with bouncing text effects
- Adding professional subtitles with precise timing
- Auto-generating captions from video audio using AI transcription
- Creating karaoke-style word-by-word highlighting
- Adding multi-language caption support with text replacements
- Implementing accessibility features with customizable positioning
- Creating engaging social media content with gradient colors and glow effects

### Text Overlay

The text overlay endpoints allow you to add professional text overlays to videos with advanced styling options. This is useful for:

- Adding titles and headers to video content
- Creating subtitles and captions for accessibility
- Adding watermarks and branding to videos
- Creating engaging social media content with text
- Adding call-to-action messages and alerts
- Using predefined presets for quick, professional results

## Supported Video Formats

The Media Master API supports various video formats for both input and output:

- MP4 (.mp4)
- WebM (.webm)
- AVI (.avi)
- MOV (.mov)
- MKV (.mkv)

## Error Handling

All video endpoints follow standard HTTP status codes:

- 200: Successful operation
- 400: Bad request (invalid parameters)
- 401: Unauthorized (invalid API key)
- 404: Resource not found
- 422: Validation error (invalid input parameters)
- 429: Rate limit exceeded
- 500: Internal server error

Detailed error messages are provided in the response body for debugging and error resolution.
