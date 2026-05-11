# Timely Playbook Operations Guide

> Base template for orchestrated, agent-ready projects. The shipped provider
> defaults target Codex, but the orchestrator and governance model are designed
> to support other agent CLIs with config changes instead of rewrites.

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
- CXDB and LEANN integration:
  [CXDB-LEANN-Integration.md](CXDB-LEANN-Integration.md)
- Context Hub integration:
  [Context-Hub-Integration.md](Context-Hub-Integration.md)
- Full-stack agent pipeline:
  [FullStack-Agent-Integration.md](FullStack-Agent-Integration.md)

## Template purpose

- Treat this repository as the canonical starter kit. Use it directly as a seed
  source or create a reusable snapshot with `timely-playbook package`.
- In seeded repos, treat `.timely-core/` as the immutable Timely snapshot and
  `.timely-playbook/local/` as the editable Timely surface.
- Keep `.timely-playbook/local/.orchestrator/ownership.yaml`,
  `.timely-playbook/local/.orchestrator/state.json`,
  `.timely-playbook/local/.orchestrator/STATUS.md`,
  `.timely-playbook/local/.cxdb/`,
  `.timely-playbook/local/.leann/`, root
  `.vscode/tasks.json`, and root `.github/workflows/*.yml` intact; downstream
  repos inherit these guardrails.
- Update `AGENTS.md` whenever you add new governance rules so every operator and
  agent works from the same baseline.

## Install and configure

### Prerequisites

- Go 1.22+
- Python 3.11+
- Node `22.22.0+` (22.x)
- `npm 10.x`
- Git and Bash

End users who bootstrap from published release assets can skip the local Go
toolchain. Template maintainers still need Go to build and verify the source
tree.

Fresh seeds preinstall the pinned runtime dependencies and prepare `.chub/` by
default. Re-run the install only if the seeded runtime dependencies were
cleared:

```bash
npm ci --prefix .timely-playbook/runtime
```

The seeded runtime pins Node in `.timely-playbook/runtime/.nvmrc` and
`.timely-playbook/runtime/.node-version` at `22.22.0`.

### Build or install the CLI

For end-user installation from published releases:

```bash
curl -fsSL https://raw.githubusercontent.com/<org>/<timely-playbook-repo>/main/.timely-core/scripts/bootstrap-timely-release.sh | bash -s -- \
  --release-repo <org>/<timely-playbook-repo> \
  --output ~/projects/aurora \
  --owner "Aurora Ops" \
  --email "ops@example.com" \
  --repo "aurora" \
  --init-git
```

This installs `timely-playbook` to `~/.local/bin` by default, downloads the
matching `timely-template.tgz`, verifies checksums, and seeds the new repo.

In a seeded repo, use the generated launcher:

```bash
bash .timely-playbook/bin/timely-playbook help
```

This launcher builds a cached CLI binary under
`.timely-playbook/runtime/cache/timely-playbook` and executes it.
If Go is unavailable but `timely-playbook` is already installed on your `PATH`,
the launcher falls back to that binary instead of rebuilding from source.

If you want the CLI globally on your `PATH`, use:

```bash
cd .timely-core/cmd/timely-playbook && go install .
```

### Initialize configuration

Create or update `.timely-playbook/config.yaml`:

```bash
bash .timely-playbook/bin/timely-playbook init-config \
  --owner "Smoke Test" \
  --email "smoke@example.com" \
  --repo "$(basename "$(pwd)")"
```

Config fields:

<!-- markdownlint-disable MD013 -->
| Field | Purpose | Default |
| --- | --- | --- |
| `owner_name` | Operator or agent name stamped into exports and fallback owners | `Smoke Test` |
| `owner_email` | Contact info captured in packaged templates | `smoke@example.com` |
| `repo_name` | Display name for exports | current directory |
| `docs_dir` | Editable Timely content root | `.timely-playbook/local` |
| `log_dir` | Directory that receives run logs | `.timely-playbook/local/run-logs` |
| `journal_path` | Markdown journal updated after weekly runs | `.timely-playbook/local/timely-trackers/test-run-journal.md` |
| `ledger_path` | Control ledger path used by append commands | `.timely-playbook/local/timely-trackers/agent-control-ledger.md` |
| `backlog_path` | TODO backlog path used by append commands | `.timely-playbook/local/timely-trackers/todo-backlog.md` |
<!-- markdownlint-enable MD013 -->

