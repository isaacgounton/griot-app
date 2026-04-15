#!/bin/bash
# Griot - Media Download (yt-dlp)
# Usage: ./download.sh "URL" [--format mp4] [--subtitles] [--thumbnail]

set -e

URL="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
FORMAT=""
SUBTITLES=""
THUMBNAIL=""
COOKIES=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --format) FORMAT="$2"; shift 2 ;;
    --subtitles) SUBTITLES="true"; shift ;;
    --thumbnail) THUMBNAIL="true"; shift ;;
    --cookies) COOKIES="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$URL" ]]; then
  echo "Usage: download.sh \"URL\" [options]"
  echo ""
  echo "Supports YouTube, Vimeo, TikTok, Twitter, and 1000+ sites"
  echo ""
  echo "Options:"
  echo "  --format FORMAT    Output format (mp4, mp3, wav, etc.)"
  echo "  --subtitles        Extract subtitles"
  echo "  --thumbnail        Download thumbnail"
  echo "  --cookies FILE     Cookie file for restricted content"
  exit 1
fi

BODY=$(jq -n -c --arg url "$URL" '{url: $url}')

if [[ -n "$FORMAT" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$FORMAT" '. + {format: $v}')
fi
if [[ "$SUBTITLES" == "true" ]]; then
  BODY=$(echo "$BODY" | jq -c '. + {subtitles: true}')
fi
if [[ "$THUMBNAIL" == "true" ]]; then
  BODY=$(echo "$BODY" | jq -c '. + {thumbnail: true}')
fi
if [[ -n "$COOKIES" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$COOKIES" '. + {cookies: $v}')
fi

echo "Downloading: $URL"

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/media/download" \
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
      exit 0
      ;;
    failed)
      echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"
      exit 1
      ;;
    *) echo "  Status: $STATUS"; sleep 5 ;;
  esac
done
