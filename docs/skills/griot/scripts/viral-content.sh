#!/bin/bash
# Griot - Simone Viral Content Generator
# Usage: ./viral-content.sh VIDEO_URL [--platforms twitter,instagram] [--threads 5]

set -e

VIDEO_URL="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
PLATFORMS=""
THREAD_COUNT=""
COOKIES=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --platforms) PLATFORMS="$2"; shift 2 ;;
    --threads) THREAD_COUNT="$2"; shift 2 ;;
    --cookies) COOKIES="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$VIDEO_URL" ]]; then
  echo "Usage: viral-content.sh <video_url> [options]"
  echo ""
  echo "Generates from video:"
  echo "  - Topic identification"
  echo "  - X/Twitter threads (up to 8 posts)"
  echo "  - Multi-platform posts (Twitter, LinkedIn, Instagram)"
  echo "  - Blog content"
  echo "  - Hashtag suggestions"
  echo ""
  echo "Options:"
  echo "  --platforms LIST   Comma-separated platforms"
  echo "  --threads N        Max thread posts (default: 5)"
  echo "  --cookies FILE     Cookie file for restricted videos"
  exit 1
fi

BODY=$(jq -n -c --arg url "$VIDEO_URL" '{video_url: $url}')

if [[ -n "$PLATFORMS" ]]; then
  PLATFORMS_JSON=$(echo "$PLATFORMS" | tr ',' '\n' | jq -R . | jq -s .)
  BODY=$(echo "$BODY" | jq -c --argjson v "$PLATFORMS_JSON" '. + {platforms: $v}')
fi
if [[ -n "$THREAD_COUNT" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$THREAD_COUNT" '. + {max_threads: ($v | tonumber)}')
fi
if [[ -n "$COOKIES" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$COOKIES" '. + {cookies: $v}')
fi

echo "Generating viral content..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/simone/viral-content" \
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
