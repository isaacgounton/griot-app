#!/bin/bash
# Griot - Vision Analysis (analyze images with AI)
# Usage: ./vision.sh IMAGE_URL [--prompt "What is in this image?"]

set -e

IMAGE_URL="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
PROMPT="Describe this image in detail"
MODEL=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --prompt) PROMPT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$IMAGE_URL" ]]; then
  echo "Usage: vision.sh <image_url> [options]"
  echo ""
  echo "Options:"
  echo "  --prompt TEXT    Question about the image (default: 'Describe this image in detail')"
  echo "  --model MODEL    Vision model to use"
  exit 1
fi

BODY=$(jq -n -c --arg url "$IMAGE_URL" --arg question "$PROMPT" \
  '{image_url: $url, question: $question}')

if [[ -n "$MODEL" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$MODEL" '. + {model: $v}')
fi

echo "Analyzing image..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/pollinations/vision/analyze" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')
RESULT=$(echo "$RESPONSE" | jq -r '.result // .analysis // .content // empty')

if [[ -n "$RESULT" ]]; then
  echo "$RESULT"
elif [[ -n "$JOB_ID" ]]; then
  echo "Job ID: $JOB_ID — polling..." >&2
  while true; do
    STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
    case "$STATUS" in
      completed)
        echo "$STATUS_RESPONSE" | jq -r '.data.result.text // .data.result.analysis // .data.result.content // .data.result'
        exit 0 ;;
      failed)
        echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')" >&2; exit 1 ;;
      *) sleep 5 ;;
    esac
  done
else
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
fi
