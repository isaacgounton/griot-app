#!/bin/bash
# Griot - Add Audio to Video
# Usage: ./add-audio.sh VIDEO_URL AUDIO_URL [--mode mix] [--volume 0.3]

set -e

VIDEO_URL="$1"
AUDIO_URL="$2"
shift 2 2>/dev/null || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
MODE="mix"
AUDIO_VOL="0.3"
VIDEO_VOL="1.0"
FADE_IN=""
FADE_OUT=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --volume) AUDIO_VOL="$2"; shift 2 ;;
    --video-volume) VIDEO_VOL="$2"; shift 2 ;;
    --fade-in) FADE_IN="$2"; shift 2 ;;
    --fade-out) FADE_OUT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$VIDEO_URL" ]] || [[ -z "$AUDIO_URL" ]]; then
  echo "Usage: add-audio.sh <video_url> <audio_url> [options]"
  echo ""
  echo "Options:"
  echo "  --mode MODE           replace, mix, overlay (default: mix)"
  echo "  --volume N            Audio volume 0.0-1.0 (default: 0.3)"
  echo "  --video-volume N      Video volume 0.0-1.0 (default: 1.0)"
  echo "  --fade-in N           Fade in seconds"
  echo "  --fade-out N          Fade out seconds"
  exit 1
fi

BODY=$(jq -n -c \
  --arg video "$VIDEO_URL" \
  --arg audio "$AUDIO_URL" \
  --arg mode "$MODE" \
  --arg avol "$AUDIO_VOL" \
  --arg vvol "$VIDEO_VOL" \
  '{
    video_url: $video,
    audio_url: $audio,
    sync_mode: $mode,
    audio_volume: ($avol | tonumber),
    video_volume: ($vvol | tonumber)
  }')

if [[ -n "$FADE_IN" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$FADE_IN" '. + {fade_in: ($v | tonumber)}')
fi
if [[ -n "$FADE_OUT" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$FADE_OUT" '. + {fade_out: ($v | tonumber)}')
fi

echo "Adding audio ($MODE mode)..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/videos/add-audio" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')

if [[ -z "$JOB_ID" ]]; then
  echo "Error:"
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
  exit 1
fi

echo "Job ID: $JOB_ID — polling..."

while true; do
  STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
  STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
  case "$STATUS" in
    completed)
      RESULT_URL=$(echo "$STATUS_RESPONSE" | jq -r '.data.result.url // .data.result.video_url // empty')
      echo "Done! Video with audio: $RESULT_URL"
      exit 0
      ;;
    failed)
      echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"
      exit 1
      ;;
    *)
      echo "  Status: $STATUS"
      sleep 10
      ;;
  esac
done
