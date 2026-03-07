# Timely Playbook

Timely Playbook is a repository template for orchestrated, agent-ready projects.
It ships with Codex as the default execution path, but the orchestrator, CI
hooks, and governance model are provider-pluggable. It also integrates Context
Hub so operators and agents can pull current repo docs and public API docs from
the same local surface.

## Quick start

Use this flow to adopt Timely in a new project repository.

### 1) Install runtime dependencies and use the generated launcher

```bash
npm ci --prefix .timely-playbook/runtime
bash .timely-playbook/bin/timely-playbook help
```

This installs the pinned Node tooling and confirms the relocated launcher can
build the CLI from the template source on demand.

### 2) Seed a new repository

```bash
bash .timely-playbook/bin/timely-playbook seed \
  --output /path/to/new-repo \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "new-repo"
```

This creates a relocated Timely scaffold:

- `.timely-core/` for the read-only Timely snapshot
- `.timely-playbook/local/` for repo-specific Timely content
- `.timely-playbook/runtime/` for repo-local runtime dependencies
- `.chub/` for generated Context Hub state

### 3) Initialize configuration

```bash
cd /path/to/new-repo
bash .timely-playbook/bin/timely-playbook init-config \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "$(basename "$(pwd)")"
```

### 4) Validate and verify installability

```bash
npm ci --prefix .timely-playbook/runtime
go test ./.timely-core/cmd/timely-playbook/...
python -m unittest discover -s .timely-core/tests -p 'test_*.py'
bash .timely-playbook/bin/chub.sh validate
bash .timely-playbook/bin/run-markdownlint.sh
bash .timely-playbook/bin/check-doc-links.sh
```

Template maintainers can still use `make validate` and `make verify` from the
Timely source repository.

### 5) Start operating

- `bash .timely-playbook/bin/timely-playbook append journal|ledger|backlog ...`
- `bash .timely-playbook/bin/timely-playbook run-weekly`
- `bash .timely-playbook/bin/chub.sh build`
- `bash .timely-playbook/bin/chub.sh validate`
- `bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub`

Context Hub is on-demand. It does not run silently in the background. Use
`bash .timely-playbook/bin/chub.sh ...` for CLI access or
`bash .timely-playbook/bin/chub-mcp.sh` to start the MCP server; those wrappers
regenerate the Timely mirror and build `.chub/` automatically when invoked.

Full-stack runs default to the `codex` provider. To use another agent CLI,
define it in `.timely-playbook/local/.orchestrator/fullstack-agent.json` and
pass `--provider <name>` to `python .timely-playbook/bin/orchestrator.py
fullstack-run` or `fullstack-run-all`.

## Existing repository migration

Use `seed` for clean directories. For an existing Timely repo that still uses
the legacy root layout, run the in-place migration command instead.

```bash
bash .timely-playbook/bin/timely-playbook migrate-layout
```

This backs up the original Timely-owned files under
`.timely-playbook/migration-backups/<timestamp>/`, writes the relocated layout,
and leaves root `AGENTS.md`, `SKILLS.md`, `.github/workflows/*.yml`, and
`.vscode/tasks.json` as generated dispatchers only.

To refresh the immutable snapshot later without overwriting local customizations:

```bash
bash .timely-playbook/bin/timely-playbook refresh-core --source /path/to/timely-playbook
```

## References

- [TimelyPlaybook.md](TimelyPlaybook.md)
- [AutomationPlaybook-GettingStarted.md](AutomationPlaybook-GettingStarted.md)
- [HOWTO.md](HOWTO.md) — Step-by-step instructions for starting a new project
  from the Timely template, including clean-machine bootstrap, smoke checks,
  tailoring, and validation after seeding.
- [Timely-Governance-Index.md](Timely-Governance-Index.md)
- [Context-Hub-Integration.md](Context-Hub-Integration.md)
