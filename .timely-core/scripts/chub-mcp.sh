#!/usr/bin/env bash

set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(basename "$SCRIPT_ROOT")" == ".timely-core" ]]; then
  ROOT_DIR="${TIMELY_REPO_ROOT:-$(cd "$SCRIPT_ROOT/.." && pwd)}"
  RUNTIME_DIR="${TIMELY_RUNTIME_DIR:-$ROOT_DIR/.timely-playbook/runtime}"
else
  ROOT_DIR="${TIMELY_REPO_ROOT:-$SCRIPT_ROOT}"
  RUNTIME_DIR="${TIMELY_RUNTIME_DIR:-$ROOT_DIR}"
fi
CHUB_MCP_BIN="$RUNTIME_DIR/node_modules/.bin/chub-mcp"
if [[ -x "${TIMELY_PLAYBOOK_DIR:-}/bin/chub.sh" ]]; then
  CHUB_WRAPPER="${TIMELY_PLAYBOOK_DIR}/bin/chub.sh"
elif [[ -x "$ROOT_DIR/.timely-playbook/bin/chub.sh" ]]; then
  CHUB_WRAPPER="$ROOT_DIR/.timely-playbook/bin/chub.sh"
elif [[ -x "$ROOT_DIR/.timely-core/scripts/chub.sh" ]]; then
  CHUB_WRAPPER="$ROOT_DIR/.timely-core/scripts/chub.sh"
else
  CHUB_WRAPPER="$ROOT_DIR/scripts/chub.sh"
fi

if [[ ! -x "$CHUB_MCP_BIN" ]]; then
  echo "chub-mcp is not installed locally; run 'npm ci --prefix $RUNTIME_DIR'" >&2
  exit 1
fi

bash "$CHUB_WRAPPER" build >/dev/null
export CHUB_DIR="${CHUB_DIR:-$ROOT_DIR/.chub}"

exec "$CHUB_MCP_BIN" "$@"
