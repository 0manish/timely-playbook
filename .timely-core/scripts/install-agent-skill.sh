#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  install-agent-skill.sh <skill-name> [--dest /path/to/skills] [--copy | --link]

Options:
  --dest   Destination skills directory. Defaults to $AGENT_SKILLS_HOME,
           then $CODEX_HOME/skills, then ~/.codex/skills.
  --copy   Copy the repo-local skill bundle into the destination (default).
  --link   Symlink the repo-local skill bundle into the destination.
  --help   Show this help text.
EOF
}

SCRIPT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ "$(basename "$SCRIPT_ROOT")" == ".timely-core" ]]; then
  ROOT_DIR="${TIMELY_REPO_ROOT:-$(cd "$SCRIPT_ROOT/.." && pwd)}"
  LOCAL_DIR="${TIMELY_LOCAL_DIR:-$ROOT_DIR/.timely-playbook/local}"
else
  ROOT_DIR="${TIMELY_REPO_ROOT:-$SCRIPT_ROOT}"
  LOCAL_DIR="${TIMELY_LOCAL_DIR:-$ROOT_DIR}"
fi
if [[ -n "${AGENT_SKILLS_HOME:-}" ]]; then
  DEST_DIR="${AGENT_SKILLS_HOME}"
elif [[ -n "${CODEX_HOME:-}" ]]; then
  DEST_DIR="${CODEX_HOME}/skills"
else
  DEST_DIR="${HOME}/.codex/skills"
fi
MODE="copy"
SKILL_NAME=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dest)
      DEST_DIR="${2:-}"
      shift 2
      ;;
    --copy)
      MODE="copy"
      shift
      ;;
    --link)
      MODE="link"
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    -*)
      echo "error: unknown argument: $1" >&2
      usage
      exit 1
      ;;
    *)
      if [[ -n "${SKILL_NAME}" ]]; then
        echo "error: only one skill name may be provided" >&2
        usage
        exit 1
      fi
      SKILL_NAME="$1"
      shift
      ;;
  esac
done

if [[ -z "${SKILL_NAME}" ]]; then
  usage
  exit 1
fi

SOURCE_DIR="${LOCAL_DIR}/skills/${SKILL_NAME}"
TARGET_DIR="${DEST_DIR}/${SKILL_NAME}"

if [[ ! -f "${SOURCE_DIR}/SKILL.md" ]]; then
  echo "error: repo skill '${SKILL_NAME}' not found at ${SOURCE_DIR}" >&2
  exit 1
fi

if [[ -e "${TARGET_DIR}" ]]; then
  echo "error: destination already exists: ${TARGET_DIR}" >&2
  exit 1
fi

mkdir -p "${DEST_DIR}"

if [[ "${MODE}" == "link" ]]; then
  ln -s "${SOURCE_DIR}" "${TARGET_DIR}"
else
  cp -R "${SOURCE_DIR}" "${TARGET_DIR}"
fi

echo "installed ${SKILL_NAME} to ${TARGET_DIR}"
echo "Restart your agent tool if it caches skills."
