#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")/scripts" && pwd)"

echo "=============================="
echo "  dotfiles setup"
echo "=============================="
echo ""

"$SCRIPT_DIR/link.sh"
echo ""
"$SCRIPT_DIR/binaries.sh"
echo ""
"$SCRIPT_DIR/setup.sh"
echo ""
"$SCRIPT_DIR/completions.sh"
