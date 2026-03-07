#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
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

if [[ "${run_smoke}" != "true" ]]; then
  echo "smoke check disabled; rerun with --smoke"
  exit 0
fi

OUTPUT_DIR="${WORK_DIR}/seeded"
mkdir -p "${OUTPUT_DIR}"

BIN_DIR="${ROOT_DIR}/.bin"
BIN_PATH="${BIN_DIR}/timely-playbook"

mkdir -p "${BIN_DIR}"
pushd "${ROOT_DIR}" >/dev/null
pushd cmd/timely-playbook >/dev/null
go build -o "${BIN_PATH}" .
popd >/dev/null
"${BIN_PATH}" seed \
  --output "${OUTPUT_DIR}" \
  --owner "Smoke Test" \
  --email "smoke@example.com" \
  --repo "smoke-project" \
  --templated=false \
  --init-git
popd >/dev/null

if [ ! -f "${OUTPUT_DIR}/timely-playbook.yaml" ]; then
  echo "smoke failed: timely-playbook.yaml missing"
  exit 1
fi

if [ ! -d "${OUTPUT_DIR}/.orchestrator" ]; then
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

if [ ! -f "${OUTPUT_DIR}/package.json" ]; then
  echo "smoke failed: package.json missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/scripts/chub.sh" ]; then
  echo "smoke failed: chub wrapper missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/scripts/install-codex-skill.sh" ]; then
  echo "smoke failed: skill installer missing"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/skills/chub-context-hub/SKILL.md" ]; then
  echo "smoke failed: Context Hub skill bundle missing"
  exit 1
fi

if ! grep -Fq "kiss-fullstack-core" "${OUTPUT_DIR}/SKILLS.md"; then
  echo "smoke failed: SKILLS.md missing kiss-fullstack-core policy baseline"
  exit 1
fi

if ! grep -Fq "KISS-to-Codex incorporation policy (A-E)" "${OUTPUT_DIR}/AGENTS.md"; then
  echo "smoke failed: AGENTS.md missing updated A-E incorporation policy"
  exit 1
fi

if [ ! -f "${OUTPUT_DIR}/.git/HEAD" ]; then
  echo "smoke failed: repository was not initialized"
  exit 1
fi

echo "bootstrap smoke test passed"
