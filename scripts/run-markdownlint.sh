#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$ROOT/.markdownlint.json"
LOCAL_BIN="$ROOT/node_modules/.bin/markdownlint"

if [[ -x "$LOCAL_BIN" ]]; then
  MARKDOWNLINT_BIN="$LOCAL_BIN"
elif command -v markdownlint >/dev/null 2>&1; then
  MARKDOWNLINT_BIN="$(command -v markdownlint)"
else
  echo "markdownlint not found; run 'npm ci' from $ROOT or install markdownlint-cli globally" >&2
  exit 1
fi

cd "$ROOT"

TMP="$(mktemp)"
trap 'rm -f "$TMP"' EXIT

if [[ -d "$ROOT/.git" ]] && command -v git >/dev/null 2>&1; then
  git ls-files -z '*.md' >"$TMP"
else
  find . \
    -path './.chub' -prune -o \
    -path './dist' -prune -o \
    -path './node_modules' -prune -o \
    -path './.orchestrator/upstream' -prune -o \
    -path './run-logs' -prune -o \
    -name '*.md' -print0 >"$TMP"
fi

if [[ ! -s "$TMP" ]]; then
  echo "No Markdown files to lint."
  exit 0
fi

ARGS=()
if [[ -f "$CONFIG" ]]; then
  ARGS+=("-c" "$CONFIG")
fi

xargs -0 "$MARKDOWNLINT_BIN" "${ARGS[@]}" <"$TMP"
