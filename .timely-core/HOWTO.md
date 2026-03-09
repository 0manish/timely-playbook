# Start a new project from the Timely Playbook template

Use these steps whenever you spin up a fresh repo that should inherit the
orchestrator-ready scaffolding.

## Recommended end-user path: bootstrap from a published release

```bash
curl -fsSL https://raw.githubusercontent.com/<org>/<timely-playbook-repo>/main/.timely-core/scripts/bootstrap-timely-release.sh | bash -s -- \
  --release-repo <org>/<timely-playbook-repo> \
  --output ~/projects/aurora \
  --owner "Aurora Ops" \
  --email "ops@example.com" \
  --repo "aurora" \
  --init-git
```

This installs the released `timely-playbook` binary to `~/.local/bin` by
default, downloads `timely-template.tgz`, verifies the checksums, and seeds the
repo in one step. Use `--version vX.Y.Z` if you need a specific tag instead of
the latest release.

## Source checkout path: seed from the current template tree

1. **Seed the new repository:**

   ```bash
   bash .timely-playbook/bin/timely-playbook seed \
     --output ~/projects/aurora \
     --owner "Aurora Ops" \
     --email "ops@example.com" \
     --repo "aurora"
   ```

   This creates a relocated Timely workspace in one step. The seeded repo gets
   a read-only `.timely-core/`, an editable `.timely-playbook/local/`,
   project-local CXDB and LEANN directories under
   `.timely-playbook/local/.cxdb/` and `.timely-playbook/local/.leann/`,
   a repo-local runtime under `.timely-playbook/runtime/`, and generated root
   files for `README.md`, `AGENTS.md`, `SKILLS.md`,
   `.github/workflows/*.yml`, and `.vscode/tasks.json`. It also installs the
   repo-local runtime dependencies and prepares `.chub/` by default.

2. **Finish setup:**

   ```bash
   cd ~/projects/aurora
   python .timely-playbook/bin/orchestrator.py update-status
   ```

   Then add the remote with `git remote add origin <git-url>`.

   `update-status` imports the portable
   `.timely-playbook/local/.orchestrator/state.json` snapshot into
   `.timely-playbook/local/.cxdb/cxdb.sqlite3`, refreshes
   `.timely-playbook/local/.leann/index.json`, and rewrites `STATUS.md`.

   Context Hub is not a silent background service. It is prepared on demand
   when you run `bash .timely-playbook/bin/chub.sh ...`,
   `bash .timely-playbook/bin/chub-mcp.sh`, or repo validation commands.

## One-shot bootstrap on a clean machine from a source checkout

From any host with `git`, `go`, `npm`, and `python`:

```bash
git clone https://github.com/<org>/<timely-playbook-repo>.git ~/timely-playbook
bash ~/timely-playbook/.timely-playbook/bin/bootstrap-timely-template.sh \
  --template-repo https://github.com/<org>/<timely-playbook-repo>.git \
  --output ~/projects/aurora \
  --owner "Aurora Ops" \
  --email "ops@example.com" \
  --repo "aurora" \
  --init-git
```

This performs clone plus seed in one step. For local templates, use `--source`
instead of `--template-repo`.

## One-shot bootstrap from packaged artifact

From any host with the packaged template:

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

Verify baseline files after bootstrap:

```bash
[ -f ~/projects/aurora/.timely-playbook/config.yaml ] && \
[ -f ~/projects/aurora/.timely-core/manifest.json ]
```

If you already installed the release binary, you can also bootstrap from a
packaged artifact with:

```bash
timely-playbook seed \
  --output ~/projects/aurora \
  --owner "Aurora Ops" \
  --email "ops@example.com" \
  --repo "aurora"
```

## Smoke check for bootstrap tooling

```bash
bash ~/timely-playbook/.timely-playbook/bin/bootstrap-smoke.sh --smoke
```

Run this only when verifying the template bootstrap path end to end. To use the
repo Makefile convenience target, run:

```bash
make -C ~/timely-playbook test-smoke
```

## Tailor the seeded repository

1. Edit `.timely-playbook/local/.orchestrator/ownership.yaml` and
   `.timely-playbook/local/.orchestrator/state.json`, then regenerate
   `.timely-playbook/config.yaml` with the new owner and email via
   `bash .timely-playbook/bin/timely-playbook init-config`.
   Refresh the status dashboard with:

   ```bash
   python .timely-playbook/bin/orchestrator.py update-status
   ```

   If you manually edit guardrails, trackers, or `state.json`, resync the
   project-local context plane with:

   ```bash
   python .timely-playbook/bin/orchestrator.py context-sync
   ```

2. Update the canonical local files under `.timely-playbook/local/`, especially
   `AGENTS.md`, `SKILLS.md`, trackers, and any repo-specific workflow/task
   settings before pushing.

## Validate the seeded repository

Run the standard checks after seeding and before opening the repo to other
contributors:

```bash
go test ./.timely-core/cmd/timely-playbook/...
python -m unittest discover -s .timely-core/tests -p 'test_*.py'
bash .timely-playbook/bin/run-markdownlint.sh
bash .timely-playbook/bin/check-doc-links.sh
bash .timely-playbook/bin/chub.sh validate
python .timely-playbook/bin/orchestrator.py context-sync
```

Re-run `npm ci --prefix .timely-playbook/runtime` only if the seeded runtime
dependencies were cleared or need to be refreshed.

The `chub` wrappers build the local mirror automatically when invoked, so there
is no separate daemon to start unless you specifically want the MCP server via
`bash .timely-playbook/bin/chub-mcp.sh`.

If you plan to distribute the template or test the package path, also run:

```bash
make compile
bash .timely-playbook/bin/bootstrap-smoke.sh --smoke
```

## Publish a refreshed template package

From the Timely repository root:

```bash
make compile
tar -tzf dist/timely-template.tgz | head
```

This confirms that the packaged export was rebuilt from the current source
files. Do not edit `dist/` directly.
