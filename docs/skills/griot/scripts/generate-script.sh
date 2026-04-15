#!/bin/bash
# Griot - Script Generation
# Usage: ./generate-script.sh "topic" [--lang code] [--type type] [--style style] [--duration N]
#
# NOTE: The /api/v1/ai/generate-script endpoint is NOT AVAILABLE on the live instance (404).
# This script uses the /api/v1/ai/research-topic endpoint as a workaround to research a topic
# and generate content that can be used as a script basis. Alternatively, use chat.sh with a
# system prompt to generate scripts via the AnyLLM chat endpoint.

set -e

TOPIC="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
LANG="en"
SCRIPT_TYPE=""
STYLE=""
DURATION=""
AUDIENCE=""
USE_CHAT=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --lang) LANG="$2"; shift 2 ;;
    --type) SCRIPT_TYPE="$2"; shift 2 ;;
    --style) STYLE="$2"; shift 2 ;;
    --duration) DURATION="$2"; shift 2 ;;
    --audience) AUDIENCE="$2"; shift 2 ;;
    --use-chat) USE_CHAT="true"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$TOPIC" ]]; then
  echo "Usage: generate-script.sh \"topic\" [options]"
  echo ""
  echo "NOTE: The dedicated script generation endpoint is not available."
  echo "This script uses /api/v1/ai/research-topic as a workaround,"
  echo "or --use-chat to generate scripts via AnyLLM chat completions."
  echo ""
  echo "Options:"
  echo "  --lang CODE       Language (default: en)"
  echo "  --type TYPE       educational, facts, story, promotional"
  echo "  --style STYLE     engaging, formal, casual, dramatic"
  echo "  --duration N      Target duration in seconds"
  echo "  --audience TEXT    Target audience description"
  echo "  --use-chat        Use AnyLLM chat to generate script (recommended)"
  exit 1
fi

if [[ "$USE_CHAT" == "true" ]]; then
  # Use AnyLLM chat completions as alternative
  SYSTEM_PROMPT="You are a professional video script writer. Write a ${SCRIPT_TYPE:-engaging} script about the given topic in ${LANG}."
  if [[ -n "$STYLE" ]]; then SYSTEM_PROMPT="$SYSTEM_PROMPT Style: $STYLE."; fi
  if [[ -n "$DURATION" ]]; then SYSTEM_PROMPT="$SYSTEM_PROMPT Target duration: ${DURATION} seconds."; fi
  if [[ -n "$AUDIENCE" ]]; then SYSTEM_PROMPT="$SYSTEM_PROMPT Target audience: $AUDIENCE."; fi

  MESSAGES=$(jq -n -c --arg sys "$SYSTEM_PROMPT" --arg msg "$TOPIC" \
    '[{role: "system", content: $sys}, {role: "user", content: $msg}]')

  BODY=$(jq -n -c --argjson msgs "$MESSAGES" \
    '{provider: "openai", model: "gpt-4o-mini", messages: $msgs, stream: true}')

  echo "Generating script via AnyLLM chat about: $TOPIC" >&2

  curl -sN -X POST "$DAHO_URL/api/v1/anyllm/completions" \
    -H "X-API-Key: $DAHO_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$BODY" | while IFS= read -r line; do
      [[ -z "$line" ]] && continue
      [[ "$line" == ":"* ]] && continue
      data="${line#data: }"
      [[ "$data" == "[DONE]" ]] && break
      error=$(echo "$data" | jq -r '.error // empty' 2>/dev/null)
      if [[ -n "$error" ]]; then echo "Error: $error" >&2; break; fi
      content=$(echo "$data" | jq -r '.choices[0].delta.content // empty' 2>/dev/null)
      if [[ -n "$content" ]]; then printf '%s' "$content"; fi
    done
  echo ""
  exit 0
fi

# Fallback: use research-topic endpoint
BODY=$(jq -n -c \
  --arg topic "$TOPIC" \
  --arg lang "$LANG" \
  '{topic: $topic, language: $lang}')

if [[ -n "$SCRIPT_TYPE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$SCRIPT_TYPE" '. + {script_type: $v}')
fi
if [[ -n "$STYLE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$STYLE" '. + {style: $v}')
fi
if [[ -n "$DURATION" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$DURATION" '. + {max_duration: ($v | tonumber)}')
fi
if [[ -n "$AUDIENCE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$AUDIENCE" '. + {target_audience: $v}')
fi

echo "Researching topic (script generation endpoint not available): $TOPIC"
echo "TIP: Use --use-chat for better script generation via AnyLLM." >&2

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/ai/research-topic" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

# Check for async or sync response
JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')
SCRIPT=$(echo "$RESPONSE" | jq -r '.script // .text // .content // empty')

if [[ -n "$SCRIPT" ]]; then
  echo "$SCRIPT"
elif [[ -n "$JOB_ID" ]]; then
  echo "Job ID: $JOB_ID — polling..." >&2
  while true; do
    STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
    case "$STATUS" in
      completed)
        echo "$STATUS_RESPONSE" | jq -r '.data.result.script // .data.result.text // .data.result // empty'
        exit 0
        ;;
      failed)
        echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')" >&2
        exit 1
        ;;
      *)
        sleep 5
        ;;
    esac
  done
else
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
fi
