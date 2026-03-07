#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHUB_MCP_BIN="$ROOT_DIR/node_modules/.bin/chub-mcp"

if [[ ! -x "$CHUB_MCP_BIN" ]]; then
  echo "chub-mcp is not installed locally; run 'npm ci' from $ROOT_DIR" >&2
  exit 1
fi

bash "$ROOT_DIR/scripts/chub.sh" build >/dev/null
export CHUB_DIR="${CHUB_DIR:-$ROOT_DIR/.chub}"

exec "$CHUB_MCP_BIN" "$@"
