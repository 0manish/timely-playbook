# Context Hub integration

> Timely Playbook ships a repo-local Context Hub mirror so operators and agents
> can search current Timely docs and fetch curated public API docs from the same
> `chub` surface.

## What this adds

- Pinned local install of `@aisuite/chub@0.1.1` through the repository
  `.timely-playbook/runtime/package.json`.
- Repo-local wrappers:
  `.timely-playbook/bin/chub.sh` for CLI usage and
  `.timely-playbook/bin/chub-mcp.sh` for MCP server startup.
- Deterministic Timely mirror generation from the source-authored Markdown corpus
  via `.timely-core/tools/chub/timely_registry.py`.
- Repo-local `CHUB_DIR` state under `.chub/` so annotations, cache, config, and
  generated registry data stay out of git history.
- Generated mirror metadata at `.chub/timely-mirror-metadata.json` so Timely
  can track the pinned `@aisuite/chub` version, mirrored doc set, and registry
  hash as the upstream Context Hub tool evolves.

## Prerequisites

- Node `22.22.0+` (22.x)
- `npm 10.x`
- Python `3.11+`

Fresh Timely seeds preinstall the pinned dependency set and prepare `.chub/` by
default. Re-run the install from the repository root only if the runtime
dependencies were cleared:

```bash
npm ci --prefix .timely-playbook/runtime
```

## Local command surface

Build or validate the Timely mirror:

```bash
bash .timely-playbook/bin/chub.sh validate
bash .timely-playbook/bin/chub.sh build
```

Search or fetch across the merged Timely + public registry:

```bash
bash .timely-playbook/bin/chub.sh search timely-playbook --json
bash .timely-playbook/bin/chub.sh get timely-playbook/timely-playbook
bash .timely-playbook/bin/chub.sh search openai --json
bash .timely-playbook/bin/chub.sh get openai/chat --lang py
```

Start the MCP server:

```bash
bash .timely-playbook/bin/chub-mcp.sh
```

The wrappers always:

1. Regenerate `.chub/timely-source`
2. Refresh `.chub/config.yaml`
3. Build `.chub/timely-dist` before normal `search` / `get` / MCP use

## Repo-local configuration

The generated config lives at `.chub/config.yaml` and points at:

- `community`: `https://cdn.aichub.org/v1`
- `timely`: local build output at `.chub/timely-dist`

Timely also writes `.chub/timely-mirror-metadata.json`, which records the
pinned `@aisuite/chub` dependency version from
`.timely-playbook/runtime/package.json`, the mirrored file set, generated
registry path, and a registry hash. Use that metadata when reviewing `chub`
upgrades or diagnosing downstream repo behavior changes caused by evolving
Context Hub functionality.

Telemetry defaults to enabled in the generated config. To opt out for a session
or shell profile:

```bash
export CHUB_TELEMETRY=0
```

## Timely mirror scope

The mirror includes only source-authored Timely Markdown. In a relocated seeded
repo that means:

- `.timely-core/*.md`
- `.timely-playbook/local/AGENTS.md`
- `.timely-playbook/local/SKILLS.md`
- `.timely-playbook/local/timely-trackers/**`
- `.timely-core/templates/**`
- `.timely-core/snippets/**`
- `.timely-playbook/local/.orchestrator/STATUS.md`
- `.timely-core/tools/orchestrator/fullstack_prompts/*.md`

The generator also understands the authoring source layout used by this
template repository and normalizes both directory structures to the same
registry ids.

The mirror excludes generated, vendored, or operational output:

- `dist/**`
- `.timely-playbook/local/.orchestrator/upstream/**`
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
- `.timely-core/tools/orchestrator/fullstack_prompts/01_architecture.md` ->
  `timely-playbook/prompt-architecture`

Descriptions come from the first prose paragraph unless an override is defined
in `.timely-core/tools/chub/metadata_overrides.json`.

## MCP client snippets

Codex CLI and other MCP-compatible clients can point directly at the repo-local
wrapper.

Example `~/.codex/config.toml` snippet:

```toml
[mcp_servers.chub]
command = "bash"
args = ["/absolute/path/to/timely-playbook/.timely-playbook/bin/chub-mcp.sh"]
```

Example generic JSON shape used by MCP-capable tools:

```json
{
  "mcpServers": {
    "chub": {
      "command": "bash",
      "args": [
        "/absolute/path/to/timely-playbook/.timely-playbook/bin/chub-mcp.sh"
      ]
    }
  }
}
```

## Proper agent skill bundle

This repository also ships a repo-local skill bundle at
`.timely-playbook/local/skills/chub-context-hub/`. It is intended for coding
agents to use when they need current Timely docs or public API docs through
`chub`.

The installed skill assumes the agent is operating inside a repository seeded
from Timely Playbook and that commands are run from that repo root, so it calls
the repo-local wrappers such as `bash .timely-playbook/bin/chub.sh ...` instead
of any global `chub` binary.

Install it with:

```bash
bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub
```

That installs the bundle into `$AGENT_SKILLS_HOME`, then `$CODEX_HOME/skills`,
then `~/.codex/skills` by default. The legacy
`bash .timely-playbook/bin/install-codex-skill.sh chub-context-hub` wrapper
remains available for Codex-specific workflows. Restart your agent tool after
installation if it caches skills.

Example for Claude Code:

```bash
AGENT_SKILLS_HOME="$HOME/.claude/skills" \
  bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub
```

Example for an arbitrary skill directory:

```bash
bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub --dest /path/to/agent/skills
```

## Validation workflow

Run the local checks after changing mirror logic or mirrored docs. Re-run
`npm ci --prefix .timely-playbook/runtime` first only if the local runtime was
cleared or needs to be refreshed:

```bash
npm ci --prefix .timely-playbook/runtime
python -m unittest discover -s .timely-core/tests -p "test_*.py"
bash .timely-playbook/bin/chub.sh validate
bash .timely-playbook/bin/chub.sh search timely-playbook --json
bash .timely-playbook/bin/chub.sh get timely-playbook/timely-playbook --json
bash .timely-playbook/bin/chub.sh search openai --json
bash .timely-playbook/bin/check-doc-links.sh
bash .timely-playbook/bin/run-markdownlint.sh
```

Record documentation validation runs in
`.timely-playbook/local/timely-trackers/test-run-journal.md` with
`timely-playbook append journal`.
