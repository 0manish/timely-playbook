# Context Hub integration

> Timely Playbook ships a repo-local Context Hub mirror so operators and agents
> can search current Timely docs and fetch curated public API docs from the same
> `chub` surface.

## What this adds

- Pinned local install of `@aisuite/chub@0.1.1` through the repository
  `package.json`.
- Repo-local wrappers:
  `scripts/chub.sh` for CLI usage and `scripts/chub-mcp.sh` for MCP server
  startup.
- Deterministic Timely mirror generation from the source-authored Markdown corpus
  via `tools/chub/timely_registry.py`.
- Repo-local `CHUB_DIR` state under `.chub/` so annotations, cache, config, and
  generated registry data stay out of git history.

## Prerequisites

- Node `22.22.0+` (22.x)
- `npm 10.x`
- Python `3.11+`

Install the pinned dependency set from the repository root:

```bash
npm ci
```

## Local command surface

Build or validate the Timely mirror:

```bash
bash scripts/chub.sh validate
bash scripts/chub.sh build
```

Search or fetch across the merged Timely + public registry:

```bash
bash scripts/chub.sh search timely-playbook --json
bash scripts/chub.sh get timely-playbook/timely-playbook
bash scripts/chub.sh search openai --json
bash scripts/chub.sh get openai/chat --lang py
```

Start the MCP server:

```bash
bash scripts/chub-mcp.sh
```

The wrappers always:

1. Regenerate `.chub/timely-source`
2. Refresh `.chub/config.yaml`
3. Build `.chub/timely-dist` before normal `search` / `get` / MCP use

## Repo-local configuration

The generated config lives at `.chub/config.yaml` and points at:

- `community`: `https://cdn.aichub.org/v1`
- `timely`: local build output at `.chub/timely-dist`

Telemetry defaults to enabled in the generated config. To opt out for a session
or shell profile:

```bash
export CHUB_TELEMETRY=0
```

## Timely mirror scope

The mirror includes only source-authored Timely Markdown:

- repo-root `*.md`
- `timely-trackers/**`
- `templates/**`
- `snippets/**`
- `.orchestrator/STATUS.md`
- `tools/orchestrator/fullstack_prompts/*.md`

The mirror excludes generated, vendored, or operational output:

- `dist/**`
- `.orchestrator/upstream/**`
- `run-logs/**`
- `vendor/**`
- `node_modules/**`
- `.chub/**`

## Stable ids

Each mirrored file becomes a `timely-playbook/<entry>` doc entry:

- `TimelyPlaybook.md` -> `timely-playbook/timely-playbook`
- `timely-trackers/test-run-journal.md` ->
  `timely-playbook/tracker-test-run-journal`
- `templates/todo-backlog.md` -> `timely-playbook/template-todo-backlog`
- `tools/orchestrator/fullstack_prompts/01_architecture.md` ->
  `timely-playbook/prompt-architecture`

Descriptions come from the first prose paragraph unless an override is defined
in `tools/chub/metadata_overrides.json`.

## MCP client snippets

Codex CLI / MCP-compatible clients can point directly at the repo-local wrapper.

Example `~/.codex/config.toml` snippet:

```toml
[mcp_servers.chub]
command = "bash"
args = ["/absolute/path/to/timely-playbook/scripts/chub-mcp.sh"]
```

Example generic JSON shape used by MCP-capable tools:

```json
{
  "mcpServers": {
    "chub": {
      "command": "bash",
      "args": [
        "/absolute/path/to/timely-playbook/scripts/chub-mcp.sh"
      ]
    }
  }
}
```

## Proper Codex skill bundle

This repository also ships a real Codex skill bundle at
`skills/chub-context-hub/`.

Install it into Codex with:

```bash
bash scripts/install-codex-skill.sh chub-context-hub
```

That installs the bundle into `$CODEX_HOME/skills` or `~/.codex/skills` by
default. Restart Codex after installation so the new skill is discovered.

## Validation workflow

Run the local checks after changing mirror logic or mirrored docs:

```bash
python -m unittest discover -s tests -p "test_*.py"
bash scripts/chub.sh validate
bash scripts/chub.sh search timely-playbook --json
bash scripts/chub.sh get timely-playbook/timely-playbook --json
bash scripts/chub.sh search openai --json
./scripts/check-doc-links.sh
./scripts/run-markdownlint.sh
```

Record documentation validation runs in
`timely-trackers/test-run-journal.md` with `timely-playbook append journal`.
