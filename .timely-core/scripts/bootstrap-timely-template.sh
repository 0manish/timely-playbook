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
    [--branch main] [--templated | --inject] [--include-logs] [--init-git] [--skip-runtime-setup]

  bootstrap-timely-template.sh --template-repo https://github.com/<org>/<repo>.git \
    --output /path/to/new-repo \
    --owner "Your Name" \
    --email "you@example.com" \
    --repo "new-repo-name" \
    [--branch main] [--templated | --inject] [--include-logs] [--init-git] [--skip-runtime-setup]

Options:
  --source            Local path to this timely-playbook checkout.
  --template-repo     Remote repo URL to clone before seeding.
  --branch            Branch for cloned template repo (default: main).
  --output            Destination directory for the new project.
  --owner             Operator/owner name inserted into .timely-playbook/config.yaml.
  --email             Operator email inserted into .timely-playbook/config.yaml.
  --repo              Repo name inserted into .timely-playbook/config.yaml.
  --templated         Keep placeholders in exports (default).
  --inject            Inject local values instead of placeholders.
  --include-logs      Include run-logs in the copied template.
  --init-git          Run `git init` in the destination.
  --skip-runtime-setup Skip the default npm install and initial chub build.
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
SKIP_RUNTIME_SETUP=false

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
    --skip-runtime-setup)
      SKIP_RUNTIME_SETUP=true
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

if [[ ! -f "${SOURCE}/cmd/timely-playbook/main.go" && ! -f "${SOURCE}/.timely-core/cmd/timely-playbook/main.go" && ! -x "${SOURCE}/.timely-playbook/bin/timely-playbook" ]]; then
  echo "error: ${SOURCE} is not a timely-playbook checkout"
  exit 1
fi

if ! command -v git >/dev/null 2>&1; then
  echo "error: git is required"
  exit 1
fi

if ! command -v go >/dev/null 2>&1 && ! command -v timely-playbook >/dev/null 2>&1; then
  echo "error: install Go 1.22+ or place timely-playbook on PATH"
  exit 1
fi

if [[ "${SKIP_RUNTIME_SETUP}" != "true" ]]; then
  if ! command -v npm >/dev/null 2>&1; then
    echo "error: npm is required unless --skip-runtime-setup is used"
    exit 1
  fi
  if ! command -v python >/dev/null 2>&1; then
    echo "error: python is required unless --skip-runtime-setup is used"
    exit 1
  fi
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

if [[ "${SKIP_RUNTIME_SETUP}" == "true" ]]; then
  TEMPLATE_ARGS+=(--skip-runtime-setup)
fi

unset TIMELY_REPO_ROOT TIMELY_CORE_DIR TIMELY_PLAYBOOK_DIR TIMELY_LOCAL_DIR TIMELY_RUNTIME_DIR TIMELY_BIN_DIR TIMELY_CONFIG_PATH

pushd "${SOURCE}" >/dev/null
if [[ -x "${SOURCE}/.timely-playbook/bin/timely-playbook" ]]; then
  "${SOURCE}/.timely-playbook/bin/timely-playbook" seed "${TEMPLATE_ARGS[@]}"
elif command -v timely-playbook >/dev/null 2>&1 && ! command -v go >/dev/null 2>&1; then
  timely-playbook seed "${TEMPLATE_ARGS[@]}"
else
  BIN_DIR="${SOURCE}/.bin"
  BIN_PATH="${BIN_DIR}/timely-playbook"
  if [[ -f "${SOURCE}/.timely-core/cmd/timely-playbook/main.go" ]]; then
    MODULE_DIR="${SOURCE}/.timely-core/cmd/timely-playbook"
  else
    MODULE_DIR="${SOURCE}/cmd/timely-playbook"
  fi

  mkdir -p "${BIN_DIR}"
  pushd "${MODULE_DIR}" >/dev/null
  go build -o "${BIN_PATH}" .
  popd >/dev/null
  "${BIN_PATH}" seed "${TEMPLATE_ARGS[@]}"
fi
popd >/dev/null

if [[ ! -f "${OUTPUT}/AGENTS.md" ]]; then
  echo "error: seeded repository is missing AGENTS.md"
  exit 1
fi

if [[ ! -f "${OUTPUT}/SKILLS.md" ]]; then
  echo "error: seeded repository is missing SKILLS.md"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.agents/README.md" ]]; then
  echo "error: seeded repository is missing .agents/README.md"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.timely-playbook/local/skills/chub-context-hub/SKILL.md" ]]; then
  echo "error: seeded repository is missing the Context Hub skill bundle"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.timely-playbook/local/skills/project-agent-harness/SKILL.md" ]]; then
  echo "error: seeded repository is missing the project agent harness skill bundle"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.timely-playbook/local/agent-harness/templates/agents-readme-sync.md" ]]; then
  echo "error: seeded repository is missing the agent roster README sync template"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.timely-playbook/bin/install-agent-skill.sh" ]]; then
  echo "error: seeded repository is missing the generic skill installer"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.timely-playbook/bin/bootstrap-timely-release.sh" ]]; then
  echo "error: seeded repository is missing the release bootstrap script"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.timely-playbook/bin/install-codex-skill.sh" ]]; then
  echo "error: seeded repository is missing the Codex compatibility skill installer"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.timely-playbook/config.yaml" ]]; then
  echo "error: seeded repository is missing .timely-playbook/config.yaml"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.timely-core/manifest.json" ]]; then
  echo "error: seeded repository is missing .timely-core/manifest.json"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.timely-playbook/local/.cxdb/README.md" ]]; then
  echo "error: seeded repository is missing the CXDB directory scaffold"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.timely-playbook/local/.leann/README.md" ]]; then
  echo "error: seeded repository is missing the LEANN directory scaffold"
  exit 1
fi

if [[ "${SKIP_RUNTIME_SETUP}" != "true" ]]; then
  if [[ ! -x "${OUTPUT}/.timely-playbook/runtime/node_modules/.bin/chub" ]]; then
    echo "error: seeded repository is missing the preinstalled chub runtime"
    exit 1
  fi
  if [[ ! -f "${OUTPUT}/.chub/config.yaml" ]]; then
    echo "error: seeded repository is missing the prepared .chub/config.yaml"
    exit 1
  fi
fi

if [[ ! -f "${OUTPUT}/.gitignore" ]]; then
  echo "error: seeded repository is missing the root .gitignore"
  exit 1
fi

if [[ ! -f "${OUTPUT}/.github/workflows/release.yml" ]]; then
  echo "error: seeded repository is missing the root release workflow"
  exit 1
fi
