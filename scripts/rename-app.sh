#!/usr/bin/env bash
# rename-app.sh — Rename the app across the entire codebase
#
# Usage:
#   ./scripts/rename-app.sh <OLD_NAME> <NEW_NAME>
#
# Examples:
#   ./scripts/rename-app.sh "Griot" "Griot"
#   ./scripts/rename-app.sh "Griot" "MyApp"
#
# The script handles all common case variants automatically:
#   - "Griot" / "Griot AI"  → Title case with AI suffix
#   - "griot" / "griot-ai"  → Kebab-case
#   - "griot" / "griot_ai"  → Snake_case
#   - "Griot" / "GriotAI"   → CamelCase
#   - "GRIOT" / "GRIOTAI"   → UPPERCASE
#   - "Griot" / "Griot"        → Title case
#   - "griot" / "griot"        → lowercase

set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <OLD_NAME> <NEW_NAME>"
  echo "Example: $0 Griot Griot"
  exit 1
fi

OLD="$1"
NEW="$2"

OLD_LOWER="${OLD,,}"
NEW_LOWER="${NEW,,}"
OLD_UPPER="${OLD^^}"
NEW_UPPER="${NEW^^}"

# Derived variants
OLD_KEBAB="${OLD_LOWER}-ai"
NEW_KEBAB="${NEW_LOWER}"
OLD_SNAKE="${OLD_LOWER}_ai"
NEW_SNAKE="${NEW_LOWER}"
OLD_CAMEL="${OLD}AI"
NEW_CAMEL="${NEW}"
OLD_CAMEL_UPPER="${OLD_UPPER}AI"
NEW_CAMEL_UPPER="${NEW_UPPER}"
OLD_WITH_AI="${OLD} AI"
NEW_WITH_AI="${NEW}"

echo "Renaming app: '$OLD' → '$NEW'"
echo ""

# ── 1. Content replacements ────────────────────────────────────────────────

# File extensions to process
EXTENSIONS="py ts tsx js jsx json toml yaml yml html md sh env"

# Build find command for all target extensions
FIND_ARGS=()
for ext in $EXTENSIONS; do
  FIND_ARGS+=(-o -name "*.${ext}")
done
# Remove leading -o
FIND_ARGS=("${FIND_ARGS[@]:1}")

# Files to process (exclude node_modules, .git, dist, __pycache__, venv)
FILES=$(find . \
  \( -path ./node_modules -o -path ./.git -o -path ./frontend/node_modules \
     -o -path ./dist -o -path ./__pycache__ -o -path ./venv -o -path ./.venv \) \
  -prune -o \
  \( "${FIND_ARGS[@]}" \) -print)

# Detect sed flavor (GNU vs macOS)
if sed --version 2>/dev/null | grep -q GNU; then
  SED_INPLACE="sed -i"
else
  SED_INPLACE="sed -i ''"
fi

replace_in_files() {
  local pattern="$1"
  local replacement="$2"
  local count=0
  while IFS= read -r file; do
    if grep -qF -- "$pattern" "$file" 2>/dev/null; then
      $SED_INPLACE "s|${pattern}|${replacement}|g" "$file"
      echo "  [content] $file"
      ((count++)) || true
    fi
  done <<< "$FILES"
  echo "  → $count file(s) updated for: '$pattern' → '$replacement'"
  echo ""
}

echo "=== Replacing content in files ==="
echo ""

# Order matters: most specific patterns first
replace_in_files "${OLD_WITH_AI}"      "${NEW_WITH_AI}"
replace_in_files "${OLD_KEBAB}"        "${NEW_KEBAB}"
replace_in_files "${OLD_SNAKE}"        "${NEW_SNAKE}"
replace_in_files "${OLD_CAMEL}"        "${NEW_CAMEL}"
replace_in_files "${OLD_CAMEL_UPPER}"  "${NEW_CAMEL_UPPER}"
replace_in_files "${OLD}"              "${NEW}"
replace_in_files "${OLD_LOWER}"        "${NEW_LOWER}"

# ── 2. File renames ────────────────────────────────────────────────────────

echo "=== Renaming files ==="
echo ""

rename_file() {
  local old_path="$1"
  local new_path="$2"
  if [[ -f "$old_path" ]]; then
    git mv "$old_path" "$new_path" 2>/dev/null || mv "$old_path" "$new_path"
    echo "  [rename] $old_path → $new_path"
  fi
}

rename_dir() {
  local old_path="$1"
  local new_path="$2"
  if [[ -d "$old_path" ]]; then
    git mv "$old_path" "$new_path" 2>/dev/null || mv "$old_path" "$new_path"
    echo "  [rename] $old_path/ → $new_path/"
  fi
}

# Known files that include the old name
rename_file "frontend/src/types/${OLD_LOWER}.ts"        "frontend/src/types/${NEW_LOWER}.ts"
rename_file "frontend/src/services/${OLD_LOWER}Api.ts"  "frontend/src/services/${NEW_LOWER}Api.ts"
rename_dir  "docs/skills/${OLD_LOWER}-ai"               "docs/skills/${NEW_LOWER}"
rename_dir  "docs/skills/${OLD_LOWER}"                  "docs/skills/${NEW_LOWER}"

# Rename any remaining files that contain the old name in their filename
find . \
  \( -path ./node_modules -o -path ./.git -o -path ./frontend/node_modules \
     -o -path ./dist -o -path ./__pycache__ -o -path ./venv -o -path ./.venv \) \
  -prune -o -type f -print | while IFS= read -r file; do
  basename=$(basename "$file")
  dir=$(dirname "$file")
  if echo "$basename" | grep -qi "${OLD_LOWER}"; then
    new_basename=$(echo "$basename" | sed "s|${OLD_LOWER}|${NEW_LOWER}|gI")
    if [[ "$basename" != "$new_basename" ]]; then
      new_file="${dir}/${new_basename}"
      git mv "$file" "$new_file" 2>/dev/null || mv "$file" "$new_file"
      echo "  [rename] $file → $new_file"
    fi
  fi
done

echo ""
echo "Done! '$OLD' has been renamed to '$NEW' throughout the codebase."
echo ""
echo "Next steps:"
echo "  1. Review changes: git diff --stat"
echo "  2. Check for missed references: grep -r '${OLD_LOWER}' . --include='*.py' --include='*.ts' --include='*.tsx'"
echo "  3. Rebuild frontend: cd frontend && npm install && npm run build"
echo "  4. Commit: git add -A && git commit -m 'refactor: rename app from ${OLD} to ${NEW}'"
