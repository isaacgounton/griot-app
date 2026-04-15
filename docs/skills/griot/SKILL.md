---
name: griot
version: 1.4.0
description: "Griot — complete media production API with 29 CLI tools. Video creation (scenes, topics, AI generation, YouTube Shorts), image generation, text-to-speech (300+ voices), captions, document conversion, media download, transcription, format conversion, vision analysis, LLM chat (30+ providers via AnyLLM), content repurposing (video-to-blog, viral content), and media library. All endpoints tested against live instance. Use when user wants to create, edit, analyze, convert, or publish any media content."
metadata: {"openclaw":{"emoji":"🎬","homepage":"https://github.com/isaacgounton/griot","os":["darwin","linux","win32"],"requires":{"bins":["curl","jq"],"env":["DAHO_API_KEY"]},"primaryEnv":"DAHO_API_KEY","install":[{"id":"jq-brew","kind":"brew","formula":"jq","bins":["jq"],"label":"Install jq via Homebrew","os":["darwin"]},{"id":"jq-apt","kind":"shell","command":"sudo apt-get install -y jq","bins":["jq"],"label":"Install jq via apt","os":["linux"]}]}}
---

# Griot v1.4.0

Complete media production API with 25+ CLI tools. Create videos, generate images, text-to-speech, captions, documents, downloads, transcription, vision analysis, LLM chat, content repurposing, social scheduling, and more.

## API Setup

Deploy Griot or use a hosted instance. Set your credentials:

```bash
export DAHO_URL="http://localhost:8000"   # Your Griot instance
export DAHO_API_KEY="your_api_key"        # Your API key
```

### Runtime Requirements

