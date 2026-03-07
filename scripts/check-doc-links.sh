#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CONFIG="$ROOT/.markdown-link-check.json"
LOCAL_BIN="$ROOT/node_modules/.bin/markdown-link-check"
DOCS=(
  "AGENTS.md"
  "AutomationPlaybook-GettingStarted.md"
  "AutonomousAgentTracking.md"
  "Conductor-Orchestration.md"
  "Context-Hub-Integration.md"
  "FullStack-Agent-Integration.md"
  "HOWTO.md"
  "Timely-Governance-Index.md"
  "Timely-Governance-Trackers.md"
  "Timely-Flowgraph.md"
  "TimelyPlaybook.md"
  "timely-trackers/agent-control-ledger.md"
  "timely-trackers/ceremony-agendas.md"
  "timely-trackers/spec-traceability.md"
  "timely-trackers/test-run-journal.md"
  "timely-trackers/todo-backlog.md"
)

if [[ -x "$LOCAL_BIN" ]]; then
  LINKCHECK_BIN="$LOCAL_BIN"
elif command -v markdown-link-check >/dev/null 2>&1; then
  LINKCHECK_BIN="$(command -v markdown-link-check)"
else
  echo "markdown-link-check not found; run 'npm ci' from $ROOT or install markdown-link-check globally" >&2
  exit 1
fi

ARGS=()
if [[ -f "$CONFIG" ]]; then
  ARGS+=("-c" "$CONFIG")
fi

for file in "${DOCS[@]}"; do
  if [[ -f "$ROOT/$file" ]]; then
    echo "Checking links in $file"
    "$LINKCHECK_BIN" "${ARGS[@]}" "$ROOT/$file"
  fi
done
