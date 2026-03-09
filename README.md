# Timely Playbook

Timely Playbook is a repository template for orchestrated, agent-ready projects.
It ships with Codex as the default execution path, but the orchestrator, CI
hooks, and governance model are provider-pluggable. It also integrates Context
Hub so operators and agents can pull current repo docs and public API docs from
the same local surface, and it now ships CXDB plus LEANN as the default
project-local context plane.

## Quick start

Use this flow to adopt Timely in a new project repository.

### 1) Bootstrap from the latest release

```bash
curl -fsSL https://raw.githubusercontent.com/<org>/<timely-playbook-repo>/main/.timely-core/scripts/bootstrap-timely-release.sh | bash -s -- \
  --release-repo <org>/<timely-playbook-repo> \
  --output /path/to/new-repo \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "new-repo" \
  --init-git
```

This downloads the latest published `timely-playbook` binary plus
`timely-template.tgz`, verifies the release checksums, installs the CLI to
`~/.local/bin` by default, and seeds the new repo in one step. This path does
not require a local Go toolchain.

### 2) Install runtime dependencies and use the generated launcher

```bash
npm ci --prefix .timely-playbook/runtime
bash .timely-playbook/bin/timely-playbook help
```

This installs the pinned Node tooling and confirms the relocated launcher can
build the CLI from the template source on demand.

### 3) Seed a new repository from a source checkout

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
- `.timely-playbook/local/.cxdb/` for project-local context storage
- `.timely-playbook/local/.leann/` for project-local retrieval indexes
- `.timely-playbook/runtime/` for repo-local runtime dependencies
- `.chub/` for generated Context Hub state

The default seed path also runs `npm ci --prefix .timely-playbook/runtime` and
prebuilds the local `.chub/` mirror so Context Hub is ready immediately.

### 4) Initialize configuration

```bash
cd /path/to/new-repo
bash .timely-playbook/bin/timely-playbook init-config \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "$(basename "$(pwd)")"
```

### 5) Validate and verify installability

```bash
go test ./.timely-core/cmd/timely-playbook/...
python -m unittest discover -s .timely-core/tests -p 'test_*.py'
bash .timely-playbook/bin/chub.sh validate
python .timely-playbook/bin/orchestrator.py context-sync
bash .timely-playbook/bin/run-markdownlint.sh
bash .timely-playbook/bin/check-doc-links.sh
```

Template maintainers can still use `make validate` and `make verify` from the
Timely source repository. Re-run `npm ci --prefix .timely-playbook/runtime`
only if you clear the seeded runtime dependencies.

### 6) Start operating

- `timely-playbook help` if you installed the release binary onto your `PATH`
- `bash .timely-playbook/bin/timely-playbook append journal|ledger|backlog ...`
- `bash .timely-playbook/bin/timely-playbook run-weekly`
- `python .timely-playbook/bin/orchestrator.py context-sync`
- `python .timely-playbook/bin/orchestrator.py context-search "ready tasks"`
- `bash .timely-playbook/bin/chub.sh build`
- `bash .timely-playbook/bin/chub.sh validate`
- `bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub`

Context Hub is prebuilt during seed by default, and then stays on-demand. It
does not run silently in the background. Use `bash .timely-playbook/bin/chub.sh
...` for CLI access or
`bash .timely-playbook/bin/chub-mcp.sh` to start the MCP server; those wrappers
regenerate the Timely mirror and build `.chub/` automatically when invoked.

Full-stack runs default to the `codex` provider. To use another agent CLI,
define it in `.timely-playbook/local/.orchestrator/fullstack-agent.json` and
pass `--provider <name>` to `python .timely-playbook/bin/orchestrator.py
fullstack-run` or `fullstack-run-all`.

The generated repo launcher builds from `.timely-core/` when Go is available,
and falls back to an installed `timely-playbook` binary only when Go is not
present.

## Existing repository migration

Use `seed` for clean directories. For an existing Timely repo that still uses
the legacy root layout, run the in-place migration command instead.

```bash
bash .timely-playbook/bin/timely-playbook migrate-layout
```

This backs up the original Timely-owned files under
`.timely-playbook/migration-backups/<timestamp>/`, writes the relocated layout,
and leaves root `README.md`, `AGENTS.md`, `SKILLS.md`,
`.github/workflows/*.yml`, and `.vscode/tasks.json` as generated public
surface files and dispatchers.

To refresh the immutable snapshot later without overwriting local customizations:

```bash
bash .timely-playbook/bin/timely-playbook refresh-core --source /path/to/timely-playbook
```

## References

- [TimelyPlaybook.md](.timely-core/TimelyPlaybook.md)
- [AutomationPlaybook-GettingStarted.md](.timely-core/AutomationPlaybook-GettingStarted.md)
- [HOWTO.md](.timely-core/HOWTO.md) — Step-by-step instructions for starting a new project
  from the Timely template, including clean-machine bootstrap, smoke checks,
  tailoring, and validation after seeding.
- [Timely-Governance-Index.md](.timely-core/Timely-Governance-Index.md)
- [CXDB-LEANN-Integration.md](.timely-core/CXDB-LEANN-Integration.md)
- [Context-Hub-Integration.md](.timely-core/Context-Hub-Integration.md)
