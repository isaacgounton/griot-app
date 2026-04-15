#!/bin/bash
# Initialize music directory
MUSIC_DIR="/app/static/music"

echo "Checking music directory initialization..."
echo "Music dir: $MUSIC_DIR"

# Ensure music directory exists
mkdir -p "$MUSIC_DIR"

# Check music files
MUSIC_FILES=$(ls -1 "$MUSIC_DIR" 2>/dev/null | wc -l)
echo "Music directory has $MUSIC_FILES files"

if [ "$MUSIC_FILES" -gt 0 ]; then
    echo "✅ Music files available - background music will work"
    echo "Sample files:"
    ls -1 "$MUSIC_DIR" | head -3
else
    echo "⚠️  No music files found - background music will be skipped"
    echo "This is expected if using empty volume mounts"
fi

echo "Music initialization complete"