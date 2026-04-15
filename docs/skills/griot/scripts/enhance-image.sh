#!/bin/bash
# Griot - Image Enhancement
# Usage: ./enhance-image.sh IMAGE_URL [--color] [--contrast] [--grain] [--vintage]

set -e

IMAGE_URL="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
COLOR=""
CONTRAST=""
GRAIN=""
VINTAGE=""
FORMAT=""
QUALITY=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --color) COLOR="true"; shift ;;
    --contrast) CONTRAST="true"; shift ;;
    --grain) GRAIN="true"; shift ;;
    --vintage) VINTAGE="true"; shift ;;
    --format) FORMAT="$2"; shift 2 ;;
    --quality) QUALITY="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$IMAGE_URL" ]]; then
  echo "Usage: enhance-image.sh <image_url> [options]"
  echo ""
  echo "Options:"
  echo "  --color        Enhance colors"
  echo "  --contrast     Improve contrast"
  echo "  --grain        Add film grain"
  echo "  --vintage      Apply vintage effect"
  echo "  --format FMT   Output format (jpg, png, webp)"
  echo "  --quality N    Output quality 1-100"
  exit 1
fi

BODY=$(jq -n -c --arg url "$IMAGE_URL" '{image_url: $url}')

if [[ "$COLOR" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {color_enhance: true}'); fi
if [[ "$CONTRAST" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {contrast_enhance: true}'); fi
if [[ "$GRAIN" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {film_grain: true}'); fi
if [[ "$VINTAGE" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {vintage: true}'); fi
if [[ -n "$FORMAT" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$FORMAT" '. + {output_format: $v}'); fi
if [[ -n "$QUALITY" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$QUALITY" '. + {quality: ($v | tonumber)}'); fi

echo "Enhancing image..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/images/enhance" \
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
      echo "Done! $(echo "$STATUS_RESPONSE" | jq -r '.data.result.url // .data.result.image_url // .data.result')"
      exit 0 ;;
    failed)
      echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"; exit 1 ;;
    *) sleep 5 ;;
  esac
done
