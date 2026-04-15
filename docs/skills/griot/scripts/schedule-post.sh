#!/bin/bash
# Griot - Social Media Scheduling (Postiz)
# Usage: ./schedule-post.sh "content" --integrations ID1,ID2 [--media URL] [--now]

set -e

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
CONTENT=""
INTEGRATIONS=""
MEDIA=""
SCHEDULE_DATE=""
POST_TYPE="schedule"
LIST_INTEGRATIONS=""
GENERATE=""
GENERATE_TOPIC=""

# Parse args — positional content detected by absence of --
while [[ $# -gt 0 ]]; do
  case "$1" in
    --integrations) INTEGRATIONS="$2"; shift 2 ;;
    --media) MEDIA="$2"; shift 2 ;;
    --date) SCHEDULE_DATE="$2"; shift 2 ;;
    --now) POST_TYPE="now"; shift ;;
    --draft) POST_TYPE="draft"; shift ;;
    --list-integrations) LIST_INTEGRATIONS="true"; shift ;;
    --generate) GENERATE="true"; GENERATE_TOPIC="$2"; shift 2 ;;
    --*) echo "Unknown option: $1"; exit 1 ;;
    *) CONTENT="$1"; shift ;;
  esac
done

# List integrations
if [[ "$LIST_INTEGRATIONS" == "true" ]]; then
  echo "Fetching Postiz integrations..."
  curl -s "$DAHO_URL/api/v1/postiz/integrations" \
    -H "X-API-Key: $DAHO_API_KEY" | jq '.'
  exit 0
fi

# Generate content with AI
if [[ "$GENERATE" == "true" ]]; then
  echo "Generating content for: $GENERATE_TOPIC"
  curl -s -X POST "$DAHO_URL/api/v1/postiz/generate-content" \
    -H "X-API-Key: $DAHO_API_KEY" \
    -H "Content-Type: application/json" \
    -d "$(jq -n -c --arg topic "$GENERATE_TOPIC" '{topic: $topic}')" | jq '.'
  exit 0
fi

if [[ -z "$CONTENT" ]] || [[ -z "$INTEGRATIONS" ]]; then
  echo "Usage: schedule-post.sh \"content\" --integrations ID1,ID2 [options]"
  echo ""
  echo "Options:"
  echo "  --integrations IDS  Comma-separated integration IDs (use --list-integrations to find)"
  echo "  --media URL         Attach video/image URL"
  echo "  --now               Post immediately"
  echo "  --date ISODATE      Schedule for date (e.g., 2026-03-01T10:00:00Z)"
  echo "  --draft             Save as draft"
  echo "  --list-integrations List available Postiz integrations"
  echo "  --generate TOPIC    Generate content with AI for a topic"
  exit 1
fi

# Convert comma-separated to JSON array
INTEGRATIONS_JSON=$(echo "$INTEGRATIONS" | tr ',' '\n' | jq -R . | jq -s .)

BODY=$(jq -n -c \
  --arg content "$CONTENT" \
  --argjson integrations "$INTEGRATIONS_JSON" \
  '{content: $content, integrations: $integrations}')

if [[ -n "$MEDIA" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$MEDIA" '. + {media_urls: [$v]}')
fi
if [[ -n "$SCHEDULE_DATE" ]]; then
  BODY=$(echo "$BODY" | jq -c --arg v "$SCHEDULE_DATE" '. + {schedule_date: $v}')
fi

echo "Scheduling post ($POST_TYPE)..."

if [[ "$POST_TYPE" == "now" ]]; then
  ENDPOINT="/api/v1/postiz/schedule-now"
elif [[ "$POST_TYPE" == "draft" ]]; then
  ENDPOINT="/api/v1/postiz/create-draft"
else
  ENDPOINT="/api/v1/postiz/schedule"
fi

RESPONSE=$(curl -s -X POST "$DAHO_URL$ENDPOINT" \
  -H "X-API-Key: $DAHO_API_KEY" \
  -H "Content-Type: application/json" \
  -d "$BODY")

echo "$RESPONSE" | jq '.'
