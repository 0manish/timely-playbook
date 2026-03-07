#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bootstrap-timely-template.sh --source /path/to/timely-playbook \
    --output /path/to/new-repo \
    --owner "Your Name" \
    --email "you@example.com" \
    --repo "new-repo-name" \
    [--branch main] [--templated | --inject] [--include-logs] [--init-git]

  bootstrap-timely-template.sh --template-repo https://github.com/<org>/<repo>.git \
    --output /path/to/new-repo \
    --owner "Your Name" \
    --email "you@example.com" \
    --repo "new-repo-name" \
    [--branch main] [--templated | --inject] [--include-logs] [--init-git]

Options:
  --source            Local path to this timely-playbook checkout.
  --template-repo     Remote repo URL to clone before seeding.
  --branch            Branch for cloned template repo (default: main).
  --output            Destination directory for the new project.
  --owner             Operator/owner name inserted into timely-playbook.yaml.
  --email             Operator email inserted into timely-playbook.yaml.
  --repo              Repo name inserted into timely-playbook.yaml.
  --templated         Keep placeholders in exports (default).
  --inject            Inject local values instead of placeholders.
  --include-logs      Include run-logs in the copied template.
  --init-git          Run `git init` in the destination.
  --help              Show this help text.
EOF
}

SOURCE=""
REPO_URL=""
BRANCH="main"
OUTPUT=""
OWNER=""
EMAIL=""
REPO_NAME=""
TEMPLATED=true
INCLUDE_LOGS=false
INIT_GIT=false

while [[ $# -gt 0 ]]; do
  case "$1" in
    --source)
      SOURCE="${2:-}"
      shift 2
      ;;
    --template-repo)
      REPO_URL="${2:-}"
      shift 2
      ;;
    --branch)
      BRANCH="${2:-main}"
      shift 2
      ;;
    --output)
      OUTPUT="${2:-}"
      shift 2
      ;;
    --owner)
      OWNER="${2:-}"
      shift 2
      ;;
    --email)
      EMAIL="${2:-}"
      shift 2
      ;;
    --repo)
      REPO_NAME="${2:-}"
      shift 2
      ;;
    --templated)
      TEMPLATED=true
      shift
      ;;
    --inject)
      TEMPLATED=false
      shift
      ;;
    --include-logs)
      INCLUDE_LOGS=true
      shift
      ;;
    --init-git)
      INIT_GIT=true
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1"
      usage
      exit 1
      ;;
  esac
done

if [[ -z "${OUTPUT}" || -z "${OWNER}" || -z "${EMAIL}" || -z "${REPO_NAME}" ]]; then
  usage
  exit 1
fi

if [[ -z "${SOURCE}" && -z "${REPO_URL}" ]]; then
  usage
  exit 1
fi

if [[ -n "${SOURCE}" && -n "${REPO_URL}" ]]; then
  echo "error: provide exactly one of --source or --template-repo"
  exit 1
fi

if [[ ! -d "${OUTPUT}" ]]; then
  mkdir -p "${OUTPUT}"
fi

if [[ -n "${REPO_URL}" ]]; then
  TMP_DIR="$(mktemp -d)"
  trap 'rm -rf "${TMP_DIR}"' EXIT
  SOURCE="${TMP_DIR}/timely-playbook"
  git clone --depth 1 --branch "${BRANCH}" "${REPO_URL}" "${SOURCE}"
fi

if [[ ! -f "${SOURCE}/cmd/timely-playbook/main.go" ]]; then
  echo "error: ${SOURCE} is not a timely-playbook checkout"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "error: git is required"
  exit 1
fi

if ! command -v go >/dev/null 2>&1; then
  echo "error: go is required"
  exit 1
fi

TEMPLATE_ARGS=(--output "${OUTPUT}" --owner "${OWNER}" --email "${EMAIL}" --repo "${REPO_NAME}")

if [[ "${TEMPLATED}" == "true" ]]; then
  TEMPLATE_ARGS+=(--templated)
else
  TEMPLATE_ARGS+=(--templated=false)
fi

if [[ "${INCLUDE_LOGS}" == "true" ]]; then
  TEMPLATE_ARGS+=(--include-logs)
fi

if [[ "${INIT_GIT}" == "true" ]]; then
  TEMPLATE_ARGS+=(--init-git)
fi

BIN_DIR="${SOURCE}/.bin"
BIN_PATH="${BIN_DIR}/timely-playbook"

mkdir -p "${BIN_DIR}"
pushd "${SOURCE}" >/dev/null
pushd cmd/timely-playbook >/dev/null
go build -o "${BIN_PATH}" .
popd >/dev/null
"${BIN_PATH}" seed "${TEMPLATE_ARGS[@]}"
popd >/dev/null

if [[ ! -f "${OUTPUT}/AGENTS.md" ]]; then
  echo "error: seeded repository is missing AGENTS.md"
  exit 1
fi

if [[ ! -f "${OUTPUT}/SKILLS.md" ]]; then
  echo "error: seeded repository is missing SKILLS.md"
  exit 1
fi

if [[ ! -f "${OUTPUT}/skills/chub-context-hub/SKILL.md" ]]; then
  echo "error: seeded repository is missing the Context Hub skill bundle"
  exit 1
fi

if [[ ! -f "${OUTPUT}/scripts/install-codex-skill.sh" ]]; then
  echo "error: seeded repository is missing the Codex skill installer"
  exit 1
fi
