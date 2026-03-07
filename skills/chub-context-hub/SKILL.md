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

## Stable interface

Always use the repo-local wrappers from the repository root, not a global `chub`
install:

```bash
bash ../../scripts/chub.sh validate
bash ../../scripts/chub.sh search timely-playbook --json
bash ../../scripts/chub.sh get timely-playbook/timely-playbook --json
bash ../../scripts/chub.sh search openai --json
bash ../../scripts/chub.sh get openai/chat --lang py --json
bash ../../scripts/chub-mcp.sh
```

These wrappers regenerate `.chub/timely-source`, refresh `.chub/config.yaml`,
and build `.chub/timely-dist` before normal use.

## Operating notes

- Run `npm ci` first if `node_modules/.bin/chub` is missing.
- Do not hand-edit `.chub/**`; it is generated state.
- If you change mirrored docs or generator logic, rerun:

```bash
python -m unittest discover -s tests -p "test_*.py"
bash ../../scripts/chub.sh validate
./scripts/run-markdownlint.sh
./scripts/check-doc-links.sh
```

## Install into Codex

This repository ships the skill bundle at `skills/chub-context-hub/`. Install it
into Codex with:

```bash
bash ../../scripts/install-codex-skill.sh chub-context-hub
```

Restart Codex after installation so the new skill is discovered.

## References

Read these only when needed:
- `../../Context-Hub-Integration.md`
- `../../scripts/chub.sh`
- `../../scripts/chub-mcp.sh`
- `../../tools/chub/timely_registry.py`
