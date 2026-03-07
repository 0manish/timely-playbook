#!/usr/bin/env bash
set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
if [[ "$(basename "$SCRIPT_ROOT")" == ".timely-core" ]]; then
  ROOT="${TIMELY_REPO_ROOT:-$(cd "$SCRIPT_ROOT/.." && pwd)}"
  CORE_DIR="${TIMELY_CORE_DIR:-$SCRIPT_ROOT}"
  LOCAL_DIR="${TIMELY_LOCAL_DIR:-$ROOT/.timely-playbook/local}"
  RUNTIME_DIR="${TIMELY_RUNTIME_DIR:-$ROOT/.timely-playbook/runtime}"
else
  ROOT="${TIMELY_REPO_ROOT:-$SCRIPT_ROOT}"
  CORE_DIR="${TIMELY_CORE_DIR:-$SCRIPT_ROOT}"
  LOCAL_DIR="${TIMELY_LOCAL_DIR:-$ROOT}"
  RUNTIME_DIR="${TIMELY_RUNTIME_DIR:-$ROOT}"
fi
CONFIG="${TIMELY_LINKCHECK_CONFIG:-$CORE_DIR/.markdown-link-check.json}"
LOCAL_BIN="$RUNTIME_DIR/node_modules/.bin/markdown-link-check"
DOCS=()

if [[ "$CORE_DIR" == "$ROOT" ]]; then
  DOCS=(
    "README.md"
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
else
  DOCS=(
    "README.md"
    ".timely-playbook/local/AGENTS.md"
    ".timely-playbook/local/SKILLS.md"
    ".timely-playbook/local/timely-trackers/agent-control-ledger.md"
    ".timely-playbook/local/timely-trackers/ceremony-agendas.md"
    ".timely-playbook/local/timely-trackers/spec-traceability.md"
    ".timely-playbook/local/timely-trackers/test-run-journal.md"
    ".timely-playbook/local/timely-trackers/todo-backlog.md"
    ".timely-core/AutomationPlaybook-GettingStarted.md"
    ".timely-core/Conductor-Orchestration.md"
    ".timely-core/Context-Hub-Integration.md"
    ".timely-core/FullStack-Agent-Integration.md"
    ".timely-core/HOWTO.md"
    ".timely-core/Timely-Governance-Index.md"
    ".timely-core/Timely-Governance-Trackers.md"
    ".timely-core/Timely-Flowgraph.md"
    ".timely-core/TimelyPlaybook.md"
  )
fi

if [[ -x "$LOCAL_BIN" ]]; then
  LINKCHECK_BIN="$LOCAL_BIN"
elif command -v markdown-link-check >/dev/null 2>&1; then
  LINKCHECK_BIN="$(command -v markdown-link-check)"
else
  echo "markdown-link-check not found; run 'npm ci --prefix $RUNTIME_DIR' or install markdown-link-check globally" >&2
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
