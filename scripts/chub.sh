#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CHUB_HOME="${CHUB_DIR:-$ROOT_DIR/.chub}"
CHUB_BIN="$ROOT_DIR/node_modules/.bin/chub"

if [[ ! -x "$CHUB_BIN" ]]; then
  echo "chub is not installed locally; run 'npm ci' from $ROOT_DIR" >&2
  exit 1
fi

export CHUB_DIR="$CHUB_HOME"

python "$ROOT_DIR/tools/chub/timely_registry.py" \
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
    python "$ROOT_DIR/tools/chub/timely_registry.py" \
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
