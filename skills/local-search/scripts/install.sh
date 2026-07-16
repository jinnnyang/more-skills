#!/usr/bin/env bash
# Install/refresh the local-search CLI as a uv tool (editable).
#
# Idempotent: safe to re-run after pulling changes; the --force flag
# refreshes the venv contents without disturbing the CLI on PATH.
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "→ Installing local-search from $SKILL_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "  [FAIL] uv not found. Install from https://astral.sh/uv" >&2
    exit 1
fi

uv tool install --editable "$SKILL_DIR" --force
echo

echo "→ Verifying"
local-search --version
echo
local-search doctor || true
echo
echo "✅ Done. Run 'local-search --help' to see commands."
