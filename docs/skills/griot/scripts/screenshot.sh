#!/bin/bash
# Griot - Web Screenshot
# Usage: ./screenshot.sh "URL" [--device mobile] [--full-page] [--output file.png]

set -e

PAGE_URL="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
DEVICE=""
FULL_PAGE=""
FORMAT="png"
QUALITY=""
WIDTH=""
HEIGHT=""
OUTPUT=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --device) DEVICE="$2"; shift 2 ;;
    --full-page) FULL_PAGE="true"; shift ;;
    --format) FORMAT="$2"; shift 2 ;;
    --quality) QUALITY="$2"; shift 2 ;;
    --width) WIDTH="$2"; shift 2 ;;
    --height) HEIGHT="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PAGE_URL" ]]; then
  echo "Usage: screenshot.sh \"URL\" [options]"
  echo ""
  echo "Options:"
  echo "  --device DEVICE    desktop, mobile, tablet"
  echo "  --full-page        Capture full scrollable page"
  echo "  --format FMT       png, jpeg (default: png)"
  echo "  --quality N        JPEG quality 1-100"
  echo "  --width N          Viewport width"
  echo "  --height N         Viewport height"
  echo "  --output FILE      Save to file"
  exit 1
fi

BODY=$(jq -n -c --arg url "$PAGE_URL" --arg fmt "$FORMAT" '{url: $url, format: $fmt}')

if [[ -n "$DEVICE" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$DEVICE" '. + {device: $v}'); fi
if [[ "$FULL_PAGE" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {full_page: true}'); fi
if [[ -n "$QUALITY" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$QUALITY" '. + {quality: ($v | tonumber)}'); fi
if [[ -n "$WIDTH" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$WIDTH" '. + {viewport_width: ($v | tonumber)}'); fi
if [[ -n "$HEIGHT" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$HEIGHT" '. + {viewport_height: ($v | tonumber)}'); fi

echo "Capturing screenshot..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/web_screenshot/capture" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')
IMG_URL=$(echo "$RESPONSE" | jq -r '.url // .image_url // empty')

if [[ -n "$IMG_URL" ]]; then
  if [[ -n "$OUTPUT" ]]; then
    curl -s -o "$OUTPUT" "$IMG_URL"
    echo "Saved to: $OUTPUT"
  else
    echo "Screenshot URL: $IMG_URL"
  fi
elif [[ -n "$JOB_ID" ]]; then
  echo "Job ID: $JOB_ID — polling..."
  while true; do
    STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
    case "$STATUS" in
      completed)
        IMG_URL=$(echo "$STATUS_RESPONSE" | jq -r '.data.result.url // .data.result.image_url // empty')
        if [[ -n "$OUTPUT" ]]; then
          curl -s -o "$OUTPUT" "$IMG_URL"
          echo "Saved to: $OUTPUT"
        else
          echo "Screenshot URL: $IMG_URL"
        fi
        exit 0 ;;
      failed)
        echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"; exit 1 ;;
      *) sleep 5 ;;
    esac
  done
else
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
fi
