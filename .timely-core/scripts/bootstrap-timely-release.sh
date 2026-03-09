#!/usr/bin/env bash

set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  bootstrap-timely-release.sh \
    --release-repo <owner>/<repo> \
    --output /path/to/new-repo \
    --owner "Your Name" \
    --email "you@example.com" \
    --repo "new-repo-name" \
    [--version v1.2.3] [--install-dir ~/.local/bin] [--templated | --inject] \
    [--include-logs] [--init-git] [--skip-runtime-setup]

  bootstrap-timely-release.sh \
    --asset-base-url file:///tmp/timely-release \
    --output /path/to/new-repo \
    --owner "Your Name" \
    --email "you@example.com" \
    --repo "new-repo-name" \
    [--install-dir ~/.local/bin] [--templated | --inject] [--include-logs] \
    [--init-git] [--skip-runtime-setup]

Options:
  --release-repo       GitHub repo that hosts Timely release assets.
  --asset-base-url     Override release download base URL (for mirrors/tests).
  --version            Release tag to download (default: latest).
  --install-dir        Directory where the CLI binary should be installed
                       (default: ~/.local/bin).
  --skip-binary-install Use the downloaded binary only for this bootstrap run.
  --output             Destination directory for the new project.
  --owner              Operator/owner name inserted into .timely-playbook/config.yaml.
  --email              Operator email inserted into .timely-playbook/config.yaml.
  --repo               Repo name inserted into .timely-playbook/config.yaml.
  --templated          Keep placeholders in exports (default).
  --inject             Inject local values instead of placeholders.
  --include-logs       Include run-logs in the copied template.
  --init-git           Run `git init` in the destination.
  --skip-runtime-setup Skip the default npm install and initial chub build.
  --help               Show this help text.
EOF
}

fail() {
  echo "error: $*" >&2
  exit 1
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    fail "$1 is required"
  fi
}

sha256_file() {
  local path="$1"
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$path" | awk '{print $1}'
    return
  fi
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$path" | awk '{print $1}'
    return
  fi
  fail "sha256sum or shasum is required to verify release assets"
}

expected_checksum() {
  local checksums_file="$1"
  local asset_name="$2"
  awk -v asset="$asset_name" '$2 == asset { print $1 }' "$checksums_file"
}

detect_platform() {
  local os arch
  os="$(uname -s)"
  arch="$(uname -m)"

  case "$os" in
    Linux) os="linux" ;;
    Darwin) os="darwin" ;;
    *) fail "unsupported operating system: $os" ;;
  esac

  case "$arch" in
    x86_64) arch="amd64" ;;
    arm64|aarch64) arch="arm64" ;;
    *) fail "unsupported architecture: $arch" ;;
  esac

  printf '%s %s\n' "$os" "$arch"
}

download_asset() {
  local base_url="$1"
  local asset_name="$2"
  local destination="$3"
  curl -fsSL "${base_url}/${asset_name}" -o "$destination"
}

RELEASE_REPO=""
ASSET_BASE_URL=""
VERSION="latest"
INSTALL_DIR="${HOME}/.local/bin"
SKIP_BINARY_INSTALL=false
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
    --release-repo)
      RELEASE_REPO="${2:-}"
      shift 2
      ;;
    --asset-base-url)
      ASSET_BASE_URL="${2:-}"
      shift 2
      ;;
    --version)
      VERSION="${2:-latest}"
      shift 2
      ;;
    --install-dir)
      INSTALL_DIR="${2:-}"
      shift 2
      ;;
    --skip-binary-install)
      SKIP_BINARY_INSTALL=true
      shift
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
      usage
      fail "unknown argument: $1"
      ;;
  esac
done

if [[ -z "$OUTPUT" || -z "$OWNER" || -z "$EMAIL" || -z "$REPO_NAME" ]]; then
  usage
  fail "--output, --owner, --email, and --repo are required"
fi

if [[ -z "$ASSET_BASE_URL" && -z "$RELEASE_REPO" ]]; then
  usage
  fail "provide --release-repo or --asset-base-url"
fi

require_command curl
require_command tar
require_command git

if [[ "$SKIP_BINARY_INSTALL" != "true" ]]; then
  require_command install
fi

if [[ "$SKIP_RUNTIME_SETUP" != "true" ]]; then
  require_command npm
  require_command python
fi

read -r OS_NAME ARCH_NAME < <(detect_platform)
BINARY_ASSET="timely-playbook_${OS_NAME}_${ARCH_NAME}.tar.gz"
TEMPLATE_ASSET="timely-template.tgz"
CHECKSUM_ASSET="timely-checksums.txt"

