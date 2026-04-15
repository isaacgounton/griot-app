#!/bin/bash
# Griot - Topic to Video (fully automated)
# Usage: ./topic-to-video.sh "topic" [--lang code] [--duration N] [--type type]

set -e

TOPIC="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
LANG="en"
DURATION="60"
SCRIPT_TYPE=""
PROVIDER="edge"
VOICE=""
FOOTAGE=""
MEDIA_TYPE=""
AI_VIDEO_PROVIDER=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --lang) LANG="$2"; shift 2 ;;
    --duration) DURATION="$2"; shift 2 ;;
    --type) SCRIPT_TYPE="$2"; shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    --voice) VOICE="$2"; shift 2 ;;
    --footage) FOOTAGE="$2"; shift 2 ;;
    --media-type) MEDIA_TYPE="$2"; shift 2 ;;
    --ai-video-provider) AI_VIDEO_PROVIDER="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$TOPIC" ]]; then
  echo "Usage: topic-to-video.sh \"topic\" [options]"
  echo ""
  echo "Options:"
  echo "  --lang CODE               Language (default: en)"
  echo "  --duration N              Target seconds (default: 60)"
  echo "  --type TYPE               educational, facts, story, promotional"
  echo "  --provider PROV           TTS: edge, kokoro, kitten, pollinations"
  echo "  --voice VOICE             TTS voice name"
  echo "  --footage SOURCE          pexels, pixabay, unsplash, ai_generated (default: pexels)"
  echo "  --media-type TYPE         video or image (default: video)"
  echo "  --ai-video-provider PROV  modal_video, wavespeed, comfyui (when footage=ai_generated)"
  exit 1
fi

# Build request (API expects: tts_provider, voice, tts_speed)
BODY=$(jq -n -c \
  --arg topic "$TOPIC" \
  --arg lang "$LANG" \
  --arg duration "$DURATION" \
  --arg provider "$PROVIDER" \
  '{
    topic: $topic,
    language: $lang,
    video_duration: ($duration | tonumber),
    tts_provider: $provider
  }')

if [[ -n "$SCRIPT_TYPE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$SCRIPT_TYPE" '. + {script_type: $v}')
fi
if [[ -n "$VOICE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$VOICE" '. + {voice: $v}')
fi
if [[ -n "$FOOTAGE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$FOOTAGE" '. + {footage_provider: $v}')
fi
if [[ -n "$MEDIA_TYPE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$MEDIA_TYPE" '. + {media_type: $v}')
fi
if [[ -n "$AI_VIDEO_PROVIDER" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$AI_VIDEO_PROVIDER" '. + {ai_video_provider: $v}')
fi

echo "Creating video about: $TOPIC"
echo "Language: $LANG | Duration: ${DURATION}s | Provider: $PROVIDER"

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/ai/footage-to-video" \
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
      sleep 15
      ;;
  esac
done
