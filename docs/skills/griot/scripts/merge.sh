#!/bin/bash
# Griot - Merge Videos
# Usage: ./merge.sh url1 url2 [url3...] [--transition dissolve] [--duration 0.5]

set -e

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
TRANSITION="dissolve"
TRANS_DURATION="0.5"
URLS_FILE=""
URLS=()

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --transition) TRANSITION="$2"; shift 2 ;;
    --duration) TRANS_DURATION="$2"; shift 2 ;;
    --file) URLS_FILE="$2"; shift 2 ;;
    --*) echo "Unknown option: $1"; exit 1 ;;
    *) URLS+=("$1"); shift ;;
  esac
done

# Read URLs from file if specified
if [[ -n "$URLS_FILE" ]]; then
  while IFS= read -r line; do
    [[ -n "$line" ]] && URLS+=("$line")
  done < "$URLS_FILE"
fi

if [[ ${#URLS[@]} -lt 2 ]]; then
  echo "Usage: merge.sh <url1> <url2> [url3...] [options]"
  echo ""
  echo "Options:"
  echo "  --transition TYPE    none, fade, dissolve, slide, wipe (default: dissolve)"
  echo "  --duration N         Transition seconds (default: 0.5)"
  echo "  --file FILE          Read URLs from file (one per line)"
  exit 1
fi

# Build JSON array of URLs
URLS_JSON=$(printf '%s\n' "${URLS[@]}" | jq -R . | jq -s .)

BODY=$(jq -n -c \
  --argjson urls "$URLS_JSON" \
  --arg transition "$TRANSITION" \
  --arg duration "$TRANS_DURATION" \
  '{
    video_urls: $urls,
    transition: $transition,
    transition_duration: ($duration | tonumber)
  }')

echo "Merging ${#URLS[@]} videos (transition: $TRANSITION)..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/videos/merge" \
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
      echo "Done! Merged video: $RESULT_URL"
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
