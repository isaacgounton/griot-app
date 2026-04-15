#!/bin/bash
# Griot - Text-to-Speech
# Usage: ./tts.sh "text" [--provider edge] [--voice voice] [--speed N] [--format mp3]

set -e

TEXT="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
PROVIDER="edge"
VOICE=""
SPEED="1.0"
FORMAT="mp3"
OUTPUT=""
TEXT_FILE=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --provider) PROVIDER="$2"; shift 2 ;;
    --voice) VOICE="$2"; shift 2 ;;
    --speed) SPEED="$2"; shift 2 ;;
    --format) FORMAT="$2"; shift 2 ;;
    --output) OUTPUT="$2"; shift 2 ;;
    --file) TEXT_FILE="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

# Read from file if specified
if [[ -n "$TEXT_FILE" ]]; then
  TEXT=$(cat "$TEXT_FILE")
fi

if [[ -z "$TEXT" ]]; then
  echo "Usage: tts.sh \"text\" [options]"
  echo ""
  echo "Options:"
  echo "  --provider PROV   edge (300+ voices), kokoro (natural), kitten (fast), pollinations"
  echo "  --voice VOICE     Voice name"
  echo "  --speed N         Speed 0.5-2.0 (default: 1.0)"
  echo "  --format FMT      mp3, wav, ogg, aac (default: mp3)"
  echo "  --output FILE     Output filename"
  echo "  --file FILE       Read text from file"
  echo ""
  echo "Popular voices:"
  echo "  edge: en-US-GuyNeural, en-US-JennyNeural, fr-FR-HenriNeural, es-ES-AlvaroNeural"
  echo "  kokoro: af_bella, am_adam, bf_emma"
  echo "  pollinations: alloy, echo, nova, onyx, fable, shimmer"
  exit 1
fi

# Set default voice per provider if not specified
if [[ -z "$VOICE" ]]; then
  case "$PROVIDER" in
    edge) VOICE="en-US-GuyNeural" ;;
    kokoro) VOICE="af_bella" ;;
    kitten) VOICE="expr-voice-2-m" ;;
    pollinations) VOICE="nova" ;;
    *) VOICE="en-US-GuyNeural" ;;
  esac
fi

# Set output filename
if [[ -z "$OUTPUT" ]]; then
  OUTPUT="speech_$(date +%s).$FORMAT"
fi

BODY=$(jq -n -c \
  --arg text "$TEXT" \
  --arg provider "$PROVIDER" \
  --arg voice "$VOICE" \
  --arg speed "$SPEED" \
  --arg format "$FORMAT" \
  '{
    text: $text,
    provider: $provider,
    voice: $voice,
    speed: ($speed | tonumber),
    output_format: $format
  }')

echo "Generating speech with $PROVIDER ($VOICE)..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/audio/speech" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

# Check if async job or direct URL
JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')
AUDIO_URL=$(echo "$RESPONSE" | jq -r '.url // .audio_url // empty')

if [[ -n "$AUDIO_URL" ]]; then
  curl -s -o "$OUTPUT" "$AUDIO_URL"
  FILE_SIZE=$(ls -lh "$OUTPUT" | awk '{print $5}')
  echo "Saved to: $OUTPUT ($FILE_SIZE)"
elif [[ -n "$JOB_ID" ]]; then
  echo "Job ID: $JOB_ID — polling..."
  while true; do
    STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
    case "$STATUS" in
      completed)
        AUDIO_URL=$(echo "$STATUS_RESPONSE" | jq -r '.data.result.url // .data.result.audio_url // empty')
        curl -s -o "$OUTPUT" "$AUDIO_URL"
        FILE_SIZE=$(ls -lh "$OUTPUT" | awk '{print $5}')
        echo "Saved to: $OUTPUT ($FILE_SIZE)"
        exit 0
        ;;
      failed)
        echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"
        exit 1
        ;;
      *)
        sleep 3
        ;;
    esac
  done
else
  echo "Error:"
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
  exit 1
fi