if [[ -z "$ASSET_BASE_URL" ]]; then
  if [[ "$VERSION" == "latest" ]]; then
    ASSET_BASE_URL="https://github.com/${RELEASE_REPO}/releases/latest/download"
  else
    ASSET_BASE_URL="https://github.com/${RELEASE_REPO}/releases/download/${VERSION}"
  fi
fi
ASSET_BASE_URL="${ASSET_BASE_URL%/}"

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

download_asset "$ASSET_BASE_URL" "$BINARY_ASSET" "${WORK_DIR}/${BINARY_ASSET}"
download_asset "$ASSET_BASE_URL" "$TEMPLATE_ASSET" "${WORK_DIR}/${TEMPLATE_ASSET}"
download_asset "$ASSET_BASE_URL" "$CHECKSUM_ASSET" "${WORK_DIR}/${CHECKSUM_ASSET}"

EXPECTED_BINARY_SUM="$(expected_checksum "${WORK_DIR}/${CHECKSUM_ASSET}" "$BINARY_ASSET")"
EXPECTED_TEMPLATE_SUM="$(expected_checksum "${WORK_DIR}/${CHECKSUM_ASSET}" "$TEMPLATE_ASSET")"

if [[ -z "$EXPECTED_BINARY_SUM" || -z "$EXPECTED_TEMPLATE_SUM" ]]; then
  fail "release checksums file is missing expected entries"
fi

ACTUAL_BINARY_SUM="$(sha256_file "${WORK_DIR}/${BINARY_ASSET}")"
ACTUAL_TEMPLATE_SUM="$(sha256_file "${WORK_DIR}/${TEMPLATE_ASSET}")"

if [[ "$EXPECTED_BINARY_SUM" != "$ACTUAL_BINARY_SUM" ]]; then
  fail "checksum mismatch for ${BINARY_ASSET}"
fi

if [[ "$EXPECTED_TEMPLATE_SUM" != "$ACTUAL_TEMPLATE_SUM" ]]; then
  fail "checksum mismatch for ${TEMPLATE_ASSET}"
fi

mkdir -p "${WORK_DIR}/bin"
tar -xzf "${WORK_DIR}/${BINARY_ASSET}" -C "${WORK_DIR}/bin"
CLI_BIN="${WORK_DIR}/bin/timely-playbook"
if [[ ! -x "$CLI_BIN" ]]; then
  fail "downloaded archive did not contain an executable timely-playbook binary"
fi

if [[ "$SKIP_BINARY_INSTALL" != "true" ]]; then
  if [[ -z "$INSTALL_DIR" ]]; then
    fail "--install-dir must not be empty unless --skip-binary-install is used"
  fi
  mkdir -p "$INSTALL_DIR"
  install -m 0755 "$CLI_BIN" "${INSTALL_DIR}/timely-playbook"
fi

mkdir -p "${WORK_DIR}/template"
tar -xzf "${WORK_DIR}/${TEMPLATE_ASSET}" -C "${WORK_DIR}/template"
TEMPLATE_ROOT="${WORK_DIR}/template/timely-template"

if [[ ! -d "$TEMPLATE_ROOT" ]]; then
  fail "downloaded template archive did not unpack to timely-template/"
fi

SEED_ARGS=(seed --output "$OUTPUT" --owner "$OWNER" --email "$EMAIL" --repo "$REPO_NAME")

if [[ "$TEMPLATED" == "true" ]]; then
  SEED_ARGS+=(--templated)
else
  SEED_ARGS+=(--templated=false)
fi

if [[ "$INCLUDE_LOGS" == "true" ]]; then
  SEED_ARGS+=(--include-logs)
fi

if [[ "$INIT_GIT" == "true" ]]; then
  SEED_ARGS+=(--init-git)
fi

if [[ "$SKIP_RUNTIME_SETUP" == "true" ]]; then
  SEED_ARGS+=(--skip-runtime-setup)
fi

unset TIMELY_REPO_ROOT TIMELY_CORE_DIR TIMELY_PLAYBOOK_DIR TIMELY_LOCAL_DIR TIMELY_RUNTIME_DIR TIMELY_BIN_DIR TIMELY_CONFIG_PATH

pushd "$TEMPLATE_ROOT" >/dev/null
"$CLI_BIN" "${SEED_ARGS[@]}"
popd >/dev/null

if [[ "$SKIP_BINARY_INSTALL" != "true" ]]; then
  echo "Installed timely-playbook to ${INSTALL_DIR}/timely-playbook"
  case ":${PATH}:" in
    *":${INSTALL_DIR}:"*) ;;
    *)
      echo "warning: ${INSTALL_DIR} is not on PATH"
      ;;
  esac
fi

echo "Seeded repository at ${OUTPUT} from release assets"
