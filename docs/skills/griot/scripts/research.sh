#!/bin/bash
# Griot - Web/News Research
# Usage: ./research.sh "query" [--type web|news] [--lang code] [--count N]

set -e

QUERY="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
TYPE="web"
LANG=""
COUNT=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --type) TYPE="$2"; shift 2 ;;
    --lang) LANG="$2"; shift 2 ;;
    --count) COUNT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$QUERY" ]]; then
  echo "Usage: research.sh \"query\" [options]"
  echo ""
  echo "Options:"
  echo "  --type TYPE    web or news (default: web)"
  echo "  --lang CODE    Language filter"
  echo "  --count N      Max results"
  exit 1
fi

BODY=$(jq -n -c --arg query "$QUERY" '{query: $query}')

if [[ -n "$LANG" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$LANG" '. + {language: $v}')
fi
if [[ -n "$COUNT" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$COUNT" '. + {max_results: ($v | tonumber)}')
fi

echo "Searching ($TYPE): $QUERY"

RESPONSE=$(curl -s -X POST "$DAHO_URL/api/v1/research/$TYPE" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

echo "$RESPONSE" | jq '.'