| Type | Name | Required |
|------|------|----------|
| Env | `DAHO_API_KEY` | Yes |
| Env | `DAHO_URL` | Yes (default: http://localhost:8000) |
| Bin | `curl` | Yes |
| Bin | `jq` | Yes |

## Operations & Scripts

### 1. Create Video from Scenes (`scripts/scenes-to-video.sh`)

Build complete videos from scene-based scripts with TTS narration, stock visuals, captions, and music.

**Usage:**
```bash
scripts/scenes-to-video.sh scenes.json
scripts/scenes-to-video.sh scenes.json --voice fr-FR-HenriNeural --provider edge --lang fr
scripts/scenes-to-video.sh scenes.json --music epic --captions viral_bounce --resolution 1080x1920
scripts/scenes-to-video.sh scenes.json --motion ken_burns --footage pixabay --media-type image
scripts/scenes-to-video.sh scenes.json --footage ai_generated --ai-video-provider wavespeed
scripts/scenes-to-video.sh scenes.json --footage ai_generated --media-type image --ai-image-provider pollinations
```

**Scene file format (JSON):**
```json
[
  {"text": "Your narration for scene 1", "search_terms": ["keyword1", "keyword2"], "duration": 10},
  {"text": "Narration for scene 2", "search_terms": ["keyword3"], "duration": 15}
]
```

**Options:**
- `--provider PROVIDER` — TTS provider: `edge`, `kokoro`, `kitten`, `piper`, `pollinations` (default: edge)
- `--voice VOICE` — Voice name (default: en-US-GuyNeural)
- `--speed N` — Speech speed 0.5-2.0 (default: 1.0)
- `--music MOOD` — Background music: `epic`, `chill`, `sad`, `happy`, `upbeat`
- `--captions STYLE` — Caption style: `viral_bounce`, `karaoke`, `standard_bottom`, `highlight`
- `--caption-color HEX` — Caption color (default: #FFFFFF)
- `--resolution RES` — `1080x1920` (portrait) or `1920x1080` (landscape)
- `--motion EFFECT` — `ken_burns`, `zoom`, `pan`, `fade`
- `--lang CODE` — Language code (default: en)
- `--footage SOURCE` — Media source: `pexels`, `pixabay`, `ai_generated` (default: pexels)
- `--media-type TYPE` — `video` (stock clips) or `image` (images with motion effects) (default: video)
- `--ai-video-provider PROV` — AI video provider: `wavespeed`, `comfyui` (when footage=ai_generated)
- `--ai-image-provider PROV` — AI image provider: `together`, `pollinations` (when media-type=image + ai_generated)

**Recommended voices:**
- English: `en-US-GuyNeural`, `en-US-JennyNeural`, `en-GB-RyanNeural`
- French: `fr-FR-HenriNeural`, `fr-FR-DeniseNeural`
- Spanish: `es-ES-AlvaroNeural`, `es-MX-DaliaNeural`
- Portuguese: `pt-BR-AntonioNeural`

### 2. Auto Video from Topic (`scripts/topic-to-video.sh`)

Give it a topic — get a complete video. AI handles script, TTS, visuals, and captions.

**Usage:**
```bash
scripts/topic-to-video.sh "The history of jazz music"
scripts/topic-to-video.sh "Climate change effects" --lang fr --duration 90
scripts/topic-to-video.sh "How computers work" --type educational --voice en-US-GuyNeural
scripts/topic-to-video.sh "Ancient Egypt" --footage pixabay --media-type image
scripts/topic-to-video.sh "Future of AI" --footage ai_generated --ai-video-provider wavespeed
```

**Options:**
- `--lang CODE` — Language (default: en)
- `--duration N` — Target duration in seconds (default: 60)
- `--type TYPE` — Script type: `educational`, `facts`, `story`, `promotional`
- `--provider PROVIDER` — TTS provider (default: edge)
- `--voice VOICE` — TTS voice name
- `--footage SOURCE` — Media source: `pexels`, `pixabay`, `unsplash`, `ai_generated` (default: pexels)
- `--media-type TYPE` — `video` or `image` (default: video)
- `--ai-video-provider PROV` — AI video: `modal_video`, `wavespeed`, `comfyui` (when footage=ai_generated)

### 3. Text-to-Speech (`scripts/tts.sh`)

Convert text to speech with multiple providers and 300+ voices.

**Usage:**
```bash
scripts/tts.sh "Hello world"
scripts/tts.sh "Bonjour le monde" --provider edge --voice fr-FR-HenriNeural
scripts/tts.sh "Welcome" --provider kokoro --voice af_bella --speed 0.9
scripts/tts.sh "Read this file" --file script.txt --output narration.mp3
```

**Options:**
- `--provider PROVIDER` — `edge` (300+ voices), `kokoro` (natural), `kitten` (fast), `pollinations`
- `--voice VOICE` — Voice name
- `--speed N` — Speed 0.5-2.0 (default: 1.0)
- `--format FORMAT` — `mp3`, `wav`, `ogg`, `aac` (default: mp3)
- `--output FILE` — Output filename
- `--file FILE` — Read text from file instead of argument

**Providers & best voices:**

| Provider | Voices | Languages | Best For |
|----------|--------|-----------|----------|
| Edge TTS | 300+ | 40+ | Best language coverage |
| Kokoro | 15+ | EN, FR, ES | Most natural quality |
| KittenTTS | 8 | EN | Ultra-fast, lightweight |
| Pollinations | 6 | EN | alloy/echo/nova/onyx/fable/shimmer |

### 4. Generate AI Images (`scripts/image.sh`)

Generate images from text prompts using Pollinations AI (Flux model).

**Usage:**
```bash
scripts/image.sh "A sunset over the ocean"
scripts/image.sh "Yoruba deity Olorun" --width 1080 --height 1920
scripts/image.sh "Product photo" --width 1920 --height 1080 --enhance
scripts/image.sh "Logo design" --output logo.png --seed 42
```

**Options:**
- `--width N` — Width 256-2048 (default: 1024)
- `--height N` — Height 256-2048 (default: 1024)
- `--model MODEL` — Model name (default: flux)
- `--enhance` — AI-improve the prompt
- `--seed N` — Reproducibility seed
- `--nologo` — Remove watermark
- `--output FILE` — Output filename

### 5. Generate Scripts (`scripts/generate-script.sh`)

AI-powered script generation for videos.

**Usage:**
```bash
scripts/generate-script.sh "The solar system"
scripts/generate-script.sh "Yoruba creation mythology" --lang fr --type educational
scripts/generate-script.sh "5 facts about AI" --type facts --style dramatic --duration 90
```

**Options:**
- `--lang CODE` — Language (default: en)
- `--type TYPE` — `educational`, `facts`, `story`, `promotional`
- `--style STYLE` — `engaging`, `formal`, `casual`, `dramatic`
- `--duration N` — Target duration in seconds
- `--audience TEXT` — Target audience description

### 6. Search Stock Media (`scripts/stock-search.sh`)

Search Pexels and Pixabay for free stock videos and images.

**Usage:**
```bash
scripts/stock-search.sh "African landscape" --type video
scripts/stock-search.sh "technology abstract" --type image --count 10
scripts/stock-search.sh "ocean waves" --type video --orientation portrait
```

**Options:**
- `--type TYPE` — `video` or `image` (default: video)
- `--count N` — Number of results (default: 5)
- `--orientation ORI` — `landscape`, `portrait`, `square`

### 7. Merge Videos (`scripts/merge.sh`)

Combine multiple videos into one with transitions.

**Usage:**
```bash
scripts/merge.sh url1 url2 url3
scripts/merge.sh url1 url2 --transition dissolve --duration 1.0
scripts/merge.sh --file urls.txt --transition fade
```

**Options:**
- `--transition TYPE` — `none`, `fade`, `dissolve`, `slide`, `wipe` (default: dissolve)
- `--duration N` — Transition duration in seconds (default: 0.5)
- `--file FILE` — Read URLs from file (one per line)

### 8. Add Captions (`scripts/add-captions.sh`)

Add styled captions/subtitles to any video.

**Usage:**
```bash
scripts/add-captions.sh "https://s3.example.com/video.mp4"
scripts/add-captions.sh VIDEO_URL --style karaoke --color "#FFD700"
scripts/add-captions.sh VIDEO_URL --style viral_bounce --font Montserrat --size 42
scripts/add-captions.sh VIDEO_URL --lang fr --position bottom_center
```

**Options:**
- `--style STYLE` — `classic`, `karaoke`, `highlight`, `underline`, `word_by_word`, `viral_bounce`
- `--font FAMILY` — Font family name
- `--size N` — Font size
- `--bold` — Bold text
- `--color HEX` — Text color (default: #FFFFFF)
- `--highlight HEX` — Word highlight color
- `--outline HEX` — Outline color
- `--position POS` — `bottom_center`, `top_center`, `center`, etc.
- `--lang CODE` — Language for auto-detection

### 9. Add Audio to Video (`scripts/add-audio.sh`)

Mix, replace, or overlay audio on video.

**Usage:**
```bash
scripts/add-audio.sh VIDEO_URL AUDIO_URL
scripts/add-audio.sh VIDEO_URL AUDIO_URL --mode mix --volume 0.15
scripts/add-audio.sh VIDEO_URL AUDIO_URL --mode replace --fade-in 2 --fade-out 3
```

**Options:**
- `--mode MODE` — `replace`, `mix`, `overlay` (default: mix)
- `--volume N` — Audio volume 0.0-1.0 (default: 0.3)
- `--video-volume N` — Video volume 0.0-1.0 (default: 1.0)
- `--fade-in N` — Fade in seconds
- `--fade-out N` — Fade out seconds

### 10. Research (`scripts/research.sh`)

Search the web or news for information.

**Usage:**
```bash
scripts/research.sh "Yoruba mythology Olorun"
scripts/research.sh "latest AI news" --type news --lang fr
scripts/research.sh "climate change data 2025" --type web --count 10
```

**Options:**
- `--type TYPE` — `web` or `news` (default: web)
- `--lang CODE` — Language filter
- `--count N` — Max results

### 11. Social Media Scheduling (`scripts/schedule-post.sh`)

Schedule content to social media via Postiz integration.

**Usage:**
```bash
scripts/schedule-post.sh "Check out our new video!" --integrations ID1,ID2
scripts/schedule-post.sh "New episode!" --integrations ID1 --media VIDEO_URL --now
scripts/schedule-post.sh "Coming soon" --integrations ID1,ID2 --date "2026-03-01T10:00:00Z"
scripts/schedule-post.sh --list-integrations     # List available integrations
scripts/schedule-post.sh --generate "AI news"    # Generate content with AI
```

**Options:**
- `--integrations IDS` — Comma-separated integration IDs (use `--list-integrations` to discover)
- `--media URL` — Attach video/image URL
- `--now` — Post immediately
- `--date ISODATE` — Schedule for specific date/time
- `--draft` — Save as draft
- `--list-integrations` — List available Postiz integrations
- `--generate TOPIC` — Generate social media content with AI

### 12. Job Status (`scripts/job-status.sh`)

Check status of any async job.

**Usage:**
```bash
scripts/job-status.sh JOB_ID
scripts/job-status.sh JOB_ID --wait
scripts/job-status.sh JOB_ID --wait --interval 5
```

**Options:**
- `--wait` — Poll until completion
- `--interval N` — Poll interval in seconds (default: 10)

### 13. Media Download (`scripts/download.sh`)

Download media from YouTube, Vimeo, TikTok, Twitter, and 1000+ sites via yt-dlp.

**Usage:**
```bash
scripts/download.sh "https://www.youtube.com/watch?v=abc123"
scripts/download.sh "https://tiktok.com/@user/video/123" --format mp4
scripts/download.sh "https://youtube.com/watch?v=xyz" --subtitles --thumbnail
```

**Options:**
- `--format FORMAT` — Output format (mp4, mp3, wav, etc.)
- `--subtitles` — Extract subtitles
- `--thumbnail` — Download thumbnail
- `--cookies FILE` — Cookie file for restricted content

### 14. Audio/Video Transcription (`scripts/transcribe.sh`)

Whisper-based transcription with SRT/VTT subtitle output.

**Usage:**
```bash
scripts/transcribe.sh recording.mp3
scripts/transcribe.sh "https://example.com/audio.wav" --lang fr --format srt
```

**Options:**
- `--lang CODE` — Language (auto-detect if omitted)
- `--format FORMAT` — Output: text, srt, vtt, json

### 15. Media Format Conversion (`scripts/convert.sh`)

Convert between video, audio, and image formats.

**Usage:**
```bash
scripts/convert.sh video.mp4 --to mp3
scripts/convert.sh "https://example.com/video.webm" --to mp4 --quality high
scripts/convert.sh image.png --to jpg
```

**Options:**
- `--to FORMAT` — Target format (required): mp4, mp3, wav, webm, gif, png, jpg, etc.
- `--quality LEVEL` — low, medium, high

### 16. Document Processing (`scripts/document.sh`)

Convert PDFs, DOCX, PPTX, HTML, EPUB to markdown/JSON, or extract structured data with AI.

**Usage:**
```bash
scripts/document.sh report.pdf
scripts/document.sh "https://example.com/doc.pdf" --mode marker --output-format json
scripts/document.sh invoice.pdf --mode extract --prompt "Extract total amount and date"
scripts/document.sh presentation.pptx --mode markdown
scripts/document.sh scan.pdf --mode marker --ocr
```

**Modes:**
- `--mode marker` — Convert to markdown/json/html using Marker (default)
- `--mode markdown` — Convert using MarkItDown
- `--mode extract` — Extract structured data with AI (LangExtract)

**Options:**
- `--output-format FMT` — markdown, json, html, chunks (marker mode)
- `--ocr` — Force OCR (marker mode)
- `--schema FILE` — JSON schema for extraction (extract mode)
- `--prompt TEXT` — Extraction instruction (extract mode)

### 17. Text Overlay on Video (`scripts/text-overlay.sh`)

Add custom text over video with full styling control.

**Usage:**
```bash
scripts/text-overlay.sh VIDEO_URL "TITLE TEXT"
scripts/text-overlay.sh VIDEO_URL "Subscribe!" --position bottom_center --font-size 64 --color "#FFD700"
scripts/text-overlay.sh VIDEO_URL "Chapter 1" --start 0 --duration 5 --bg-color "#000000" --bg-opacity 0.5
```

**Options:**
- `--font-size N` — Font size
- `--color HEX` — Text color
- `--font FAMILY` — Font family
- `--position POS` — 9 positions (top/center/bottom + left/center/right)
- `--bg-color HEX` — Background box color
- `--bg-opacity N` — Background opacity 0.0-1.0
- `--start N` — Start time in seconds
- `--duration N` — Display duration

### 18. Extract Video Clips (`scripts/clips.sh`)

Extract segments by time or AI-powered content search.

**Usage:**
```bash
scripts/clips.sh VIDEO_URL --start 10 --end 30
scripts/clips.sh VIDEO_URL --query "the most exciting moment"
scripts/clips.sh VIDEO_URL --start 60 --end 120 --format webm --quality high
```

**Options:**
- `--start N` / `--end N` — Manual time range (seconds)
- `--query TEXT` — AI content search (auto-detect best segment)
- `--format FMT` — mp4, webm, avi, mov, mkv
- `--quality LVL` — low, medium, high

### 19. YouTube Shorts Creator (`scripts/yt-shorts.sh`)

Auto-detect highlights, crop to vertical, speaker tracking, and audio enhancement.

**Usage:**
```bash
scripts/yt-shorts.sh "https://youtube.com/watch?v=abc123"
scripts/yt-shorts.sh "https://youtube.com/watch?v=abc123" --quality high --tracking --fade
scripts/yt-shorts.sh "https://youtube.com/watch?v=abc123" --start 60 --end 120 --thumbnail
```

**Options:**
- `--quality LVL` — low, medium, high, ultra
- `--tracking` — Speaker/face tracking
- `--audio-enhance MODE` — speech, music, auto
- `--fade` — Smooth fade transitions
- `--thumbnail` — Generate thumbnail
- `--start N` / `--end N` — Custom time range
- `--cookies FILE` — Cookie file for restricted videos

### 20. AI Video Generation (`scripts/video-generate.sh`)

Generate video from text prompt using AI models.

**Usage:**
```bash
scripts/video-generate.sh "A cat playing piano"
scripts/video-generate.sh "Ocean waves at sunset" --provider pollinations --audio
scripts/video-generate.sh "A timelapse of flowers blooming" --width 512 --height 512
```

**Options:**
- `--provider PROV` — ltx_video, wavespeed, comfyui, pollinations (default: pollinations)
- `--width N` / `--height N` — Dimensions (256-1024)
- `--frames N` — Frame count (1-257)
- `--seed N` — Reproducibility
- `--negative TEXT` — Negative prompt
- `--audio` — Generate with audio (pollinations)

### 21. Image-to-Video (`scripts/image-to-video.sh`)

Animate static images with motion effects, optional narration and music.

**Usage:**
```bash
scripts/image-to-video.sh IMAGE_URL --motion ken_burns
scripts/image-to-video.sh IMAGE_URL --narration "This is ancient Ife" --tts-provider edge --tts-voice fr-FR-HenriNeural
scripts/image-to-video.sh IMAGE_URL --music epic --captions viral_bounce
```

**Options:**
- `--motion EFFECT` — ken_burns, zoom, pan, fade
- `--narration TEXT` — Add TTS narration
- `--music MOOD` — Background music mood
- `--tts-provider` / `--tts-voice` — Voice configuration
- `--captions STYLE` — Caption style

### 22. Image Enhancement (`scripts/enhance-image.sh`)

Remove AI artifacts, improve colors, add effects.

**Usage:**
```bash
scripts/enhance-image.sh IMAGE_URL
scripts/enhance-image.sh IMAGE_URL --color --contrast
scripts/enhance-image.sh IMAGE_URL --grain --vintage --format jpg --quality 95
```

**Options:**
- `--color` — Enhance colors
- `--contrast` — Improve contrast
- `--grain` — Film grain effect
- `--vintage` — Vintage effect
- `--format FMT` — jpg, png, webp
- `--quality N` — 1-100

### 23. Vision Analysis (`scripts/vision.sh`)

Analyze images with AI vision — describe, OCR, answer questions.

**Usage:**
```bash
scripts/vision.sh "https://example.com/photo.jpg"
scripts/vision.sh IMAGE_URL --prompt "What objects are in this image?"
scripts/vision.sh IMAGE_URL --prompt "Extract all text from this image" --model claude
```

**Options:**
- `--prompt TEXT` — Question (default: "Describe this image in detail")
- `--model MODEL` — Vision model

### 24. Web Screenshot (`scripts/screenshot.sh`)

Capture screenshots of any web page.

**Usage:**
```bash
scripts/screenshot.sh "https://example.com"
scripts/screenshot.sh "https://example.com" --device mobile --output mobile.png
scripts/screenshot.sh "https://example.com" --full-page --format jpeg --quality 90
```

**Options:**
- `--device DEVICE` — desktop, mobile, tablet
- `--full-page` — Capture full scrollable page
- `--format FMT` — png, jpeg
- `--quality N` — JPEG quality
- `--width N` / `--height N` — Viewport size
- `--output FILE` — Save to file

### 25. Viral Content Generator (`scripts/viral-content.sh`)

Generate X threads, multi-platform posts, blog content, and hashtags from video.

**Usage:**
```bash
scripts/viral-content.sh VIDEO_URL
scripts/viral-content.sh VIDEO_URL --platforms twitter,instagram,linkedin
scripts/viral-content.sh VIDEO_URL --threads 8
```

**Options:**
- `--platforms LIST` — Target platforms
- `--threads N` — Max thread posts
- `--cookies FILE` — Cookie file

### 26. Video-to-Blog (`scripts/video-to-blog.sh`)

Convert any video into a full blog post with screenshots and social content.

**Usage:**
```bash
scripts/video-to-blog.sh VIDEO_URL
scripts/video-to-blog.sh VIDEO_URL --social --screenshots
```

**Options:**
- `--social` — Include social media posts
- `--screenshots` — Include video screenshots
- `--cookies FILE` — Cookie file

### 27. LLM Chat (`scripts/chat.sh`)

Chat with 30+ AI providers via AnyLLM streaming. Supports OpenAI, Groq, Anthropic, Mistral, and more.

**Usage:**
```bash
scripts/chat.sh "Explain quantum computing"
scripts/chat.sh "Translate to French: Hello world" --provider groq --model llama-3.3-70b-versatile
scripts/chat.sh "List 5 facts about Mars" --provider openai --model gpt-4o-mini
scripts/chat.sh "Write a poem" --system "You are a poet" --temp 0.9
scripts/chat.sh --providers          # List all available providers
scripts/chat.sh --models --provider groq  # List models for a provider
```

**Options:**
- `--provider PROV` — openai, groq, anthropic, mistral, deepseek, xai, openrouter, together, etc.
- `--model MODEL` — Model name (default: gpt-4o-mini)
- `--temp N` — Temperature 0-2
- `--max-tokens N` — Max response length
- `--system TEXT` — System prompt
- `--providers` — List all available providers
- `--models` — List models for a provider

### 28. Media Library (`scripts/library.sh`)

Browse, search, and manage all generated media.

**Usage:**
```bash
scripts/library.sh
scripts/library.sh --type video --limit 20
scripts/library.sh --search "yoruba" --type image
scripts/library.sh --stats
scripts/library.sh --get MEDIA_ID
scripts/library.sh --favorite MEDIA_ID
scripts/library.sh --delete MEDIA_ID
```

**Options:**
- `--type TYPE` — video, audio, image, text
- `--search TEXT` — Full-text search
- `--limit N` — Results per page
- `--offset N` — Pagination offset
- `--stats` — Show library statistics
- `--get ID` — Get specific item
- `--favorite ID` — Toggle favorite
- `--delete ID` — Soft delete

### 29. Background Music (`scripts/music.sh`)

Browse and search background music tracks by mood.

**Usage:**
```bash
scripts/music.sh --mood epic
scripts/music.sh --search "drums" --limit 5
scripts/music.sh --moods
```

**Options:**
- `--mood MOOD` — sad, happy, chill, epic, upbeat, dramatic, romantic
- `--search TEXT` — Search by title
- `--limit N` — Max results
- `--moods` — List all available moods

## API Endpoints Reference

| Category | Operation | Endpoint | Method |
|----------|-----------|----------|--------|
| **Video Creation** | Scenes-to-Video | `/api/v1/ai/scenes-to-video` | POST |
| | Topic-to-Video | `/api/v1/ai/footage-to-video` | POST |
| | AI Video Gen | `/api/v1/videos/generate` | POST |
| | YouTube Shorts | `/api/v1/yt-shorts/create` | POST |
| | Image-to-Video | `/api/v1/videos/from_image` | POST |
| **Video Editing** | Merge Videos | `/api/v1/videos/merge` | POST |
| | Add Audio | `/api/v1/videos/add-audio` | POST |
| | Add Captions | `/api/v1/videos/add-captions` | POST |
| | Text Overlay | `/api/v1/videos/text-overlay` | POST |
| | Extract Clips | `/api/v1/videos/clips` | POST |
| | Extract Frames | `/api/v1/videos/frames` | POST |
| | Advanced/Colorkey | `/api/v1/videos/advanced` | POST |
| | Thumbnails | `/api/v1/videos/thumbnails` | POST |
| **Image** | AI Image Gen | `/api/v1/pollinations/image/generate` | POST |
| | Vision Analysis | `/api/v1/pollinations/vision/analyze` | POST |
| | Image Enhance | `/api/v1/images/enhance` | POST |
| **Screenshot** | Web Screenshot | `/api/v1/web_screenshot/capture` | POST |
| **Audio** | Text-to-Speech | `/api/v1/audio/speech` | POST |
| | TTS Providers | `/api/v1/audio/tts/providers` | GET |
| | Music Tracks | `/api/v1/music/tracks` | GET |
| | Music Moods | `/api/v1/music/moods` | GET |
| | Transcribe | `/api/v1/audio/transcriptions` | POST |
| **Documents** | Marker Convert | `/api/v1/documents/marker/` | POST |
| | LangExtract | `/api/v1/documents/langextract/` | POST |
| **AI / LLM** | AnyLLM Chat (30+ providers) | `/api/v1/anyllm/completions` | POST |
| | List Providers | `/api/v1/anyllm/providers` | GET |
| | List Models | `/api/v1/anyllm/list-models` | POST |
| | Research Topic | `/api/v1/ai/research-topic` | POST |
| | News Research | `/api/v1/ai/news-research` | POST |
| **Research** | Web Search | `/api/v1/research/web` | POST |
| | News Search | `/api/v1/research/news` | POST |
| | Stock Videos | `/api/v1/ai/video-search/stock-videos` | POST |
| | Stock Images | `/api/v1/ai/image-search/stock-images` | POST |
| **Media Utils** | Download (yt-dlp) | `/api/v1/media/download` | POST |
| | Format Convert | `/api/v1/media/conversions/` | POST |
| | Metadata | `/api/v1/media/metadata` | POST |
| | YT Transcripts | `/api/v1/media/youtube-transcripts` | POST |
| **Content** | Viral Content | `/api/v1/simone/viral-content` | POST |
| | Video-to-Blog | `/api/v1/simone/video-to-blog` | POST |
| **Social** | Schedule Post | `/api/v1/postiz/schedule` | POST |
| | Post Now | `/api/v1/postiz/schedule-now` | POST |
| | Create Draft | `/api/v1/postiz/create-draft` | POST |
| | List Integrations | `/api/v1/postiz/integrations` | GET |
| | Generate Content | `/api/v1/postiz/generate-content` | POST |
| **System** | Job Status | `/api/v1/jobs/{job_id}/status` | GET |
| | Library | `/api/v1/library/content` | GET |
| | Library Stats | `/api/v1/library/stats` | GET |

## Common Workflows

### Quick Short Video
```bash
scripts/topic-to-video.sh "Your topic" --duration 60 --lang en
```

### Professional Short (scenes control)
```bash
scripts/generate-script.sh "Your topic" --type educational > script_notes.txt
# Create scenes.json from script
scripts/scenes-to-video.sh scenes.json --voice en-US-GuyNeural --music epic --captions viral_bounce
```

### Content Series Pipeline
```bash
# 1. Research
scripts/research.sh "topic" --type web

# 2. Generate scripts
scripts/generate-script.sh "episode 1 topic" --type educational --lang fr

# 3. Build each episode
scripts/scenes-to-video.sh ep1-scenes.json --voice fr-FR-HenriNeural --music epic

# 4. Add captions
scripts/add-captions.sh VIDEO_URL --style karaoke --lang fr

# 5. Schedule
scripts/schedule-post.sh "Episode 1 is out!" --integrations ID1,ID2 --media VIDEO_URL --now
```

## Tips

1. **Portrait for shorts**: Use `--resolution 1080x1920` for TikTok/Reels/Shorts
2. **Landscape for YouTube**: Use `--resolution 1920x1080` for long-form
3. **Edge TTS for languages**: 40+ languages with 300+ voices
4. **Kokoro for quality**: Most natural English voices
5. **Batch jobs**: Submit multiple jobs — the queue handles concurrency
6. **Save job IDs**: You need result URLs for merging and post-processing
7. **Ken Burns**: Use `--motion ken_burns` to animate static images
8. **Epic music**: Use `--music epic` for documentary-style content

## API Documentation

- Repository: https://github.com/isaacgounton/griot
- API Docs: `http://YOUR_INSTANCE:8000/docs`
