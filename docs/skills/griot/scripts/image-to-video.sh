#!/bin/bash
# Griot - Image to Video (animate static images)
# Usage: ./image-to-video.sh IMAGE_URL [--motion ken_burns] [--narration "text"] [--music epic]

set -e

IMAGE_URL="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
MOTION=""
NARRATION=""
MUSIC=""
TTS_PROVIDER=""
TTS_VOICE=""
CAPTIONS=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --motion) MOTION="$2"; shift 2 ;;
    --narration) NARRATION="$2"; shift 2 ;;
    --music) MUSIC="$2"; shift 2 ;;
    --tts-provider) TTS_PROVIDER="$2"; shift 2 ;;
    --tts-voice) TTS_VOICE="$2"; shift 2 ;;
    --captions) CAPTIONS="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$IMAGE_URL" ]]; then
  echo "Usage: image-to-video.sh <image_url> [options]"
  echo ""
  echo "Options:"
  echo "  --motion EFFECT       ken_burns, zoom, pan, fade"
  echo "  --narration TEXT      Add TTS narration"
  echo "  --music MOOD          Background: epic, chill, sad, happy, upbeat"
  echo "  --tts-provider PROV   edge, kokoro, kitten, pollinations"
  echo "  --tts-voice VOICE     Voice name"
  echo "  --captions STYLE      viral_bounce, karaoke, standard_bottom"
  exit 1
fi

BODY=$(jq -n -c --arg url "$IMAGE_URL" '{image_url: $url}')

if [[ -n "$MOTION" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$MOTION" '. + {motion_effect: $v}'); fi
if [[ -n "$NARRATION" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$NARRATION" '. + {narration_text: $v}'); fi
if [[ -n "$MUSIC" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$MUSIC" '. + {background_music: $v}'); fi
if [[ -n "$TTS_PROVIDER" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$TTS_PROVIDER" '. + {tts_provider: $v}'); fi
if [[ -n "$TTS_VOICE" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$TTS_VOICE" '. + {tts_voice: $v}'); fi
if [[ -n "$CAPTIONS" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$CAPTIONS" '. + {caption_style: $v}'); fi

echo "Converting image to video..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/videos/from_image" \
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
      echo "Done! $(echo "$STATUS_RESPONSE" | jq -r '.data.result.url // .data.result.video_url // .data.result')"
      exit 0 ;;
    failed)
      echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"; exit 1 ;;
    *) echo "  Status: $STATUS"; sleep 10 ;;
  esac
done
