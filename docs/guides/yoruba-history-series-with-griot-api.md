# Complete Guide: Producing the Yoruba History Series Using Griot API

**Project**: La Grande Histoire du Peuple Yoruba (6-chapter documentary series)
**Source**: [github.com/isaacgounton/darlene/projects/yoruba-history-series](https://github.com/isaacgounton/darlene/tree/master/projects/yoruba-history-series)
**Production method**: 100% Griot API

---

## Overview

This guide walks you through producing all **42 shorts** and **12 long-form videos** of the Yoruba History Series using only the Griot API. No external editing software, microphone, or design tools needed.

**What you need:**
- A Griot API key (`X-API-Key` header for all requests)
- The Griot API running (default: `http://localhost:8000`)
- The chapter scripts from the project repository

**Base URL** used throughout: `http://localhost:8000`

---

## Table of Contents

1. [Production Pipeline Summary](#1-production-pipeline-summary)
2. [Phase 1: Research & Script Writing](#2-phase-1-research--script-writing)
3. [Phase 2: Visual Asset Collection](#3-phase-2-visual-asset-collection)
4. [Phase 3: Voice-Over / TTS Generation](#4-phase-3-voice-over--tts-generation)
5. [Phase 4: Building the Shorts](#5-phase-4-building-the-shorts)
6. [Phase 5: Compiling Long-Form Videos](#6-phase-5-compiling-long-form-videos)
7. [Phase 6: Captions & Subtitles](#7-phase-6-captions--subtitles)
8. [Phase 7: Thumbnails & Visuals](#8-phase-7-thumbnails--visuals)
9. [Phase 8: Social Media & Distribution](#9-phase-8-social-media--distribution)
10. [Full Automated Workflow (One-Shot)](#10-full-automated-workflow-one-shot)
11. [API Reference Quick Sheet](#11-api-reference-quick-sheet)
12. [Tips & Best Practices](#12-tips--best-practices)

---

## 1. Production Pipeline Summary

For each of the 6 weekly chapters:

```
Research (web/news) → Script Generation → Stock Media Search
    → TTS Voice-Over → Scenes-to-Video (Shorts) → Merge (Long Videos)
        → Add Captions → Generate Thumbnails → Schedule to Social Media
```

**Per chapter output:**
- 7 shorts (60-90s each, 9:16 vertical)
- 2 long videos (8-12min each, 16:9 horizontal)
  - VL1 = Shorts 1-3 compiled
  - VL2 = Shorts 4-7 compiled

---

## 2. Phase 1: Research & Script Writing

### 2.1 Research the Topic

Use the web research endpoint to gather historical information for each chapter.

```bash
# Research Yoruba creation mythology (Chapter 1)
curl -X POST "http://localhost:8000/api/v1/research/web" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Yoruba creation mythology Olorun Obatala Ife cosmogony",
    "max_results": 10
  }'
```

```bash
# Research news and recent academic findings
curl -X POST "http://localhost:8000/api/v1/research/news" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Yoruba history culture heritage",
    "language": "fr",
    "max_results": 5
  }'
```

**Do this for each chapter theme:**
| Chapter | Research Query |
|---------|---------------|
| 1 | `Yoruba creation myth Olorun Obatala Ife cosmogony Orishas` |
| 2 | `Yoruba Orishas pantheon Shango Oshun Ogun Orunmila divine` |
| 3 | `Yoruba kingdoms Ife Oyo Benin Oduduwa dynasties` |
| 4 | `Oyo Empire golden age cavalry Egungun trade routes` |
| 5 | `Yoruba wars colonization slave trade diaspora Candomble Santeria` |
| 6 | `Modern Yoruba culture Osogbo festival Nollywood music Ifa` |

### 2.2 Generate Scripts

Use AI script generation to create narration scripts for each short.

```bash
# Generate script for Short 1 - "Olorun, maître du ciel"
curl -X POST "http://localhost:8000/api/v1/ai/script-generation" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Olorun, le Dieu Suprême de la mythologie Yoruba - maître du ciel, créateur silencieux qui règne sur Orun et délègue la création aux Orishas. Commencer par: Avant la terre, avant l eau, avant même le temps... il n y avait qu Olorun.",
    "language": "fr",
    "script_type": "educational",
    "style": "dramatic",
    "max_duration": 90,
    "target_audience": "francophone audience interested in African history and mythology"
  }'
```

**Alternative**: Use text generation for more control over the output.

```bash
curl -X POST "http://localhost:8000/api/v1/text/text-generation" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a 60-90 second documentary narration script in French about Olorun, the supreme god in Yoruba mythology. Structure: [HOOK 0-5s] captivating opener, [CONTEXT 5-20s] who Olorun is, [BODY 20-70s] his role in Yoruba cosmogony, [CTA 70-90s] tease next episode about Obatala. Tone: majestic, mysterious, educational. Include visual direction notes in brackets.",
    "model": "openai",
    "temperature": 0.7
  }'
```

> **Repeat for all 42 shorts** (7 per chapter x 6 chapters). Save the scripts - you'll need them for TTS and scene building.

### 2.3 Generate Long-Form Video Scripts

The long videos need transitions between the compiled shorts:

```bash
curl -X POST "http://localhost:8000/api/v1/text/text-generation" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write transition narrations in French to link 3 documentary segments into a cohesive 8-12 minute video about Yoruba creation mythology. Segment 1: Olorun master of the sky. Segment 2: Obatala receives the mission. Segment 3: Birth of Ife. Write: an intro (30s), transition between segments 1-2 (15s), transition between 2-3 (15s), and an outro with call to action (30s). Tone: documentary, epic.",
    "model": "openai",
    "temperature": 0.7
  }'
```

---

## 3. Phase 2: Visual Asset Collection

### 3.1 Search Stock Videos

For each scene, find relevant background footage:

```bash
# Search for Yoruba-themed footage
curl -X POST "http://localhost:8000/api/v1/ai/video-search/stock-videos" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "African starry sky cosmos universe creation",
    "orientation": "portrait",
    "per_page": 5
  }'
```

```bash
# Search for African cultural footage
curl -X POST "http://localhost:8000/api/v1/ai/video-search/stock-videos" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Yoruba traditional ceremony Nigeria",
    "orientation": "portrait",
    "per_page": 5
  }'
```

### 3.2 Search Stock Images

For scenes where static images with motion effects work better:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/image-search/stock-images" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Yoruba traditional art sculpture Ife bronze",
    "per_page": 10
  }'
```

### 3.3 Generate AI Images

For illustrations of Orishas, mythological scenes, and custom visuals:

```bash
# Generate an illustration of Olorun
curl -X POST "http://localhost:8000/api/v1/pollinations/image/generate" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Majestic African deity Olorun in golden robes standing above clouds, celestial light radiating, Yoruba art style, divine cosmic background with stars, rich gold and deep indigo color palette, epic documentary illustration style",
    "width": 1080,
    "height": 1920,
    "model": "flux",
    "enhance": true
  }'
```

```bash
# Generate an image of Obatala creating Earth
curl -X POST "http://localhost:8000/api/v1/pollinations/image/generate" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Obatala Yoruba deity descending from sky with golden chain, carrying a snail shell filled with sacred sand, creating the earth below, epic cinematic lighting, African mythology illustration, vertical composition",
    "width": 1080,
    "height": 1920,
    "model": "flux",
    "enhance": true
  }'
```

**Suggested AI images per chapter** (generate all in batch):

| Chapter | Key Images to Generate |
|---------|----------------------|
| 1 | Olorun in sky, Obatala descending, Ife birth, Ogun opening paths, Human creation, Ori choosing destiny, First spirits |
| 2 | Orishas assembly, Shango with lightning, Oshun at river, Ogun with iron, Orunmila divining, 17 Orishas panorama, Orishas guiding humans |
| 3 | Ancient Ife city, Oduduwa portrait, 7 kingdoms map, Oyo rise, Benin kingdom, Royal dynasty, Sacred king ceremony |
| 4 | Oyo warriors, Cavalry charge, Egungun masquerade, Trade routes map, Oyo Mesi council, Bashorun figure, Oyo influence map |
| 5 | Yoruba wars, European ships arriving, Slave trade scene, Resistant kings, Candomble ceremony, Santeria ritual, Preserved traditions |
| 6 | Modern Yoruba people, Osogbo festival, Ifa divination, Modern Oba, Nollywood scene, Yoruba music, Global influence |

### 3.4 Auto-Generate Search Queries from Script

Let the AI suggest optimal search terms:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/video-search-queries" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "script": "Avant la terre, avant l eau, avant même le temps, il n y avait qu Olorun. Olorun, le Dieu Suprême, maître absolu du ciel. Son nom signifie littéralement Propriétaire du Ciel...",
    "num_queries": 6
  }'
```

---

## 4. Phase 3: Voice-Over / TTS Generation

### 4.1 Choose a Voice

List available voices:

```bash
# List all TTS voices
curl -X GET "http://localhost:8000/api/v1/audio/providers" \
  -H "X-API-Key: YOUR_API_KEY"
```

**Recommended voices for documentary narration:**

| Provider | Voice | Style | Best For |
|----------|-------|-------|----------|
| **Kokoro** | `af_bella` | Warm female | Narration (recommended) |
| **Kokoro** | `am_adam` | Deep male | Documentary authority |
| **Edge TTS** | `fr-FR-HenriNeural` | French male | French narration |
| **Edge TTS** | `fr-FR-DeniseNeural` | French female | French narration |
| **Pollinations** | `onyx` | Deep male | Epic tone |
| **Pollinations** | `nova` | Clear female | Educational tone |

### 4.2 Generate Voice-Over for Each Short

```bash
# Generate French narration for Short 1
curl -X POST "http://localhost:8000/api/v1/audio/speech" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Avant la terre, avant l eau, avant même le temps... il n y avait qu Olorun. Olorun, le Dieu Suprême, maître absolu du ciel. Son nom signifie littéralement Propriétaire du Ciel. Mais Olorun ne régnait pas seul. Selon la tradition Yoruba, Olorun demeure dans le royaume céleste, Orun. De là-haut, il observe tout, mais n intervient jamais directement. Car Olorun, dans sa sagesse infinie, délègue. Il confie des missions sacrées aux Orishas, ses divinités intermédiaires. Olorun est Alaaye, celui qui donne la vie. Sans lui, rien n existe. Mais il ne crée pas seul. Il fait appel à Obatala. Mais qui est Obatala? Et comment la terre a-t-elle vraiment été créée? La réponse dans le prochain épisode!",
    "provider": "edge",
    "voice": "fr-FR-HenriNeural",
    "speed": 0.95,
    "output_format": "mp3"
  }'
```

> **Tip**: Use `speed: 0.95` for a slightly slower, more dramatic documentary pace.

### 4.3 Generate Background Music

Browse available music by mood:

```bash
# List epic/dramatic music for documentary
curl -X GET "http://localhost:8000/api/v1/music/tracks?mood=epic&limit=10" \
  -H "X-API-Key: YOUR_API_KEY"
```

Suggested moods per chapter:

| Chapter | Primary Mood | Secondary |
|---------|-------------|-----------|
| 1 - Creation | `epic` | `chill` |
| 2 - Orishas | `epic` | `happy` |
| 3 - Kingdoms | `epic` | `upbeat` |
| 4 - Oyo Golden Age | `upbeat` | `epic` |
| 5 - Wars & Diaspora | `sad` | `epic` |
| 6 - Modern Era | `upbeat` | `happy` |

---

## 5. Phase 4: Building the Shorts

### 5.1 Option A: Scenes-to-Video (Recommended)

This is the most powerful endpoint for building shorts. Define scenes with narration text, and the API handles TTS, visuals, captions, and assembly.

```bash
# Build Short 1: "Olorun, maître du ciel" (complete short)
curl -X POST "http://localhost:8000/api/v1/ai/scenes-to-video" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [
      {
        "text": "Avant la terre, avant l eau, avant même le temps, il n y avait qu Olorun.",
        "search_terms": ["starry sky cosmos creation", "divine celestial light"],
        "duration": 8
      },
      {
        "text": "Olorun, le Dieu Suprême, maître absolu du ciel. Son nom signifie littéralement Propriétaire du Ciel.",
        "search_terms": ["golden divine figure african art", "majestic sky clouds gold"],
        "duration": 12
      },
      {
        "text": "Selon la tradition Yoruba, Olorun demeure dans le royaume céleste, Orun. De là-haut, il observe tout, mais n intervient jamais directement.",
        "search_terms": ["celestial realm above clouds", "african spiritual ceremony"],
        "duration": 15
      },
      {
        "text": "Car Olorun, dans sa sagesse infinie, délègue. Il confie des missions sacrées aux Orishas, ses divinités intermédiaires.",
        "search_terms": ["african deities spiritual figures", "golden light divine delegation"],
        "duration": 15
      },
      {
        "text": "Olorun est Alaaye, celui qui donne la vie. Sans lui, rien n existe. Mais il ne crée pas seul, il fait appel à Obatala.",
        "search_terms": ["life creation nature growth", "african mythology art"],
        "duration": 15
      },
      {
        "text": "Mais qui est Obatala? Et comment la terre a-t-elle vraiment été créée? La réponse dans le prochain épisode!",
        "search_terms": ["mystery cliffhanger dramatic", "earth creation from above"],
        "duration": 10
      }
    ],
    "voice_provider": "edge",
    "tts_voice": "fr-FR-HenriNeural",
    "tts_speed": 0.95,
    "background_music": "epic",
    "caption_style": "viral_bounce",
    "caption_color": "#FFFFFF",
    "resolution": "1080x1920",
    "motion_effect": "ken_burns",
    "language": "fr"
  }'
```

This returns a `job_id`. Poll for status:

```bash
curl -X GET "http://localhost:8000/api/v1/ai/scenes-to-video/JOB_ID_HERE" \
  -H "X-API-Key: YOUR_API_KEY"
```

When `status: "completed"`, you get an S3 URL to the finished short.

### 5.2 Option B: Footage-to-Video (One-Shot)

For a more automated approach where the AI handles everything:

```bash
curl -X POST "http://localhost:8000/api/v1/ai/footage-to-video" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Olorun, le Dieu Suprême de la mythologie Yoruba, maître du ciel, créateur silencieux",
    "language": "fr",
    "script_type": "educational",
    "video_duration": 75,
    "voice_provider": "edge",
    "tts_voice": "fr-FR-HenriNeural"
  }'
```

### 5.3 Option C: Manual Assembly (Maximum Control)

If you want to control every detail:

**Step 1**: Generate TTS audio (see Phase 3)

**Step 2**: Generate or find visuals (see Phase 2)

**Step 3**: Use the advanced video endpoint to combine background images with TTS:

```bash
curl -X POST "http://localhost:8000/api/v1/videos/advanced" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "mode": "tts_captioned",
    "background_image_url": "https://your-s3-bucket/olorun-illustration.png",
    "text": "Avant la terre, avant l eau, avant même le temps...",
    "tts_provider": "edge",
    "tts_voice": "fr-FR-HenriNeural",
    "caption_style": "karaoke",
    "motion_effect": "ken_burns"
  }'
```

**Step 4**: Merge individual scene clips into a complete short:

```bash
curl -X POST "http://localhost:8000/api/v1/videos/merge" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "video_urls": [
      "https://your-s3/scene1.mp4",
      "https://your-s3/scene2.mp4",
      "https://your-s3/scene3.mp4",
      "https://your-s3/scene4.mp4",
      "https://your-s3/scene5.mp4",
      "https://your-s3/scene6.mp4"
    ],
    "transition": "dissolve",
    "transition_duration": 0.5
  }'
```

**Step 5**: Add background music:

```bash
curl -X POST "http://localhost:8000/api/v1/videos/add-audio" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://your-s3/short1-merged.mp4",
    "audio_url": "https://your-s3/epic-background-music.mp3",
    "sync_mode": "mix",
    "audio_volume": 0.15,
    "video_volume": 1.0,
    "fade_in": 2.0,
    "fade_out": 3.0
  }'
```

---

## 6. Phase 5: Compiling Long-Form Videos

### 6.1 Merge Shorts into Long Videos

**VL1** (Shorts 1-3) for each chapter:

```bash
curl -X POST "http://localhost:8000/api/v1/videos/merge" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "video_urls": [
      "https://your-s3/ch1-intro.mp4",
      "https://your-s3/ch1-short1.mp4",
      "https://your-s3/ch1-transition-1-2.mp4",
      "https://your-s3/ch1-short2.mp4",
      "https://your-s3/ch1-transition-2-3.mp4",
      "https://your-s3/ch1-short3.mp4",
      "https://your-s3/ch1-outro-vl1.mp4"
    ],
    "transition": "dissolve",
    "transition_duration": 1.0
  }'
```

> **Note**: For the long videos, you need to produce intro, transition, and outro segments first. Use the same scenes-to-video approach with your transition scripts from Phase 1.

### 6.2 Generate Transition Segments

```bash
# Create a transition between Short 1 and Short 2
curl -X POST "http://localhost:8000/api/v1/ai/scenes-to-video" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "scenes": [
      {
        "text": "Olorun a fait son choix. Parmi tous les Orishas, c est Obatala qu il désigne pour accomplir la mission la plus sacrée de toutes.",
        "search_terms": ["divine light golden transition", "spiritual mission sacred"],
        "duration": 10
      }
    ],
    "voice_provider": "edge",
    "tts_voice": "fr-FR-HenriNeural",
    "tts_speed": 0.9,
    "background_music": "epic",
    "caption_style": "standard_bottom",
    "resolution": "1920x1080",
    "language": "fr"
  }'
```

> **Important**: Use `1920x1080` (landscape) for long videos, `1080x1920` (portrait) for shorts.

---

## 7. Phase 6: Captions & Subtitles

### 7.1 Add Styled Captions

If you used `scenes-to-video`, captions are already included. For manual assembly or to add bilingual subtitles:

```bash
# Add French captions with karaoke-style highlighting
curl -X POST "http://localhost:8000/api/v1/videos/add-captions" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://your-s3/ch1-short1-final.mp4",
    "style": "karaoke",
    "font_family": "Montserrat",
    "font_size": 42,
    "font_bold": true,
    "line_color": "#FFFFFF",
    "word_highlight_color": "#FFD700",
    "outline_color": "#000000",
    "position": "bottom_center",
    "language": "fr"
  }'
```

### 7.2 Add English Subtitles (for international audience)

```bash
# First, transcribe to get timing
curl -X POST "http://localhost:8000/api/v1/media/transcribe" \
  -H "X-API-Key: YOUR_API_KEY" \
  -F "file=@ch1-short1.mp4" \
  -F "language=fr" \
  -F "output_format=srt"
```

Then use text generation to translate the SRT file and apply it as a secondary subtitle track.

---

## 8. Phase 7: Thumbnails & Visuals

### 8.1 Generate Thumbnails

Use AI image generation to create eye-catching thumbnails:

```bash
# Thumbnail for Short 1 (vertical 1080x1920)
curl -X POST "http://localhost:8000/api/v1/pollinations/image/generate" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "YouTube thumbnail: OLORUN majestic African deity in golden light, cosmic starry background, bold text overlay space, Yoruba mythology documentary style, dramatic cinematic lighting, vibrant gold and deep blue, vertical composition for social media",
    "width": 1080,
    "height": 1920,
    "model": "flux",
    "enhance": true
  }'
```

```bash
# Thumbnail for VL1 (horizontal 1920x1080)
curl -X POST "http://localhost:8000/api/v1/pollinations/image/generate" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "YouTube thumbnail: epic Yoruba creation mythology scene, Olorun deity above, earth forming below, golden chain descending from sky, dramatic lighting, documentary title card style, wide cinematic composition, bold readable text space on left third",
    "width": 1920,
    "height": 1080,
    "model": "flux",
    "enhance": true
  }'
```

### 8.2 Add Title Text to Thumbnails

```bash
# Overlay title text on generated thumbnail
curl -X POST "http://localhost:8000/api/v1/videos/text-overlay" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://your-s3/thumbnail-base.mp4",
    "texts": [
      {
        "text": "OLORUN",
        "font_size": 72,
        "font_color": "#FFD700",
        "position": "center",
        "start_time": 0,
        "duration": 1
      },
      {
        "text": "Maître du Ciel",
        "font_size": 36,
        "font_color": "#FFFFFF",
        "position": "bottom_center",
        "start_time": 0,
        "duration": 1
      }
    ]
  }'
```

> **Alternative**: Use the image edit endpoint to layer text images over thumbnail backgrounds.

---

## 9. Phase 8: Social Media & Distribution

### 9.1 Generate Social Media Posts

```bash
# Generate promotional content for the series
curl -X POST "http://localhost:8000/api/v1/simone/viral-content" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "New documentary series: La Grande Histoire du Peuple Yoruba - Episode 1: La Création du Monde. Exploring Olorun, Obatala, and the Yoruba cosmogony.",
    "platforms": ["twitter", "instagram", "linkedin"],
    "language": "fr",
    "hashtags": true
  }'
```

### 9.2 Schedule Posts to Social Media

If you have Postiz configured:

```bash
# Check available social accounts
curl -X GET "http://localhost:8000/api/v1/postiz/integrations" \
  -H "X-API-Key: YOUR_API_KEY"

# Schedule a post
curl -X POST "http://localhost:8000/api/v1/postiz/schedule" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Saviez-vous que selon la mythologie Yoruba, Olorun est le Dieu Suprême qui règne sur le ciel mais n intervient jamais directement? Découvrez l histoire fascinante de la création du monde Yoruba dans notre nouvelle série documentaire! #Yoruba #Histoire #Afrique",
    "platforms": ["twitter", "instagram"],
    "schedule_date": "2026-03-01T10:00:00Z",
    "media_urls": ["https://your-s3/ch1-short1-final.mp4"]
  }'
```

### 9.3 Schedule Completed Job Outputs Directly

```bash
# Schedule a completed video job directly to social media
curl -X POST "http://localhost:8000/api/v1/postiz/schedule-job-post" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "job_id": "YOUR_COMPLETED_JOB_ID",
    "content": "Episode 1: Olorun, maître du ciel #YorubaHistory #Afrique #Documentaire",
    "platforms": ["tiktok", "instagram"],
    "post_type": "now"
  }'
```

---

## 10. Full Automated Workflow (One-Shot)

For maximum automation, use `footage-to-video` which handles the entire pipeline from topic to finished video:

```bash
# One-shot: Topic → Script → TTS → Visuals → Captions → Video
curl -X POST "http://localhost:8000/api/v1/ai/footage-to-video" \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Olorun, le Dieu Suprême dans la mythologie Yoruba. Son rôle dans la cosmogonie Yoruba, comment il délègue la création aux Orishas, et pourquoi il est appelé Alaaye - celui qui donne la vie.",
    "language": "fr",
    "script_type": "educational",
    "video_duration": 75,
    "voice_provider": "edge",
    "tts_voice": "fr-FR-HenriNeural"
  }'
```

### Complete Chapter 1 Production Script (Automated)

Here's a bash script to produce all 7 shorts of Chapter 1:

```bash
#!/bin/bash
API_URL="http://localhost:8000"
API_KEY="YOUR_API_KEY"

# Chapter 1 shorts - topics
declare -a TOPICS=(
  "Olorun, le Dieu Suprême Yoruba, maître absolu du ciel et créateur silencieux qui observe depuis Orun"
  "Obatala reçoit d Olorun la mission sacrée de créer la terre, descendant du ciel avec une chaîne d or"
  "La naissance d Ife - Obatala verse le sable sacré depuis la coquille d escargot, la poule gratte la terre qui s étend"
  "Ogun, le dieu du fer, arrive pour ouvrir les chemins à travers la forêt dense avec sa machette"
  "Obatala façonne les premiers humains avec de l argile, et Olorun leur insuffle le souffle de vie"
  "Le choix du destin Ori - chaque âme choisit sa destinée avant de naître sur terre"
  "Les premiers esprits qui peuplent la terre - Orishas et ancêtres fondent la civilisation Yoruba"
)

for i in "${!TOPICS[@]}"; do
  SHORT_NUM=$((i + 1))
  echo "=== Generating Short $SHORT_NUM ==="

  JOB_ID=$(curl -s -X POST "$API_URL/api/v1/ai/footage-to-video" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{
      \"topic\": \"${TOPICS[$i]}\",
      \"language\": \"fr\",
      \"script_type\": \"educational\",
      \"video_duration\": 75,
      \"voice_provider\": \"edge\",
      \"tts_voice\": \"fr-FR-HenriNeural\"
    }" | jq -r '.job_id')

  echo "Short $SHORT_NUM job: $JOB_ID"

  # Poll until complete
  while true; do
    STATUS=$(curl -s "$API_URL/api/v1/jobs/$JOB_ID" \
      -H "X-API-Key: $API_KEY" | jq -r '.status')
    echo "  Status: $STATUS"
    if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
      break
    fi
    sleep 30
  done
done
```

---

## 11. API Reference Quick Sheet

| Task | Endpoint | Method |
|------|----------|--------|
| **Research** | `/api/v1/research/web` | POST |
| **News** | `/api/v1/research/news` | POST |
| **Script Generation** | `/api/v1/ai/script-generation` | POST |
| **Text Generation** | `/api/v1/text/text-generation` | POST |
| **Stock Videos** | `/api/v1/ai/video-search/stock-videos` | POST |
| **Stock Images** | `/api/v1/ai/image-search/stock-images` | POST |
| **AI Image Gen** | `/api/v1/pollinations/image/generate` | POST |
| **Image-to-Video** | `/api/v1/images/image-to-video` | POST |
| **TTS (Speech)** | `/api/v1/audio/speech` | POST |
| **Music Tracks** | `/api/v1/music/tracks` | GET |
| **Scenes-to-Video** | `/api/v1/ai/scenes-to-video` | POST |
| **Footage-to-Video** | `/api/v1/ai/footage-to-video` | POST |
| **Video Merge** | `/api/v1/videos/merge` | POST |
| **Add Audio** | `/api/v1/videos/add-audio` | POST |
| **Add Captions** | `/api/v1/videos/add-captions` | POST |
| **Text Overlay** | `/api/v1/videos/text-overlay` | POST |
| **Transcribe** | `/api/v1/media/transcribe` | POST |
| **Viral Content** | `/api/v1/simone/viral-content` | POST |
| **Social Schedule** | `/api/v1/postiz/schedule` | POST |
| **Job Status** | `/api/v1/jobs/{job_id}` | GET |
| **Video Library** | `/api/v1/library` | GET |

---

## 12. Tips & Best Practices

### Voice Consistency
- **Use the same voice** (`fr-FR-HenriNeural` or whichever you choose) across the entire series
- **Use the same speed** (0.95) for all narrations
- This creates a recognizable, cohesive series identity

### Visual Consistency
- **Use the same color palette** in AI image prompts: gold + deep indigo + white for Chapter 1 (creation/divinity)
- **Adapt colors per chapter**: gold for creation, red for Shango/war, green for nature/Oshun, etc.
- **Use the same caption style** across all shorts (e.g., `viral_bounce` or `karaoke`)

### Production Order
1. Generate all 7 scripts for a chapter first
2. Generate all TTS audio files
3. Generate all AI images
4. Build all 7 shorts
5. Then compile VL1 and VL2
6. Add bilingual captions last

### Quality Control
- **Poll job status** - don't assume completion
- **Review generated scripts** before TTS - edit for accuracy
- **Preview shorts** before compiling long videos
- **Keep job IDs** organized per chapter/short for easy reference

### File Organization
Keep a tracking spreadsheet:

```
| Chapter | Short# | Script Job | TTS Job | Video Job | Status |
|---------|--------|------------|---------|-----------|--------|
| 1       | 1      | abc-123    | def-456 | ghi-789   | Done   |
| 1       | 2      | ...        | ...     | ...       | ...    |
```

### Cost Optimization
- Use **Edge TTS** (free) over Pollinations TTS for narration
- Use **stock images + Ken Burns** motion instead of AI video generation for most scenes
- Use **Pexels/Pixabay** stock footage (free) before generating AI footage
- Batch your requests - the job queue handles concurrency

### Publishing Schedule (from the project plan)
- **Monday-Friday**: 1 short per day (5 shorts)
- **Saturday**: 2 shorts + VL1
- **Sunday**: VL2 + rest
- Use Postiz scheduling to automate the entire week's uploads

---

## Appendix: Chapter Content Quick Reference

| Ch | Theme | Shorts | VL1 | VL2 |
|----|-------|--------|-----|-----|
| 1 | La Création du Monde | Olorun, Obatala's mission, Birth of Ife, Ogun, Human creation, Ori/destiny, First spirits | Cosmos & Ife (1-3) | Humanity & Spirits (4-7) |
| 2 | L'âge des Orishas | Assembly, Shango, Oshun, Ogun, Orunmila, 17 Orishas, Guidance | Divine Council (1-3) | Power & Guidance (4-7) |
| 3 | Les Royaumes Yoruba | Ife, Oduduwa, 7 Kingdoms, Oyo rise, Benin, Dynasties, Sacred kings | Birth of Kingdoms (1-3) | Royal Organization (4-7) |
| 4 | L'âge d'or d'Oyo | Power origins, Cavalry, Egungun, Economy, Oyo Mesi, Bashorun, West African influence | Foundations of Power (1-3) | Governance & Influence (4-7) |
| 5 | Guerres & Diaspora | Internal wars, Europeans, Slave trade, Resistance, Brazil/Candomblé, Cuba/Santería, Survival | Conflicts & Colonization (1-3) | Diaspora & Preservation (4-7) |
| 6 | Le Monde Moderne | Yoruba today, Osogbo festival, Ifa system, Modern kings, Cinema, Music, Global influence | Living Traditions (1-3) | Culture & Global Reach (4-7) |

---

*Guide produced for use with Griot API. All 42 shorts and 12 long-form videos can be created entirely through API calls - no external tools required.*
