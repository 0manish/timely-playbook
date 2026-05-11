#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: claude-code-example.sh --workdir <path> [--model <name>]

Starter wrapper for the `claude_code_example` provider in Timely.

Expected environment:
- `TIMELY_CLAUDE_CODE_COMMAND`
  Command used to invoke your Claude Code workflow.
  Example:
  export TIMELY_CLAUDE_CODE_COMMAND='claude-code run'

The rendered Timely prompt is read from stdin and forwarded unchanged.
EOF
}

workdir=""
model=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir)
      workdir="${2:-}"
      shift 2
      ;;
    --model)
      model="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "error: unknown argument: $1" >&2
      usage >&2
      exit 64
      ;;
  esac
done

if [[ -z "$workdir" ]]; then
  echo "error: --workdir is required" >&2
  usage >&2
  exit 64
fi

if [[ -z "${TIMELY_CLAUDE_CODE_COMMAND:-}" ]]; then
  cat >&2 <<'EOF'
error: TIMELY_CLAUDE_CODE_COMMAND is not configured.

Set it to your Claude Code invocation, for example:

  export TIMELY_CLAUDE_CODE_COMMAND='claude-code run'

Then point `providers.claude_code_example.exec_command` at:

  [
    "bash",
    ".timely-playbook/bin/claude-code-example.sh",
    "--workdir",
    "{workdir}"
  ]
EOF
  exit 78
fi

cmd=(bash -lc "cd \"\$1\" && $TIMELY_CLAUDE_CODE_COMMAND")
args=("$workdir")

if [[ -n "$model" ]]; then
  cmd[2]+=' --model "$2"'
  args+=("$model")
fi

exec "${cmd[@]}" -- "${args[@]}"
