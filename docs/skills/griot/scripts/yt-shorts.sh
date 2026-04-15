#!/bin/bash
# Griot - YouTube Shorts Creator
# Usage: ./yt-shorts.sh "YOUTUBE_URL" [--quality high] [--tracking]

set -e

YOUTUBE_URL="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
QUALITY="medium"
TRACKING=""
AUDIO_ENHANCE=""
FADE=""
THUMBNAIL=""
START=""
END=""
COOKIES=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --quality) QUALITY="$2"; shift 2 ;;
    --tracking) TRACKING="true"; shift ;;
    --audio-enhance) AUDIO_ENHANCE="$2"; shift 2 ;;
    --fade) FADE="true"; shift ;;
    --thumbnail) THUMBNAIL="true"; shift ;;
    --start) START="$2"; shift 2 ;;
    --end) END="$2"; shift 2 ;;
    --cookies) COOKIES="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$YOUTUBE_URL" ]]; then
  echo "Usage: yt-shorts.sh \"YOUTUBE_URL\" [options]"
  echo ""
  echo "Options:"
  echo "  --quality LVL       low, medium, high, ultra (default: medium)"
  echo "  --tracking          Enable speaker/face tracking"
  echo "  --audio-enhance M   speech, music, auto"
  echo "  --fade              Smooth fade transitions"
  echo "  --thumbnail         Generate thumbnail"
  echo "  --start N           Custom start time (seconds)"
  echo "  --end N             Custom end time (seconds)"
  echo "  --cookies FILE      Cookie file for restricted videos"
  exit 1
fi

BODY=$(jq -n -c --arg url "$YOUTUBE_URL" --arg quality "$QUALITY" \
  '{url: $url, quality: $quality}')

if [[ "$TRACKING" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {speaker_tracking: true}'); fi
if [[ -n "$AUDIO_ENHANCE" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$AUDIO_ENHANCE" '. + {audio_enhance: $v}'); fi
if [[ "$FADE" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {fade_transitions: true}'); fi
if [[ "$THUMBNAIL" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {generate_thumbnail: true}'); fi
if [[ -n "$START" ]] && [[ -n "$END" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg s "$START" --arg e "$END" '. + {start_time: ($s | tonumber), end_time: ($e | tonumber)}')
fi
if [[ -n "$COOKIES" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$COOKIES" '. + {cookies: $v}'); fi

echo "Creating YouTube Short from: $YOUTUBE_URL"

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/yt-shorts/create" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')

if [[ -z "$JOB_ID" ]]; then
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
  exit 1
fi

echo "Job ID: $JOB_ID — polling..."
while true; do
  STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
  STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
  case "$STATUS" in
    completed)
      echo "$STATUS_RESPONSE" | jq '.data.result'
      exit 0 ;;
    failed)
      echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"; exit 1 ;;
    *) echo "  Status: $STATUS"; sleep 15 ;;
  esac
done
