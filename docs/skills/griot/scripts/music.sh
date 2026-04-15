#!/bin/bash
# Griot - Background Music Tracks
# Usage: ./music.sh [--mood epic] [--search "keyword"] [--limit 10]

set -e

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
MOOD=""
SEARCH=""
LIMIT="10"
ACTION="list"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mood) MOOD="$2"; shift 2 ;;
    --search) SEARCH="$2"; shift 2 ;;
    --limit) LIMIT="$2"; shift 2 ;;
    --moods) ACTION="moods"; shift ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

case "$ACTION" in
  list)
    PARAMS="limit=$LIMIT"
    if [[ -n "$MOOD" ]]; then PARAMS="$PARAMS&mood=$MOOD"; fi
    if [[ -n "$SEARCH" ]]; then PARAMS="$PARAMS&search=$SEARCH"; fi

    echo "Available tracks:"
    curl -s "$DAHO_URL/api/v1/music/tracks?$PARAMS" \
      -H "X-API-Key: $DAHO_API_KEY" | jq '.'
    ;;

  moods)
    echo "Available moods:"
    curl -s "$DAHO_URL/api/v1/music/moods" \
      -H "X-API-Key: $DAHO_API_KEY" | jq '.'
    ;;
esac
