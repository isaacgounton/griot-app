#!/bin/bash
# Griot - AI Image Generation
# Usage: ./image.sh "prompt" [--width N] [--height N] [--model flux] [--enhance] [--output file]

set -e

PROMPT="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
WIDTH="1024"
HEIGHT="1024"
MODEL="flux"
ENHANCE=""
SEED=""
NOLOGO=""
OUTPUT=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --width) WIDTH="$2"; shift 2 ;;
    --height) HEIGHT="$2"; shift 2 ;;
    --model) MODEL="$2"; shift 2 ;;
    --enhance) ENHANCE="true"; shift ;;
    --seed) SEED="$2"; shift 2 ;;
    --nologo) NOLOGO="true"; shift ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROMPT" ]]; then
  echo "Usage: image.sh \"prompt\" [options]"
  echo ""
  echo "Options:"
  echo "  --width N       Width 256-2048 (default: 1024)"
  echo "  --height N      Height 256-2048 (default: 1024)"
  echo "  --model MODEL   Model name (default: flux)"
  echo "  --enhance       AI-improve the prompt"
  echo "  --seed N        Reproducibility seed"
  echo "  --nologo        Remove watermark"
  echo "  --output FILE   Output filename"
  exit 1
fi

BODY=$(jq -n -c \
  --arg prompt "$PROMPT" \
  --arg width "$WIDTH" \
  --arg height "$HEIGHT" \
  --arg model "$MODEL" \
  '{
    prompt: $prompt,
    width: ($width | tonumber),
    height: ($height | tonumber),
    model: $model
  }')

if [[ "$ENHANCE" == "true" ]]; then
  BODY=$(echo "$BODY" | jq -c '. + {enhance: true}')
fi
if [[ -n "$SEED" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$SEED" '. + {seed: ($v | tonumber)}')
fi
if [[ "$NOLOGO" == "true" ]]; then
  BODY=$(echo "$BODY" | jq -c '. + {nologo: true}')
fi

echo "Generating image (${WIDTH}x${HEIGHT}, $MODEL)..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/pollinations/image/generate" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')
IMAGE_URL=$(echo "$RESPONSE" | jq -r '.url // .image_url // empty')

if [[ -n "$IMAGE_URL" ]]; then
  if [[ -n "$OUTPUT" ]]; then
    curl -s -o "$OUTPUT" "$IMAGE_URL"
    echo "Saved to: $OUTPUT"
  else
    echo "Image URL: $IMAGE_URL"
  fi
elif [[ -n "$JOB_ID" ]]; then
  echo "Job ID: $JOB_ID — polling..."
  while true; do
    STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
    case "$STATUS" in
      completed)
        IMAGE_URL=$(echo "$STATUS_RESPONSE" | jq -r '.data.result.url // .data.result.image_url // empty')
        if [[ -n "$OUTPUT" ]]; then
          curl -s -o "$OUTPUT" "$IMAGE_URL"
          echo "Saved to: $OUTPUT"
        else
          echo "Image URL: $IMAGE_URL"
        fi
        exit 0
        ;;
      failed)
        echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"
        exit 1
        ;;
      *)
        echo "  Status: $STATUS"
        sleep 5
        ;;
    esac
  done
else
  echo "Error:"
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
  exit 1
fi