### Agent provider configuration

Full-stack phase runs resolve their execution CLI through
`.timely-playbook/local/.orchestrator/fullstack-agent.json`.

- `default_provider` selects the provider used when `--provider` is omitted.
- `providers.<name>.exec_command` is an argv template that can use
  `{workdir}`, `{run_dir}`, and `{model_args}` placeholders.
- `providers.<name>.model_arg` expands into `{model_args}` when a model is
  supplied.
- `providers.<name>.stdin_prompt` controls whether the rendered phase prompt is
  piped on stdin.

Minimal example:

```json
{
  "default_provider": "other-agent",
  "providers": {
    "other-agent": {
      "label": "Other Agent CLI",
      "stdin_prompt": true,
      "exec_command": [
        "other-agent",
        "run",
        "--cwd",
        "{workdir}",
        "--save-last-message",
        "{run_dir}/agent-last-message.txt",
        "{model_args}"
      ],
      "model_arg": [
        "--model",
        "{model}"
      ]
    }
  }
}
```

## Core verification path

Run the standard validation suite in a seeded repo:

```bash
npm ci --prefix .timely-playbook/runtime
go test ./.timely-core/cmd/timely-playbook/...
python -m unittest discover -s ./.timely-core/tests -p 'test_*.py'
bash .timely-playbook/bin/chub.sh validate
bash .timely-playbook/bin/run-markdownlint.sh
bash .timely-playbook/bin/check-doc-links.sh
python .timely-playbook/bin/orchestrator.py context-sync
```

Template maintainers can still run `make validate` from the Timely source repo.

Run the core drift check when you refresh or inspect `.timely-core/`:

```bash
bash .timely-playbook/bin/timely-playbook validate-core
```

Use `refresh-core` to replace the immutable snapshot without overwriting local
customizations:

```bash
bash .timely-playbook/bin/timely-playbook refresh-core --source /path/to/timely-playbook
```

## Weekly status sweep

```bash
bash .timely-playbook/bin/timely-playbook run-weekly
```

- Reads the control ledger, quality journal, and backlog to generate a
  governance snapshot.
- Writes `.timely-playbook/local/run-logs/<timestamp>/summary.md` and appends
  the outcome to the quality journal.
- Lists manual follow-ups when checks were not run as part of the weekly sweep.
- Use `--dry-run` to view the agenda without writing logs or journal entries.

## Command reference

- `timely-playbook help` — print top-level usage and available commands.
- `timely-playbook init-config` — regenerate `.timely-playbook/config.yaml`
  with updated operator details.
- `timely-playbook append journal|ledger|backlog` — add rows without disturbing
  Markdown alignment (see examples in
  [Timely-Governance-Trackers.md](Timely-Governance-Trackers.md)).
- `timely-playbook run-weekly [--dry-run]` — produce the status summary
  described above.
- `timely-playbook remind` — print agendas from
  `.timely-playbook/local/timely-trackers/ceremony-agendas.md` ahead of syncs,
  gate reviews, or retros.
- `timely-playbook package --output dist/timely-template [--templated]` — export
  the template bundle for reuse.
- `timely-playbook seed` — create a new repo from the current template in one
  command and preinstall the repo-local runtime plus `.chub/` state by default.
- `bash .timely-playbook/bin/bootstrap-timely-release.sh` — download published
  release assets, install the CLI binary, and seed a repo without a source
  checkout.
