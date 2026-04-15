#!/bin/bash
# Griot - Job Status
# Usage: ./job-status.sh JOB_ID [--wait] [--interval N]

set -e

JOB_ID="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
WAIT=""
INTERVAL="10"

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --wait) WAIT="true"; shift ;;
    --interval) INTERVAL="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$JOB_ID" ]]; then
  echo "Usage: job-status.sh <job_id> [options]"
  echo ""
  echo "Options:"
  echo "  --wait           Poll until completion"
  echo "  --interval N     Poll interval in seconds (default: 10)"
  exit 1
fi

if [[ "$WAIT" != "true" ]]; then
  # Single check
  curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" \
    -H "X-API-Key: $DAHO_API_KEY" | jq '.'
  exit 0
fi

# Poll until done
echo "Waiting for job $JOB_ID..."
while true; do
  RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
  STATUS=$(echo "$RESPONSE" | jq -r '.data.status // "unknown"')

  case "$STATUS" in
    completed)
      echo "$RESPONSE" | jq '.'
      exit 0
      ;;
    failed)
      echo "$RESPONSE" | jq '.'
      exit 1
      ;;
    *)
      echo "  Status: $STATUS"
      sleep "$INTERVAL"
      ;;
  esac
done
