#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: symphony-submit.sh --payload <path> [--prompt <path>] [--run-dir <path>]

Starter wrapper for handing a Timely phase or autofix task to an external
Symphony service.

Expected environment:
- `TIMELY_SYMPHONY_SUBMIT`
  Command used to submit the payload to your Symphony service.
  Example:
  export TIMELY_SYMPHONY_SUBMIT='external-symphony submit'

The submit command will receive the following arguments:
- `--payload <path>`
- optional `--prompt <path>`
- optional `--run-dir <path>`

This script does not interpret the payload itself. It is a stable wrapper so
seeded repos can point `adapters.symphony.submit_command` at a repo-local path.
EOF
}

payload_file=""
prompt_file=""
run_dir=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --payload)
      payload_file="${2:-}"
      shift 2
      ;;
    --prompt)
      prompt_file="${2:-}"
      shift 2
      ;;
    --run-dir)
      run_dir="${2:-}"
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

if [[ -z "$payload_file" ]]; then
  echo "error: --payload is required" >&2
  usage >&2
  exit 64
fi

if [[ ! -f "$payload_file" ]]; then
  echo "error: payload file not found: $payload_file" >&2
  exit 66
fi

if [[ -z "${TIMELY_SYMPHONY_SUBMIT:-}" ]]; then
  cat >&2 <<'EOF'
error: TIMELY_SYMPHONY_SUBMIT is not configured.

Set it to the command that should receive Timely's Symphony payloads, for
example:

  export TIMELY_SYMPHONY_SUBMIT='external-symphony submit'

Then point `.timely-playbook/local/.orchestrator/fullstack-agent.json` at this
wrapper:

  "adapters": {
    "symphony": {
      "submit_command": [
        "bash",
        ".timely-playbook/bin/symphony-submit.sh",
        "--payload",
        "{payload_file}",
        "--prompt",
        "{prompt_file}",
        "--run-dir",
        "{run_dir}"
      ]
    }
  }
EOF
  exit 78
fi

cmd=(bash -lc "$TIMELY_SYMPHONY_SUBMIT --payload \"\$1\"")
args=("$payload_file")

if [[ -n "$prompt_file" ]]; then
  cmd[2]+=' --prompt "$2"'
  args+=("$prompt_file")
fi

if [[ -n "$run_dir" ]]; then
  next_index=$(( ${#args[@]} + 1 ))
  cmd[2]+=" --run-dir \"\$$next_index\""
  args+=("$run_dir")
fi

exec "${cmd[@]}" -- "${args[@]}"
