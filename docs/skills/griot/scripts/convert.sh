#!/bin/bash
# Griot - Media Format Conversion
# Usage: ./convert.sh FILE_OR_URL --to mp3 [--quality high]

set -e

INPUT="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
TO_FORMAT=""
QUALITY=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --to) TO_FORMAT="$2"; shift 2 ;;
    --quality) QUALITY="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$INPUT" ]] || [[ -z "$TO_FORMAT" ]]; then
  echo "Usage: convert.sh <file_or_url> --to <format> [options]"
  echo ""
  echo "Options:"
  echo "  --to FORMAT       Target format (mp4, mp3, wav, webm, gif, png, jpg, etc.)"
  echo "  --quality LEVEL   low, medium, high"
  echo ""
  echo "Supports video, audio, and image conversions"
  exit 1
fi

if [[ -f "$INPUT" ]]; then
  CMD="curl -s -X POST $DAHO_URL/api/v1/media/conversions/ -H 'X-API-Key: $DAHO_API_KEY' -F 'file=@$INPUT' -F 'output_format=$TO_FORMAT'"
  if [[ -n "$QUALITY" ]]; then CMD="$CMD -F 'quality=$QUALITY'"; fi
  echo "Converting to $TO_FORMAT..."
  RESPONSE=$(eval "$CMD")
else
  BODY=$(jq -n -c --arg url "$INPUT" --arg fmt "$TO_FORMAT" '{url: $url, output_format: $fmt}')
  if [[ -n "$QUALITY" ]]; then
    BODY=$(echo "$BODY" | jq -c --arg v "$QUALITY" '. + {quality: $v}')
  fi
  echo "Converting to $TO_FORMAT..."
  RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/media/conversions/" \
    -H "X-API-Key: $DAHO_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$BODY")
fi

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')
RESULT_URL=$(echo "$RESPONSE" | jq -r '.url // empty')

if [[ -n "$RESULT_URL" ]]; then
  echo "Done! URL: $RESULT_URL"
elif [[ -n "$JOB_ID" ]]; then
  echo "Job ID: $JOB_ID — polling..."
  while true; do
    STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
    case "$STATUS" in
      completed)
        echo "Done! $(echo "$STATUS_RESPONSE" | jq -r '.data.result.url // .data.result')"
        exit 0 ;;
      failed)
        echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"; exit 1 ;;
      *) sleep 5 ;;
    esac
  done
else
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
fi
