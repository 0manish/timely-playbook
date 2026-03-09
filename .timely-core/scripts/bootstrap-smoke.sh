#!/usr/bin/env bash

set -euo pipefail

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(basename "$SCRIPT_ROOT")" == ".timely-core" ]]; then
  ROOT_DIR="$(cd "$SCRIPT_ROOT/.." && pwd)"
else
  ROOT_DIR="$SCRIPT_ROOT"
fi
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

run_smoke=false

if [[ $# -gt 0 ]]; then
  if [[ "$1" != "--smoke" ]]; then
    echo "unknown argument: $1"
    echo "usage: $0 --smoke"
    exit 1
  fi
  run_smoke=true
fi

if ! command -v go >/dev/null 2>&1; then
  echo "go not found; install Go 1.22+ to run bootstrap smoke test"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "git not found; install git to run bootstrap smoke test"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm not found; install npm to run bootstrap smoke test"
  exit 1
fi

if ! command -v python >/dev/null 2>&1; then
  echo "python not found; install python to run bootstrap smoke test"
  exit 1
fi

if [[ "${run_smoke}" != "true" ]]; then
  echo "smoke check disabled; rerun with --smoke"
  exit 0
fi

OUTPUT_DIR="${WORK_DIR}/seeded"
mkdir -p "${OUTPUT_DIR}"

pushd "${ROOT_DIR}" >/dev/null
unset TIMELY_REPO_ROOT TIMELY_CORE_DIR TIMELY_PLAYBOOK_DIR TIMELY_LOCAL_DIR TIMELY_RUNTIME_DIR TIMELY_BIN_DIR TIMELY_CONFIG_PATH
bash .timely-playbook/bin/timely-playbook seed \
  --output "${OUTPUT_DIR}" \
  --owner "Smoke Test" \
  --email "smoke@example.com" \
  --repo "smoke-project" \
  --templated=false \
  --init-git
popd >/dev/null

pushd "${OUTPUT_DIR}" >/dev/null
python .timely-playbook/bin/orchestrator.py context-sync >/dev/null
popd >/dev/null

if [ -f "${OUTPUT_DIR}/timely-playbook.yaml" ]; then
  echo "smoke failed: legacy timely-playbook.yaml should not be present"
  exit 1
fi

if [ ! -d "${OUTPUT_DIR}/.timely-playbook/local/.orchestrator" ]; then
  echo "smoke failed: orchestrator config missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/AGENTS.md" ]; then
  echo "smoke failed: AGENTS.md missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/SKILLS.md" ]; then
  echo "smoke failed: SKILLS.md missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.timely-playbook/runtime/package.json" ]; then
  echo "smoke failed: runtime package.json missing"
  exit 1
fi

if [ ! -x "${OUTPUT_DIR}/.timely-playbook/runtime/node_modules/.bin/chub" ]; then
  echo "smoke failed: chub runtime dependency was not preinstalled"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.timely-playbook/bin/chub.sh" ]; then
  echo "smoke failed: chub wrapper missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.timely-playbook/bin/install-agent-skill.sh" ]; then
  echo "smoke failed: generic skill installer missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.timely-playbook/bin/bootstrap-timely-release.sh" ]; then
  echo "smoke failed: release bootstrap script missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.timely-playbook/bin/install-codex-skill.sh" ]; then
  echo "smoke failed: Codex compatibility skill installer missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.timely-playbook/local/skills/chub-context-hub/SKILL.md" ]; then
  echo "smoke failed: Context Hub skill bundle missing"
  exit 1
fi

if ! grep -Fq ".timely-playbook/local/SKILLS.md" "${OUTPUT_DIR}/SKILLS.md"; then
  echo "smoke failed: SKILLS.md missing kiss-fullstack-core policy baseline"
  exit 1
fi

if ! grep -Fq ".timely-playbook/local/AGENTS.md" "${OUTPUT_DIR}/AGENTS.md"; then
  echo "smoke failed: AGENTS.md missing updated A-E incorporation policy"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.timely-core/manifest.json" ]; then
  echo "smoke failed: core manifest missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.timely-playbook/config.yaml" ]; then
  echo "smoke failed: relocated config missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.timely-playbook/local/.cxdb/cxdb.sqlite3" ]; then
  echo "smoke failed: CXDB store missing after context sync"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.timely-playbook/local/.leann/index.json" ]; then
  echo "smoke failed: LEANN index missing after context sync"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.chub/config.yaml" ]; then
  echo "smoke failed: chub config was not prepared by default"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.chub/timely-dist/.metadata.json" ] && [ ! -d "${OUTPUT_DIR}/.chub/timely-dist" ]; then
  echo "smoke failed: chub dist was not built by default"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.gitignore" ]; then
  echo "smoke failed: root .gitignore missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.github/workflows/release.yml" ]; then
  echo "smoke failed: root release workflow missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.git/HEAD" ]; then
  echo "smoke failed: repository was not initialized"
  exit 1
fi

echo "bootstrap smoke test passed"