- `timely-playbook migrate-layout` — relocate a legacy Timely repo in place and
  back up the original Timely-owned files under
  `.timely-playbook/migration-backups/<timestamp>/`. The default migration path
  also reinstalls the repo-local runtime and prepares `.chub/`.
- `timely-playbook refresh-core --source|--template-repo|--archive` — replace
  `.timely-core/`, refresh runtime launchers, and regenerate the root GitHub
  surface plus dispatchers. The default refresh path also reinstalls the
  repo-local runtime and prepares `.chub/`.
- `timely-playbook validate-core` — verify `.timely-core/manifest.json` against
  the current immutable snapshot.
- `python .timely-playbook/bin/orchestrator.py fullstack-init-config` — create
  `.timely-playbook/local/.orchestrator/fullstack-agent.json` from pinned
  defaults.
- `python .timely-playbook/bin/orchestrator.py fullstack-sync [--update]` —
  clone or update pinned upstream FullStack repos.
- `python .timely-playbook/bin/orchestrator.py fullstack-bootstrap` —
  scaffold a full-stack project workspace.
- `python .timely-playbook/bin/orchestrator.py context-sync` — import the
  portable `.timely-playbook/local/.orchestrator/state.json` snapshot into CXDB,
  refresh the LEANN index, and rescan local governance files.
- `python .timely-playbook/bin/orchestrator.py context-search <query>` —
  search the project-local LEANN index.
- `python .timely-playbook/bin/orchestrator.py fullstack-plan <project_id>` —
  generate a phase plan and sync tasks into the CXDB-backed state store while
  updating `.timely-playbook/local/.orchestrator/state.json`.
- `python .timely-playbook/bin/orchestrator.py fullstack-run <project_id> <phase_id>
  [--stack <stack>] [--provider <provider>] [--skill <profile>]` — execute a
  development phase via the configured stack and capture back-translation
  artifacts.
- `python .timely-playbook/bin/orchestrator.py fullstack-run-all <project_id>
  [--stack <stack>] [--provider <provider>] [--skill <profile>]` — execute all
  ready phases sequentially.
- `python .timely-playbook/bin/orchestrator.py fullstack-reconcile <project_id>
  <phase_id> <state>` — reconcile an externally managed phase result back into
  Timely state after a Symphony handoff completes.
- `python .timely-playbook/bin/orchestrator.py autofix-config
  [--stack <stack>] [--provider <provider>]` — resolve the stack/provider/adapter
  profile used by the CI autofix workflow.
- `python .timely-playbook/bin/orchestrator.py autofix-dispatch --repo <repo>
  --workflow <name> --head-branch <branch> --run-url <url>` — hand a CI fix
  task to the configured Symphony adapter.
- `bash .timely-playbook/bin/symphony-submit.sh --payload <path>` — starter
  repo-local wrapper for external Symphony handoff. Configure
  `TIMELY_SYMPHONY_SUBMIT` plus `adapters.symphony.submit_command` to use it.
- `bash .timely-playbook/bin/claude-code-example.sh --workdir <path>` — starter
  repo-local wrapper for the documented Claude provider example. Configure
  `TIMELY_CLAUDE_CODE_COMMAND` plus
  `providers.claude_code_example.exec_command` to use it.
- `bash .timely-playbook/bin/open-source-agent-example.sh --workdir <path>` —
  starter repo-local wrapper for the documented open-source provider example.
  Configure `TIMELY_OPEN_SOURCE_AGENT_COMMAND` plus
  `providers.open_source_agent_example.exec_command` to use it.
- `python .timely-playbook/bin/orchestrator.py fullstack-status <project_id>` —
  show phase progress and status counts.
- `bash .timely-playbook/bin/chub.sh build` — regenerate the Timely Context
  Hub source and build `.chub/timely-dist`.
- `bash .timely-playbook/bin/chub.sh validate` — validate the generated Timely
  Context Hub source without updating the build output.
- `bash .timely-playbook/bin/chub.sh search <query>` / `get <id>` — search or
  fetch merged Timely and public Context Hub content.
