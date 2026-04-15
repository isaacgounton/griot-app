#!/bin/bash
# Griot - AI Video Generation from Text Prompt
# Usage: ./video-generate.sh "prompt" [--provider pollinations] [--width 512] [--height 512]

set -e

PROMPT="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
PROVIDER="pollinations"
WIDTH=""
HEIGHT=""
FRAMES=""
SEED=""
NEGATIVE=""
AUDIO=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --provider) PROVIDER="$2"; shift 2 ;;
    --width) WIDTH="$2"; shift 2 ;;
    --height) HEIGHT="$2"; shift 2 ;;
    --frames) FRAMES="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --negative) NEGATIVE="$2"; shift 2 ;;
    --audio) AUDIO="true"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$PROMPT" ]]; then
  echo "Usage: video-generate.sh \"prompt\" [options]"
  echo ""
  echo "Options:"
  echo "  --provider PROV    ltx_video, wavespeed, comfyui, pollinations (default: pollinations)"
  echo "  --width N          Width 256-1024"
  echo "  --height N         Height 256-1024"
  echo "  --frames N         Frame count (1-257)"
  echo "  --seed N           Reproducibility seed"
  echo "  --negative TEXT    Negative prompt (what to avoid)"
  echo "  --audio            Generate with audio (pollinations only)"
  exit 1
fi

BODY=$(jq -n -c --arg prompt "$PROMPT" --arg provider "$PROVIDER" \
  '{prompt: $prompt, provider: $provider}')

if [[ -n "$WIDTH" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$WIDTH" '. + {width: ($v | tonumber)}'); fi
if [[ -n "$HEIGHT" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$HEIGHT" '. + {height: ($v | tonumber)}'); fi
if [[ -n "$FRAMES" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$FRAMES" '. + {num_frames: ($v | tonumber)}'); fi
if [[ -n "$SEED" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$SEED" '. + {seed: ($v | tonumber)}'); fi
if [[ -n "$NEGATIVE" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$NEGATIVE" '. + {negative_prompt: $v}'); fi
if [[ "$AUDIO" == "true" ]]; then BODY=$(echo "$BODY" | jq -c '. + {audio: true}'); fi

echo "Generating AI video ($PROVIDER)..."

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/videos/generate" \
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
      echo "Done! $(echo "$STATUS_RESPONSE" | jq -r '.data.result.url // .data.result.video_url // .data.result')"
      exit 0 ;;
    failed)
      echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"; exit 1 ;;
    *) echo "  Status: $STATUS"; sleep 15 ;;
  esac
done
