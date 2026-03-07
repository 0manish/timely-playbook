# Timely Playbook Operations Guide

> Base template for orchestrated, Codex-ready projects. Use it to seed new repos
> and keep validation, packaging, documentation, and agent workflows consistent.

## Orient yourself

- Governance hub:
  [Timely-Governance-Index.md](Timely-Governance-Index.md)
- Quickstart checklist:
  [AutomationPlaybook-GettingStarted.md](AutomationPlaybook-GettingStarted.md)
- Tracker upkeep guidance:
  [Timely-Governance-Trackers.md](Timely-Governance-Trackers.md)
- Visual map:
  [Timely-Flowgraph.md](Timely-Flowgraph.md)
- Conductor blueprint:
  [Conductor-Orchestration.md](Conductor-Orchestration.md)
- Context Hub integration:
  [Context-Hub-Integration.md](Context-Hub-Integration.md)
- Full-stack agent pipeline:
  [FullStack-Agent-Integration.md](FullStack-Agent-Integration.md)

## Template purpose

- Treat this repository as the canonical starter kit. Use it directly as a seed
  source or create a reusable snapshot with `timely-playbook package`.
- Keep `.orchestrator/ownership.yaml`, `.orchestrator/state.json`,
  `.orchestrator/STATUS.md`, `.vscode/tasks.json`, and
  `.github/workflows/*.yml` intact; downstream repos inherit these guardrails.
- Update `AGENTS.md` whenever you add new governance rules so every operator and
  agent works from the same baseline.

## Install and configure

### Prerequisites

- Go 1.22+
- Python 3.11+
- Node `22.22.0+` (22.x)
- `npm 10.x`
- Git and Bash

Install the pinned Node dependencies before using Context Hub or docs wrappers:

```bash
npm ci
```

The repository pins Node in `.nvmrc` and `.node-version` at `22.22.0`.

### Build or install the CLI

For a repo-local binary and fresh package output:

```bash
make compile
```

This builds `./.bin/timely-playbook` and refreshes `dist/timely-template`.

If you want the CLI globally on your `PATH`, use:

```bash
cd cmd/timely-playbook && go install .
```

### Initialize configuration

Create or update `timely-playbook.yaml` at the repository root:

```bash
./.bin/timely-playbook init-config \
  --owner "{{OWNER_NAME}}" \
  --email "{{OWNER_EMAIL}}" \
  --repo "$(basename "$(pwd)")"
```

Config fields:

<!-- markdownlint-disable MD013 -->
| Field | Purpose | Default |
| --- | --- | --- |
| `owner_name` | Operator or agent name stamped into exports and fallback owners | `{{OWNER_NAME}}` |
| `owner_email` | Contact info captured in packaged templates | `{{OWNER_EMAIL}}` |
| `repo_name` | Display name for exports | current directory |
| `docs_dir` | Root content directory used when packaging and seeding | `.` |
| `log_dir` | Directory that receives run logs | `run-logs` |
| `journal_path` | Markdown journal updated after weekly runs | `timely-trackers/test-run-journal.md` |
| `ledger_path` | Control ledger path used by append commands | `timely-trackers/agent-control-ledger.md` |
| `backlog_path` | TODO backlog path used by append commands | `timely-trackers/todo-backlog.md` |
<!-- markdownlint-enable MD013 -->

## Core verification path

Run the standard validation suite:

```bash
make validate
```

This runs:
- Python unit tests
- Context Hub mirror validation
- Markdown lint
- Link checks

Run the full installability and packaging check:

```bash
make verify
```

This runs `make validate`, refreshes the package output, and executes the
bootstrap smoke test against a freshly seeded repository.

## Weekly status sweep

```bash
./.bin/timely-playbook run-weekly
```

- Reads the control ledger, quality journal, and backlog to generate a
  governance snapshot.
- Writes `run-logs/<timestamp>/summary.md` and appends the outcome to the
  quality journal.
- Lists manual follow-ups when checks were not run as part of the weekly sweep.
- Use `--dry-run` to view the agenda without writing logs or journal entries.

## Command reference

- `timely-playbook help` — print top-level usage and available commands.
- `timely-playbook init-config` — regenerate `timely-playbook.yaml` with updated
  operator details.