- `bash .timely-playbook/bin/chub-mcp.sh` — start the repo-local `chub-mcp`
  server.
- `bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub` —
  install the shipped Context Hub skill bundle into `$AGENT_SKILLS_HOME`, then
  `$CODEX_HOME/skills`, then `~/.codex/skills` by default.

## Context Hub workflow

- Use [Context-Hub-Integration.md](Context-Hub-Integration.md) for the full
  operator guide and MCP snippets.
- The repo-local wrappers always use `.chub/` for config, cache, annotations,
  and generated Timely registry artifacts.
- Typical sequence:

  ```bash
  npm ci --prefix .timely-playbook/runtime
  bash .timely-playbook/bin/chub.sh validate
  bash .timely-playbook/bin/chub.sh search timely-playbook --json
  bash .timely-playbook/bin/chub.sh get timely-playbook/timely-playbook
  bash .timely-playbook/bin/chub-mcp.sh
  ```

- Set `CHUB_TELEMETRY=0` if you want to disable telemetry without editing the
  generated config file.

## CXDB and LEANN workflow

- Use [CXDB-LEANN-Integration.md](CXDB-LEANN-Integration.md) for the full
  architecture notes.
- The canonical project-local store lives at
  `.timely-playbook/local/.cxdb/cxdb.sqlite3`.
- The derived retrieval index lives at
  `.timely-playbook/local/.leann/index.json`.
- Typical sequence:

  ```bash
  python .timely-playbook/bin/orchestrator.py update-status
  python .timely-playbook/bin/orchestrator.py context-search "ready tasks"
  ```

## Packaging and reuse

Create a fresh packaged snapshot:

```bash
make compile
```

This generates:
- `dist/timely-template`
- `dist/timely-template.tgz`
- Release workflow assets:
  `timely-playbook_<os>_<arch>.tar.gz`, `timely-template.tgz`,
  `timely-checksums.txt`

Seed from the current source tree directly:

```bash
bash .timely-playbook/bin/timely-playbook seed \
  --output /path/to/new-repo \
  --owner "Jane Doe" \
  --email "jane@example.com" \
  --repo "new-repo"
```

Verify the archive contents before shipping:

```bash
tar -tzf dist/timely-template.tgz | grep -E '\.timely-core/manifest\.json|\.timely-core/scripts/bootstrap-timely-template\.sh|\.timely-core/scripts/bootstrap-timely-release\.sh|\.timely-playbook/bin/install-agent-skill\.sh|\.timely-playbook/bin/install-codex-skill\.sh|\.timely-playbook/local/skills/chub-context-hub/SKILL\.md'
```

Publish a release by pushing a `v*` tag. The generated
`.github/workflows/release.yml` workflow verifies the repo, builds macOS/Linux
CLI archives, publishes `timely-template.tgz`, and emits `timely-checksums.txt`
for the bootstrap script.

### Cross-machine bootstrap flow

```bash
scp dist/timely-template.tgz vm:/tmp/timely-template.tgz
ssh vm 'mkdir -p /tmp && tar -xzf /tmp/timely-template.tgz -C /tmp && \
  bash /tmp/timely-template/.timely-playbook/bin/bootstrap-timely-template.sh \
    --source /tmp/timely-template \
    --output ~/projects/aurora \
    --owner "Aurora Ops" \
    --email "ops@example.com" \
    --repo "aurora" \
    --init-git'
```

Sanity check in the new repo:

```bash
[ -f ~/projects/aurora/.timely-playbook/config.yaml ] && \
[ -f ~/projects/aurora/.timely-core/manifest.json ]
```

## Recommended release checklist

1. Run `npm ci --prefix .timely-playbook/runtime`.
2. Run `make verify`.
3. Confirm license and contribution docs are current.
4. Push the release tag (`git tag vX.Y.Z && git push origin vX.Y.Z`) so
   `.github/workflows/release.yml` can publish the binary archives, template
   tarball, and checksums.
