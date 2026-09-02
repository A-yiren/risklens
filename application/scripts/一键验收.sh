#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BASE_URL="${1:-https://fangzhou.chat/risklens/}"
python3 "$SCRIPT_DIR/one_click_acceptance.py" --online "$BASE_URL"
