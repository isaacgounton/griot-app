#!/bin/bash
# Griot - Scenes to Video
# Usage: ./scenes-to-video.sh scenes.json [--voice voice] [--provider provider] [--music mood] [--captions style]

set -e

SCENES_FILE="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
PROVIDER="edge"
VOICE="en-US-GuyNeural"
SPEED="1.0"
MUSIC=""
CAPTIONS=""
CAPTION_COLOR="#FFFFFF"
RESOLUTION=""
MOTION=""
LANG="en"
FOOTAGE=""
MEDIA_TYPE=""
AI_VIDEO_PROVIDER=""
AI_IMAGE_PROVIDER=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --provider) PROVIDER="$2"; shift 2 ;;
    --voice) VOICE="$2"; shift 2 ;;
    --speed) SPEED="$2"; shift 2 ;;
    --music) MUSIC="$2"; shift 2 ;;
    --captions) CAPTIONS="$2"; shift 2 ;;
    --caption-color) CAPTION_COLOR="$2"; shift 2 ;;
    --resolution) RESOLUTION="$2"; shift 2 ;;
    --motion) MOTION="$2"; shift 2 ;;
    --lang) LANG="$2"; shift 2 ;;
    --footage) FOOTAGE="$2"; shift 2 ;;
    --media-type) MEDIA_TYPE="$2"; shift 2 ;;
    --ai-video-provider) AI_VIDEO_PROVIDER="$2"; shift 2 ;;
    --ai-image-provider) AI_IMAGE_PROVIDER="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$SCENES_FILE" ]] || [[ ! -f "$SCENES_FILE" ]]; then
  echo "Usage: scenes-to-video.sh <scenes.json> [options]"
  echo ""
  echo "Scene file format (JSON array):"
  echo '  [{"text": "narration", "search_terms": ["kw1"], "duration": 10}, ...]'
  echo ""
  echo "Options:"
  echo "  --provider PROVIDER       TTS: edge, kokoro, kitten, piper, pollinations (default: edge)"
  echo "  --voice VOICE             Voice name (default: en-US-GuyNeural)"
  echo "  --speed N                 Speed 0.5-2.0 (default: 1.0)"
  echo "  --music MOOD              Background: epic, chill, sad, happy, upbeat"
  echo "  --captions STYLE          viral_bounce, karaoke, standard_bottom, highlight"
  echo "  --caption-color HEX       Caption color (default: #FFFFFF)"
  echo "  --resolution RES          1080x1920 (portrait) or 1920x1080 (landscape)"
  echo "  --motion EFFECT           ken_burns, zoom, pan, fade"
  echo "  --lang CODE               Language code (default: en)"
  echo "  --footage SOURCE          pexels, pixabay, ai_generated (default: pexels)"
  echo "  --media-type TYPE         video or image (default: video)"
  echo "  --ai-video-provider PROV  wavespeed, comfyui (when footage=ai_generated)"
  echo "  --ai-image-provider PROV  together, pollinations (when media-type=image + ai_generated)"
  exit 1
fi

# Read scenes from file
SCENES=$(cat "$SCENES_FILE")

# Build config object (API expects nested {scenes, config} structure)
CONFIG=$(jq -n -c \
  --arg provider "$PROVIDER" \
  --arg voice "$VOICE" \
  --arg speed "$SPEED" \
  --arg caption_color "$CAPTION_COLOR" \
  --arg lang "$LANG" \
  '{
    provider: $provider,
    voice: $voice,
    ttsSpeed: ($speed | tonumber),
    captionColor: $caption_color,
    language: $lang
  }')

# Add optional config fields
if [[ -n "$MUSIC" ]]; then
  CONFIG=$(echo "$CONFIG" | jq -c --arg v "$MUSIC" '. + {music: $v}')
fi
if [[ -n "$CAPTIONS" ]]; then
  CONFIG=$(echo "$CONFIG" | jq -c --arg v "$CAPTIONS" '. + {captionStyle: $v}')
fi
if [[ -n "$RESOLUTION" ]]; then
  CONFIG=$(echo "$CONFIG" | jq -c --arg v "$RESOLUTION" '. + {resolution: $v}')
fi
if [[ -n "$MOTION" ]]; then
  CONFIG=$(echo "$CONFIG" | jq -c --arg v "$MOTION" '. + {effect_type: $v}')
fi
if [[ -n "$FOOTAGE" ]]; then
  CONFIG=$(echo "$CONFIG" | jq -c --arg v "$FOOTAGE" '. + {footageProvider: $v}')
fi
if [[ -n "$MEDIA_TYPE" ]]; then
  CONFIG=$(echo "$CONFIG" | jq -c --arg v "$MEDIA_TYPE" '. + {mediaType: $v}')
fi
if [[ -n "$AI_VIDEO_PROVIDER" ]]; then
  CONFIG=$(echo "$CONFIG" | jq -c --arg v "$AI_VIDEO_PROVIDER" '. + {aiVideoProvider: $v}')
fi
if [[ -n "$AI_IMAGE_PROVIDER" ]]; then
  CONFIG=$(echo "$CONFIG" | jq -c --arg v "$AI_IMAGE_PROVIDER" '. + {aiImageProvider: $v}')
fi

# Build final request body
BODY=$(jq -n -c --argjson scenes "$SCENES" --argjson config "$CONFIG" '{scenes: $scenes, config: $config}')

echo "Creating video from $(echo "$SCENES" | jq 'length') scenes..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/ai/scenes-to-video" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')

if [[ -z "$JOB_ID" ]]; then
  echo "Error: Failed to create job"
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
  exit 1
fi

echo "Job ID: $JOB_ID"
echo "Polling for completion..."

while true; do
  STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
  STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')

  case "$STATUS" in
    completed)
      RESULT_URL=$(echo "$STATUS_RESPONSE" | jq -r '.data.result.url // .data.result.video_url // .data.result // empty')
      echo "Done! Video URL: $RESULT_URL"
      exit 0
      ;;
    failed)
      ERROR=$(echo "$STATUS_RESPONSE" | jq -r '.error // "Unknown error"')
      echo "Failed: $ERROR"
      exit 1
      ;;
    *)
      echo "  Status: $STATUS"
      sleep 10
      ;;
  esac
done
