#!/usr/bin/env bash

set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(basename "$SCRIPT_ROOT")" == ".timely-core" ]]; then
  ROOT_DIR="${TIMELY_REPO_ROOT:-$(cd "$SCRIPT_ROOT/.." && pwd)}"
  CORE_DIR="${TIMELY_CORE_DIR:-$SCRIPT_ROOT}"
  RUNTIME_DIR="${TIMELY_RUNTIME_DIR:-$ROOT_DIR/.timely-playbook/runtime}"
else
  ROOT_DIR="${TIMELY_REPO_ROOT:-$SCRIPT_ROOT}"
  CORE_DIR="${TIMELY_CORE_DIR:-$SCRIPT_ROOT}"
  RUNTIME_DIR="${TIMELY_RUNTIME_DIR:-$ROOT_DIR}"
fi
CHUB_HOME="${CHUB_DIR:-${TIMELY_CHUB_DIR:-$ROOT_DIR/.chub}}"
CHUB_BIN="$RUNTIME_DIR/node_modules/.bin/chub"
export PYTHONPATH="$CORE_DIR${PYTHONPATH:+:$PYTHONPATH}"

if [[ ! -x "$CHUB_BIN" ]]; then
  echo "chub is not installed locally; run 'npm ci --prefix $RUNTIME_DIR'" >&2
  exit 1
fi

export CHUB_DIR="$CHUB_HOME"

python "$CORE_DIR/tools/chub/timely_registry.py" \
  --repo-root "$ROOT_DIR" \
  --chub-dir "$CHUB_HOME" \
  --sync-community-search-index >/dev/null

SOURCE_DIR="$CHUB_HOME/timely-source"
DIST_DIR="$CHUB_HOME/timely-dist"

build_local_dist() {
  "$CHUB_BIN" build "$SOURCE_DIR" -o "$DIST_DIR" "$@"
}

if [[ $# -eq 0 ]]; then
  exec "$CHUB_BIN" --help
fi

case "$1" in
  build)
    shift
    exec "$CHUB_BIN" build "$SOURCE_DIR" -o "$DIST_DIR" "$@"
    ;;
  validate)
    shift
    exec "$CHUB_BIN" build "$SOURCE_DIR" -o "$DIST_DIR" --validate-only "$@"
    ;;
  update)
    shift
    "$CHUB_BIN" update "$@"
    python "$CORE_DIR/tools/chub/timely_registry.py" \
      --repo-root "$ROOT_DIR" \
      --chub-dir "$CHUB_HOME" \
      --sync-community-search-index \
      --force-community-search-index >/dev/null
    ;;
  *)
    build_local_dist >/dev/null
    exec "$CHUB_BIN" "$@"
    ;;
esac
