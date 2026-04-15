#!/bin/bash
# Griot - LLM Chat Completions (AnyLLM streaming)
# Usage: ./chat.sh "message" [--provider openai] [--model gpt-4o-mini] [--temp 0.7]

set -e

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
MODEL="gpt-4o-mini"
PROVIDER="openai"
TEMP=""
MAX_TOKENS=""
SYSTEM=""
ACTION="chat"
MESSAGE=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --model) MODEL="$2"; shift 2 ;;
    --provider) PROVIDER="$2"; shift 2 ;;
    --temp) TEMP="$2"; shift 2 ;;
    --max-tokens) MAX_TOKENS="$2"; shift 2 ;;
    --system) SYSTEM="$2"; shift 2 ;;
    --providers) ACTION="providers"; shift ;;
    --models) ACTION="models"; shift ;;
    --help) ACTION="help"; shift ;;
    -*) echo "Unknown option: $1"; exit 1 ;;
    *) MESSAGE="$1"; shift ;;
  esac
done

case "$ACTION" in
  providers)
    echo "Available providers:"
    curl -s "$DAHO_URL/api/v1/anyllm/providers" \
      -H "X-API-Key: $DAHO_API_KEY" | jq '.'
    ;;

  models)
    echo "Models for provider: $PROVIDER"
    curl -s -X POST "$DAHO_URL/api/v1/anyllm/list-models" \
      -H "X-API-Key: $DAHO_API_KEY" \
      -H "Content-Type: application/json" \
      -d "{\"provider\": \"$PROVIDER\"}" | jq '.'
    ;;

  help|chat)
    if [[ -z "$MESSAGE" ]] || [[ "$ACTION" == "help" ]]; then
      echo "Usage: chat.sh \"message\" [options]"
      echo ""
      echo "Options:"
      echo "  --provider PROV     LLM provider (default: openai)"
      echo "  --model MODEL       Model name (default: gpt-4o-mini)"
      echo "  --temp N            Temperature 0-2"
      echo "  --max-tokens N      Max response tokens"
      echo "  --system TEXT       System prompt"
      echo "  --providers         List available providers"
      echo "  --models            List models for a provider"
      echo ""
      echo "Providers: openai, groq, anthropic, mistral, deepseek, xai, openrouter, together..."
      exit 0
    fi

    # Build messages
    MESSAGES=$(jq -n -c --arg msg "$MESSAGE" '[{role: "user", content: $msg}]')
    if [[ -n "$SYSTEM" ]]; then
      MESSAGES=$(echo "$MESSAGES" | jq -c --arg s "$SYSTEM" '[{role: "system", content: $s}] + .')
    fi

    # Build request body (provider is required)
    BODY=$(jq -n -c \
      --arg provider "$PROVIDER" \
      --arg model "$MODEL" \
      --argjson msgs "$MESSAGES" \
      '{provider: $provider, model: $model, messages: $msgs, stream: true}')
    if [[ -n "$TEMP" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$TEMP" '. + {temperature: ($v | tonumber)}'); fi
    if [[ -n "$MAX_TOKENS" ]]; then BODY=$(echo "$BODY" | jq -c --arg v "$MAX_TOKENS" '. + {max_tokens: ($v | tonumber)}'); fi

    # Stream SSE response and extract content deltas
    curl -sN -X POST "$DAHO_URL/api/v1/anyllm/completions" \
      -H "X-API-Key: $DAHO_API_KEY" \
      -H "Content-Type: application/json" \
      -d "$BODY" | while IFS= read -r line; do
        # Skip empty lines and SSE comments
        [[ -z "$line" ]] && continue
        [[ "$line" == ":"* ]] && continue

        # Remove "data: " prefix
        data="${line#data: }"

        # Skip [DONE] marker
        [[ "$data" == "[DONE]" ]] && break

        # Check for error response
        error=$(echo "$data" | jq -r '.error // empty' 2>/dev/null)
        if [[ -n "$error" ]]; then
          echo "Error: $error" >&2
          break
        fi

        # Extract content delta from SSE chunk
        content=$(echo "$data" | jq -r '.choices[0].delta.content // empty' 2>/dev/null)
        if [[ -n "$content" ]]; then
          printf '%s' "$content"
        fi
      done
    echo ""  # Final newline
    ;;
esac
