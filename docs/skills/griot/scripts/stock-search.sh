#!/bin/bash
# Griot - Stock Media Search
# Usage: ./stock-search.sh "query" [--type video|image] [--count N] [--orientation portrait]

set -e

QUERY="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
TYPE="video"
COUNT="5"
ORIENTATION=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --type) TYPE="$2"; shift 2 ;;
    --count) COUNT="$2"; shift 2 ;;
    --orientation) ORIENTATION="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$QUERY" ]]; then
  echo "Usage: stock-search.sh \"query\" [options]"
  echo ""
  echo "Options:"
  echo "  --type TYPE            video or image (default: video)"
  echo "  --count N              Number of results (default: 5)"
  echo "  --orientation ORI      landscape, portrait, square"
  exit 1
fi

BODY=$(jq -n -c \
  --arg query "$QUERY" \
  --arg count "$COUNT" \
  '{query: $query, per_page: ($count | tonumber)}')

if [[ -n "$ORIENTATION" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$ORIENTATION" '. + {orientation: $v}')
fi

if [[ "$TYPE" == "video" ]]; then
  ENDPOINT="/api/v1/ai/video-search/stock-videos"
else
  ENDPOINT="/api/v1/ai/image-search/stock-images"
fi

echo "Searching $TYPE: $QUERY"

RESPONSE=$(curl -s -X POST "$DAHO_URL$ENDPOINT" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

# Check if async job
JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')

if [[ -n "$JOB_ID" ]]; then
  echo "Job ID: $JOB_ID — polling..."
  while true; do
    STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
    case "$STATUS" in
      completed)
        echo "$STATUS_RESPONSE" | jq '.data.result'
        exit 0 ;;
      failed)
        echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"
        exit 1 ;;
      *) sleep 3 ;;
    esac
  done
else
  echo "$RESPONSE" | jq '.'
fi
