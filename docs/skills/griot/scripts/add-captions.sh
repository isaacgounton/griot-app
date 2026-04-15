#!/bin/bash
# Griot - Add Captions to Video
# Usage: ./add-captions.sh VIDEO_URL [--style karaoke] [--color "#FFFFFF"] [--lang fr]

set -e

VIDEO_URL="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
STYLE=""
FONT=""
SIZE=""
BOLD=""
COLOR=""
HIGHLIGHT=""
OUTLINE=""
POSITION=""
LANG=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --style) STYLE="$2"; shift 2 ;;
    --font) FONT="$2"; shift 2 ;;
    --size) SIZE="$2"; shift 2 ;;
    --bold) BOLD="true"; shift ;;
    --color) COLOR="$2"; shift 2 ;;
    --highlight) HIGHLIGHT="$2"; shift 2 ;;
    --outline) OUTLINE="$2"; shift 2 ;;
    --position) POSITION="$2"; shift 2 ;;
    --lang) LANG="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$VIDEO_URL" ]]; then
  echo "Usage: add-captions.sh <video_url> [options]"
  echo ""
  echo "Options:"
  echo "  --style STYLE       classic, karaoke, highlight, underline, word_by_word, viral_bounce"
  echo "  --font FAMILY       Font family (e.g., Montserrat)"
  echo "  --size N            Font size"
  echo "  --bold              Bold text"
  echo "  --color HEX         Text color (default: #FFFFFF)"
  echo "  --highlight HEX     Word highlight color"
  echo "  --outline HEX       Outline color"
  echo "  --position POS      bottom_center, top_center, center, etc."
  echo "  --lang CODE         Language code for auto-detection"
  exit 1
fi

BODY=$(jq -n -c --arg url "$VIDEO_URL" '{video_url: $url}')

if [[ -n "$STYLE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$STYLE" '. + {style: $v}')
fi
if [[ -n "$FONT" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$FONT" '. + {font_family: $v}')
fi
if [[ -n "$SIZE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$SIZE" '. + {font_size: ($v | tonumber)}')
fi
if [[ "$BOLD" == "true" ]]; then
  BODY=$(echo "$BODY" | jq -c '. + {font_bold: true}')
fi
if [[ -n "$COLOR" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$COLOR" '. + {line_color: $v}')
fi
if [[ -n "$HIGHLIGHT" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$HIGHLIGHT" '. + {word_highlight_color: $v}')
fi
if [[ -n "$OUTLINE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$OUTLINE" '. + {outline_color: $v}')
fi
if [[ -n "$POSITION" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$POSITION" '. + {position: $v}')
fi
if [[ -n "$LANG" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$LANG" '. + {language: $v}')
fi

echo "Adding captions${STYLE:+ ($STYLE)}..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/videos/add-captions" \
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
      echo "Done! Captioned video: $RESULT_URL"
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
