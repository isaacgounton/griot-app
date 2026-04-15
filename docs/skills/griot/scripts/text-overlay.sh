#!/bin/bash
# Griot - Text Overlay on Video
# Usage: ./text-overlay.sh VIDEO_URL "text" [--position center] [--font-size 48] [--color "#FFF"]

set -e

VIDEO_URL="$1"
TEXT="$2"
shift 2 2>/dev/null || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
FONT_SIZE=""
FONT_COLOR=""
FONT_FAMILY=""
POSITION=""
BG_COLOR=""
BG_OPACITY=""
START_TIME=""
DURATION=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --font-size) FONT_SIZE="$2"; shift 2 ;;
    --color) FONT_COLOR="$2"; shift 2 ;;
    --font) FONT_FAMILY="$2"; shift 2 ;;
    --position) POSITION="$2"; shift 2 ;;
    --bg-color) BG_COLOR="$2"; shift 2 ;;
    --bg-opacity) BG_OPACITY="$2"; shift 2 ;;
    --start) START_TIME="$2"; shift 2 ;;
    --duration) DURATION="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$VIDEO_URL" ]] || [[ -z "$TEXT" ]]; then
  echo "Usage: text-overlay.sh <video_url> \"text\" [options]"
  echo ""
  echo "Options:"
  echo "  --font-size N       Font size (default: 48)"
  echo "  --color HEX         Text color (default: #FFFFFF)"
  echo "  --font FAMILY       Font family"
  echo "  --position POS      top_left, top_center, top_right, center_left, center,"
  echo "                      center_right, bottom_left, bottom_center, bottom_right"
  echo "  --bg-color HEX      Background box color"
  echo "  --bg-opacity N      Background opacity 0.0-1.0"
  echo "  --start N           Start time in seconds"
  echo "  --duration N        Display duration in seconds"
  exit 1
fi

# Build text element
TEXT_OBJ=$(jq -n -c --arg text "$TEXT" '{text: $text}')
if [[ -n "$FONT_SIZE" ]]; then TEXT_OBJ=$(echo "$TEXT_OBJ" | jq -c --arg v "$FONT_SIZE" '. + {font_size: ($v | tonumber)}'); fi
if [[ -n "$FONT_COLOR" ]]; then TEXT_OBJ=$(echo "$TEXT_OBJ" | jq -c --arg v "$FONT_COLOR" '. + {font_color: $v}'); fi
if [[ -n "$FONT_FAMILY" ]]; then TEXT_OBJ=$(echo "$TEXT_OBJ" | jq -c --arg v "$FONT_FAMILY" '. + {font_family: $v}'); fi
if [[ -n "$POSITION" ]]; then TEXT_OBJ=$(echo "$TEXT_OBJ" | jq -c --arg v "$POSITION" '. + {position: $v}'); fi
if [[ -n "$BG_COLOR" ]]; then TEXT_OBJ=$(echo "$TEXT_OBJ" | jq -c --arg v "$BG_COLOR" '. + {bg_color: $v}'); fi
if [[ -n "$BG_OPACITY" ]]; then TEXT_OBJ=$(echo "$TEXT_OBJ" | jq -c --arg v "$BG_OPACITY" '. + {bg_opacity: ($v | tonumber)}'); fi
if [[ -n "$START_TIME" ]]; then TEXT_OBJ=$(echo "$TEXT_OBJ" | jq -c --arg v "$START_TIME" '. + {start_time: ($v | tonumber)}'); fi
if [[ -n "$DURATION" ]]; then TEXT_OBJ=$(echo "$TEXT_OBJ" | jq -c --arg v "$DURATION" '. + {duration: ($v | tonumber)}'); fi

BODY=$(jq -n -c --arg url "$VIDEO_URL" --argjson text_obj "$TEXT_OBJ" '{video_url: $url, texts: [$text_obj]}')

echo "Adding text overlay..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/videos/text-overlay" \
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
