#!/bin/bash
# Griot - Simone Video-to-Blog
# Usage: ./video-to-blog.sh VIDEO_URL [--social] [--screenshots]

set -e

VIDEO_URL="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
SOCIAL=""
SCREENSHOTS=""
COOKIES=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --social) SOCIAL="true"; shift ;;
    --screenshots) SCREENSHOTS="true"; shift ;;
    --cookies) COOKIES="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$VIDEO_URL" ]]; then
  echo "Usage: video-to-blog.sh <video_url> [options]"
  echo ""
  echo "Converts video into a full blog post with:"
  echo "  - AI-generated article"
  echo "  - Screenshots from video"
  echo "  - Optional social media posts"
  echo ""
  echo "Options:"
  echo "  --social          Generate social media posts too"
  echo "  --screenshots     Include video screenshots"
  echo "  --cookies FILE    Cookie file for restricted videos"
  exit 1
fi

BODY=$(jq -n -c --arg url "$VIDEO_URL" '{video_url: $url}')

if [[ "$SOCIAL" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {social_posts: true}'); fi
if [[ "$SCREENSHOTS" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {screenshots: true}'); fi
if [[ -n "$COOKIES" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$COOKIES" '. + {cookies: $v}'); fi

echo "Converting video to blog..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/simone/video-to-blog" \
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
