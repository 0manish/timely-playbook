---
name: chub-context-hub
description: Use this skill when you need current Timely Playbook docs or public API docs via the repo-local Context Hub wrappers, need to validate or rebuild the Timely mirror, or need to configure the local chub MCP server for Codex and other MCP-capable agents.
---

# Chub Context Hub

Use this skill when:
- the user asks for current Timely Playbook docs instead of model memory
- the user wants current public API docs fetched through `chub`
- the user wants Context Hub MCP wired into Codex or another MCP client
- the user needs the Timely mirror rebuilt or validated

## Repo assumption

This skill is meant to be installed into an agent skill directory, but executed
while your current working directory is a repository seeded from Timely
Playbook.

Before using the commands below:
- `cd /path/to/your/timely-seeded-repo`
- run the wrappers from that repo root

## Stable interface

Always use the repo-local wrappers from the seeded repository root, not a
global `chub` install:

```bash
bash .timely-playbook/bin/chub.sh validate
bash .timely-playbook/bin/chub.sh search timely-playbook --json
bash .timely-playbook/bin/chub.sh get timely-playbook/timely-playbook --json
bash .timely-playbook/bin/chub.sh search openai --json
bash .timely-playbook/bin/chub.sh get openai/chat --lang py --json
bash .timely-playbook/bin/chub-mcp.sh
```

These wrappers regenerate `.chub/timely-source`, refresh `.chub/config.yaml`,
and build `.chub/timely-dist` before normal use.

## Operating notes

- Run `npm ci` first if `node_modules/.bin/chub` is missing.
- In a relocated Timely repo, install Node deps into `.timely-playbook/runtime/`.
- Do not hand-edit `.chub/**`; it is generated state.
- If you change mirrored docs or generator logic, rerun:

```bash
python -m unittest discover -s .timely-core/tests -p "test_*.py"
bash .timely-playbook/bin/chub.sh validate
bash .timely-playbook/bin/run-markdownlint.sh
bash .timely-playbook/bin/check-doc-links.sh
```

## Install into an agent tool

This repository ships the skill bundle at
`.timely-playbook/local/skills/chub-context-hub/`. Install it with the generic
installer:

```bash
bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub
```

Examples:

```bash
# Codex-compatible default
bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub

# Claude Code example
AGENT_SKILLS_HOME="$HOME/.claude/skills" \
  bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub

# Explicit destination for any other agent tool
bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub --dest /path/to/agent/skills
```

The legacy `bash .timely-playbook/bin/install-codex-skill.sh chub-context-hub` wrapper is
still available for Codex-specific setups.

Restart your agent tool after installation if it caches skills.

## References

Read these only when needed:
- `.timely-core/Context-Hub-Integration.md`
- `.timely-core/scripts/chub.sh`
- `.timely-core/scripts/chub-mcp.sh`
- `.timely-core/tools/chub/timely_registry.py`
