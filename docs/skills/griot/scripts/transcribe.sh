#!/bin/bash
# Griot - Audio/Video Transcription (Whisper)
# Usage: ./transcribe.sh FILE_OR_URL [--lang fr] [--format srt]

set -e

INPUT="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
LANG=""
OUTPUT_FORMAT=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --lang) LANG="$2"; shift 2 ;;
    --format) OUTPUT_FORMAT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$INPUT" ]]; then
  echo "Usage: transcribe.sh <file_or_url> [options]"
  echo ""
  echo "Options:"
  echo "  --lang CODE       Language (auto-detect if omitted)"
  echo "  --format FORMAT   Output: text, srt, vtt, json"
  exit 1
fi

# Build form data or JSON based on input type
if [[ -f "$INPUT" ]]; then
  CMD="curl -s -X POST $DAHO_URL/api/v1/audio/transcriptions -H 'X-API-Key: $DAHO_API_KEY' -F 'file=@$INPUT'"
  if [[ -n "$LANG" ]]; then CMD="$CMD -F 'language=$LANG'"; fi
  if [[ -n "$OUTPUT_FORMAT" ]]; then CMD="$CMD -F 'output_format=$OUTPUT_FORMAT'"; fi
  echo "Transcribing file: $INPUT"
  RESPONSE=$(eval "$CMD")
else
  BODY=$(jq -n -c --arg url "$INPUT" '{url: $url}')
  if [[ -n "$LANG" ]]; then
    BODY=$(echo "$BODY" | jq -c --arg v "$LANG" '. + {language: $v}')
  fi
  if [[ -n "$OUTPUT_FORMAT" ]]; then
    BODY=$(echo "$BODY" | jq -c --arg v "$OUTPUT_FORMAT" '. + {output_format: $v}')
  fi
  echo "Transcribing URL: $INPUT"
  RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/audio/transcriptions" \
    -H "X-API-Key: $DAHO_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$BODY")
fi

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')
TEXT=$(echo "$RESPONSE" | jq -r '.text // .transcript // empty')

if [[ -n "$TEXT" ]]; then
  echo "$TEXT"
elif [[ -n "$JOB_ID" ]]; then
  echo "Job ID: $JOB_ID — polling..."
  while true; do
    STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
    case "$STATUS" in
      completed)
        echo "$STATUS_RESPONSE" | jq -r '.data.result.text // .data.result.transcript // .data.result'
        exit 0
        ;;
      failed)
        echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')" >&2
        exit 1
        ;;
      *) sleep 5 ;;
    esac
  done
else
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
fi
