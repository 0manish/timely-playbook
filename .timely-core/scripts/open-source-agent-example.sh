#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: open-source-agent-example.sh --workdir <path> [--model <name>]

Starter wrapper for the `open_source_agent_example` provider in Timely.

Expected environment:
- `TIMELY_OPEN_SOURCE_AGENT_COMMAND`
  Command used to invoke your local open-source agent runner.
  Example:
  export TIMELY_OPEN_SOURCE_AGENT_COMMAND='my-agent-cli run'

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

if [[ -z "${TIMELY_OPEN_SOURCE_AGENT_COMMAND:-}" ]]; then
  cat >&2 <<'EOF'
error: TIMELY_OPEN_SOURCE_AGENT_COMMAND is not configured.

Set it to your open-source agent invocation, for example:

  export TIMELY_OPEN_SOURCE_AGENT_COMMAND='my-agent-cli run'

Then point `providers.open_source_agent_example.exec_command` at:

  [
    "bash",
    ".timely-playbook/bin/open-source-agent-example.sh",
    "--workdir",
    "{workdir}"
  ]
EOF
  exit 78
fi

cmd=(bash -lc "cd \"\$1\" && $TIMELY_OPEN_SOURCE_AGENT_COMMAND")
args=("$workdir")

if [[ -n "$model" ]]; then
  cmd[2]+=' --model "$2"'
  args+=("$model")
fi

exec "${cmd[@]}" -- "${args[@]}"