- `timely-playbook append journal|ledger|backlog` — add rows without disturbing
  Markdown alignment (see examples in
  [Timely-Governance-Trackers.md](Timely-Governance-Trackers.md)).
- `timely-playbook run-weekly [--dry-run]` — produce the status summary
  described above.
- `timely-playbook remind` — print agendas from
  `timely-trackers/ceremony-agendas.md` ahead of syncs, gate reviews, or retros.
- `timely-playbook package --output dist/timely-template [--templated]` — export
  the template bundle for reuse.
- `timely-playbook seed` — create a new repo from the current template in one
  command.
- `python tools/orchestrator/orchestrator.py fullstack-init-config` — create
  `.orchestrator/fullstack-agent.json` from pinned defaults.
- `python tools/orchestrator/orchestrator.py fullstack-sync [--update]` —
  clone or update pinned upstream FullStack repos.
- `python tools/orchestrator/orchestrator.py fullstack-bootstrap` —
  scaffold a full-stack project workspace.
- `python tools/orchestrator/orchestrator.py fullstack-plan <project_id>` —
  generate a phase plan and sync tasks into `.orchestrator/state.json`.
- `python tools/orchestrator/orchestrator.py fullstack-run <project_id> <phase_id>
  [--skill <profile>]` — execute a development phase via Codex and capture
  back-translation artifacts.
- `python tools/orchestrator/orchestrator.py fullstack-run-all <project_id>
  [--skill <profile>]` — execute all ready phases sequentially.
- `python tools/orchestrator/orchestrator.py fullstack-status <project_id>` —
  show phase progress and status counts.
- `bash scripts/chub.sh build` — regenerate the Timely Context Hub source and
  build `.chub/timely-dist`.
- `bash scripts/chub.sh validate` — validate the generated Timely Context Hub
  source without updating the build output.
- `bash scripts/chub.sh search <query>` / `get <id>` — search or fetch merged
  Timely and public Context Hub content.
- `bash scripts/chub-mcp.sh` — start the repo-local `chub-mcp` server.
- `bash scripts/install-codex-skill.sh chub-context-hub` — install the shipped
  Context Hub skill bundle into `~/.codex/skills`.

## Context Hub workflow

- Use [Context-Hub-Integration.md](Context-Hub-Integration.md) for the full
  operator guide and MCP snippets.
- The repo-local wrappers always use `.chub/` for config, cache, annotations,
  and generated Timely registry artifacts.
- Typical sequence:

  ```bash
  npm ci
  bash scripts/chub.sh validate
  bash scripts/chub.sh search timely-playbook --json
  bash scripts/chub.sh get timely-playbook/timely-playbook
  bash scripts/chub-mcp.sh
  ```

- Set `CHUB_TELEMETRY=0` if you want to disable telemetry without editing the
  generated config file.

## Packaging and reuse

Create a fresh packaged snapshot:

```bash
make compile
```

This generates:
- `dist/timely-template`
- `dist/timely-template.tgz`

Seed from the current source tree directly:

```bash
./.bin/timely-playbook seed \
  --output /path/to/new-repo \
  --owner "Jane Doe" \
  --email "jane@example.com" \
  --repo "new-repo"
```

Verify the archive contents before shipping:

```bash
tar -tzf dist/timely-template.tgz | grep -E 'AGENTS\.md|SKILLS\.md|scripts/bootstrap-timely-template\.sh|scripts/install-codex-skill\.sh|skills/chub-context-hub/SKILL\.md'
```

### Cross-machine bootstrap flow

```bash
scp dist/timely-template.tgz vm:/tmp/timely-template.tgz
ssh vm 'mkdir -p /tmp && tar -xzf /tmp/timely-template.tgz -C /tmp && \
  bash /tmp/timely-template/scripts/bootstrap-timely-template.sh \
    --source /tmp/timely-template \
    --output ~/projects/aurora \
    --owner "Aurora Ops" \
    --email "ops@example.com" \
    --repo "aurora" \
    --init-git'
```

Sanity check in the new repo:

```bash
[ -f ~/projects/aurora/AGENTS.md ] && [ -f ~/projects/aurora/SKILLS.md ]
```

## Recommended release checklist

1. Run `npm ci`.
2. Run `make verify`.
3. Confirm license and contribution docs are current.
4. Rebuild `dist/` and publish only the refreshed archive.
