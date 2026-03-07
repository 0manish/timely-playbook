#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  install-codex-skill.sh <skill-name> [--dest /path/to/skills] [--copy | --link]

Options:
  --dest   Destination skills directory. Defaults to $CODEX_HOME/skills or ~/.codex/skills.
  --copy   Copy the repo-local skill bundle into the destination (default).
  --link   Symlink the repo-local skill bundle into the destination.
  --help   Show this help text.
EOF
}

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="${CODEX_HOME:-$HOME/.codex}/skills"
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

SOURCE_DIR="${ROOT_DIR}/skills/${SKILL_NAME}"
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
echo "Restart Codex to pick up new skills."
