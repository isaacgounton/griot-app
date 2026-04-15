#!/bin/bash
# Griot - Extract Video Clips
# Usage: ./clips.sh VIDEO_URL --start 10 --end 30
# Usage: ./clips.sh VIDEO_URL --query "the funniest moment"

set -e

VIDEO_URL="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
START=""
END=""
QUERY=""
FORMAT="mp4"
QUALITY="medium"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --start) START="$2"; shift 2 ;;
    --end) END="$2"; shift 2 ;;
    --query) QUERY="$2"; shift 2 ;;
    --format) FORMAT="$2"; shift 2 ;;
    --quality) QUALITY="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$VIDEO_URL" ]]; then
  echo "Usage: clips.sh <video_url> [options]"
  echo ""
  echo "Manual extraction:"
  echo "  --start N         Start time in seconds"
  echo "  --end N           End time in seconds"
  echo ""
  echo "AI-powered extraction:"
  echo "  --query TEXT      Natural language search (e.g., 'the climax scene')"
  echo ""
  echo "Common options:"
  echo "  --format FMT      mp4, webm, avi, mov, mkv (default: mp4)"
  echo "  --quality LVL     low, medium, high (default: medium)"
  exit 1
fi

BODY=$(jq -n -c --arg url "$VIDEO_URL" --arg fmt "$FORMAT" --arg q "$QUALITY" \
  '{video_url: $url, format: $fmt, quality: $q}')

if [[ -n "$QUERY" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$QUERY" '. + {query: $v}')
elif [[ -n "$START" ]] && [[ -n "$END" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg s "$START" --arg e "$END" \
    '. + {segments: [{start: ($s | tonumber), end: ($e | tonumber)}]}')
else
  echo "Error: Provide either --start/--end or --query"
  exit 1
fi

echo "Extracting clip..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/videos/clips" \
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
    *) echo "  Status: $STATUS"; sleep 10 ;;
  esac
done
