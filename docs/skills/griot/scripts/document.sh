#!/bin/bash
# Griot - Document Processing (Marker / MarkItDown / LangExtract)
# Usage: ./document.sh FILE_OR_URL [--mode marker|markdown|extract] [--output-format md]

set -e

INPUT="$1"
shift || true

# Defaults
DAHO_URL="${DAHO_URL:-http://localhost:8000}"
MODE="marker"
OUTPUT_FORMAT="markdown"
OCR=""
SCHEMA=""
EXTRACT_PROMPT=""

# Parse args
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="$2"; shift 2 ;;
    --output-format) OUTPUT_FORMAT="$2"; shift 2 ;;
    --ocr) OCR="true"; shift ;;
    --schema) SCHEMA="$2"; shift 2 ;;
    --prompt) EXTRACT_PROMPT="$2"; shift 2 ;;
    *) echo "Unknown option: $1"; exit 1 ;;
  esac
done

if [[ -z "$INPUT" ]]; then
  echo "Usage: document.sh <file_or_url> [options]"
  echo ""
  echo "Modes:"
  echo "  --mode marker      Convert PDF/DOCX/PPTX/HTML/EPUB to markdown (default)"
  echo "  --mode markdown    Convert documents to markdown (MarkItDown)"
  echo "  --mode extract     Extract structured data using AI (LangExtract)"
  echo ""
  echo "Options:"
  echo "  --output-format FMT   markdown, json, html, chunks (marker mode)"
  echo "  --ocr                 Force OCR (marker mode)"
  echo "  --schema FILE         JSON schema for extraction (extract mode)"
  echo "  --prompt TEXT         Extraction prompt (extract mode)"
  exit 1
fi

case "$MODE" in
  marker)
    ENDPOINT="/api/v1/documents/marker/"
    if [[ -f "$INPUT" ]]; then
      CMD="curl -s -X POST $DAHO_URL$ENDPOINT -H 'X-API-Key: $DAHO_API_KEY' -F 'file=@$INPUT' -F 'output_format=$OUTPUT_FORMAT'"
      if [[ "$OCR" == "true" ]]; then CMD="$CMD -F 'force_ocr=true'"; fi
      echo "Converting document (marker)..."
      RESPONSE=$(eval "$CMD")
    else
      BODY=$(jq -n -c --arg url "$INPUT" --arg fmt "$OUTPUT_FORMAT" '{url: $url, output_format: $fmt}')
      if [[ "$OCR" == "true" ]]; then
        BODY=$(echo "$BODY" | jq -c '. + {force_ocr: true}')
      fi
      echo "Converting document (marker)..."
      RESPONSE=$(curl -s -X POST "$DAHO_URL$ENDPOINT" \
        -H "X-API-Key: $DAHO_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$BODY")
    fi
    ;;

  markdown)
    ENDPOINT="/api/v1/documents/"
    if [[ -f "$INPUT" ]]; then
      echo "Converting to markdown..."
      RESPONSE=$(curl -s -X POST "$DAHO_URL$ENDPOINT" \
        -H "X-API-Key: $DAHO_API_KEY" \
        -F "file=@$INPUT")
    else
      echo "Converting to markdown..."
      RESPONSE=$(curl -s -X POST "$DAHO_URL$ENDPOINT" \
        -H "X-API-Key: $DAHO_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$(jq -n -c --arg url "$INPUT" '{url: $url}')")
    fi
    ;;

  extract)
    ENDPOINT="/api/v1/documents/langextract/"
    if [[ -f "$INPUT" ]]; then
      CMD="curl -s -X POST $DAHO_URL$ENDPOINT -H 'X-API-Key: $DAHO_API_KEY' -F 'file=@$INPUT'"
      if [[ -n "$SCHEMA" ]]; then CMD="$CMD -F 'schema=@$SCHEMA'"; fi
      if [[ -n "$EXTRACT_PROMPT" ]]; then CMD="$CMD -F 'prompt=$EXTRACT_PROMPT'"; fi
      echo "Extracting structured data..."
      RESPONSE=$(eval "$CMD")
    else
      BODY=$(jq -n -c --arg url "$INPUT" '{url: $url}')
      if [[ -n "$EXTRACT_PROMPT" ]]; then
        BODY=$(echo "$BODY" | jq -c --arg v "$EXTRACT_PROMPT" '. + {prompt: $v}')
      fi
      echo "Extracting structured data..."
      RESPONSE=$(curl -s -X POST "$DAHO_URL$ENDPOINT" \
        -H "X-API-Key: $DAHO_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$BODY")
    fi
    ;;

  *)
    echo "Unknown mode: $MODE (use marker, markdown, or extract)"
    exit 1
    ;;
esac

JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id // empty')

if [[ -n "$JOB_ID" ]]; then
  echo "Job ID: $JOB_ID — polling..."
  while true; do
    STATUS_RESPONSE=$(curl -s "$DAHO_URL/api/v1/jobs/$JOB_ID/status" -H "X-API-Key: $DAHO_API_KEY")
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.data.status // "unknown"')
    case "$STATUS" in
      completed)
        echo "$STATUS_RESPONSE" | jq '.data.result'
        exit 0 ;;
      failed)
        echo "Failed: $(echo "$STATUS_RESPONSE" | jq -r '.data.error')"; exit 1 ;;
      *) sleep 5 ;;
    esac
  done
else
  echo "$RESPONSE" | jq . 2>/dev/null || echo "$RESPONSE"
fi
