#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
export TIMELY_REPO_ROOT="${TIMELY_REPO_ROOT:-$ROOT_DIR}"
export TIMELY_CORE_DIR="${TIMELY_CORE_DIR:-$ROOT_DIR/.timely-core}"
export TIMELY_PLAYBOOK_DIR="${TIMELY_PLAYBOOK_DIR:-$ROOT_DIR/.timely-playbook}"
export TIMELY_LOCAL_DIR="${TIMELY_LOCAL_DIR:-$ROOT_DIR/.timely-playbook/local}"
export TIMELY_RUNTIME_DIR="${TIMELY_RUNTIME_DIR:-$ROOT_DIR/.timely-playbook/runtime}"
export TIMELY_CONFIG_PATH="${TIMELY_CONFIG_PATH:-$ROOT_DIR/.timely-playbook/config.yaml}"
export PYTHONPATH="$ROOT_DIR/.timely-core${PYTHONPATH:+:$PYTHONPATH}"

exec bash "$ROOT_DIR/.timely-core/scripts/bootstrap-smoke.sh" "$@"
