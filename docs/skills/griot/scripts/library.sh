#!/bin/bash
# Griot - Media Library
# Usage: ./library.sh [--type video] [--search "keyword"] [--limit 20]

set -e

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
CONTENT_TYPE=""
SEARCH=""
LIMIT="20"
OFFSET="0"
ACTION="list"
MEDIA_ID=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --type) CONTENT_TYPE="$2"; shift 2 ;;
    --search) SEARCH="$2"; shift 2 ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --offset) OFFSET="$2"; shift 2 ;;
    --stats) ACTION="stats"; shift ;;
    --get) ACTION="get"; MEDIA_ID="$2"; shift 2 ;;
    --favorite) ACTION="favorite"; MEDIA_ID="$2"; shift 2 ;;
    --delete) ACTION="delete"; MEDIA_ID="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

case "$ACTION" in
  list)
    PARAMS="limit=$LIMIT&offset=$OFFSET"
    if [[ -n "$CONTENT_TYPE" ]]; then PARAMS="$PARAMS&content_type=$CONTENT_TYPE"; fi
    if [[ -n "$SEARCH" ]]; then PARAMS="$PARAMS&search=$SEARCH"; fi

    echo "Listing library content..."
    curl -s "$DAHO_URL/api/v1/library/content?$PARAMS" \
      -H "X-API-Key: $DAHO_API_KEY" | jq '.'
    ;;

  stats)
    echo "Library statistics:"
    curl -s "$DAHO_URL/api/v1/library/stats" \
      -H "X-API-Key: $DAHO_API_KEY" | jq '.'
    ;;

  get)
    if [[ -z "$MEDIA_ID" ]]; then echo "Error: --get requires a media ID"; exit 1; fi
    curl -s "$DAHO_URL/api/v1/library/content/$MEDIA_ID" \
      -H "X-API-Key: $DAHO_API_KEY" | jq '.'
    ;;

  favorite)
    if [[ -z "$MEDIA_ID" ]]; then echo "Error: --favorite requires a media ID"; exit 1; fi
    curl -s -X POST "$DAHO_URL/api/v1/library/favorite/$MEDIA_ID" \
      -H "X-API-Key: $DAHO_API_KEY" | jq '.'
    ;;

  delete)
    if [[ -z "$MEDIA_ID" ]]; then echo "Error: --delete requires a media ID"; exit 1; fi
    curl -s -X DELETE "$DAHO_URL/api/v1/library/content/$MEDIA_ID" \
      -H "X-API-Key: $DAHO_API_KEY" | jq '.'
    ;;
esac
