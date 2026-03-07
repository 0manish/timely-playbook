# Start a new project from the Timely Playbook template

Use these steps whenever you spin up a fresh repo that should inherit the
orchestrator-ready scaffolding.

1. **Seed the new repository:**

   ```bash
   timely-playbook seed \
     --output ~/projects/aurora \
     --owner "Aurora Ops" \
     --email "ops@example.com" \
     --repo "aurora"
   ```

   This creates a fully copied workspace in one step, preserving template
   structure and stamping operator metadata. The seeded repo inherits the
   governance baseline (`AGENTS.md`) and the Codex skill contract (`SKILLS.md`)
   from the template.

2. **Finish setup:**

   ```bash
   cd ~/projects/aurora
   python tools/orchestrator/orchestrator.py update-status
   ```

   Then add the remote with `git remote add origin <git-url>`.

## One-shot bootstrap on a clean machine

From any host with `git` and `go`:

```bash
git clone https://github.com/<org>/<timely-playbook-repo>.git ~/timely-playbook
bash ~/timely-playbook/scripts/bootstrap-timely-template.sh \
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
  bash /tmp/timely-template/scripts/bootstrap-timely-template.sh \
    --source /tmp/timely-template \
    --output ~/projects/aurora \
    --owner "Aurora Ops" \
    --email "ops@example.com" \
    --repo "aurora" \
    --init-git'
```

Verify baseline files after bootstrap:

```bash
[ -f ~/projects/aurora/AGENTS.md ] && [ -f ~/projects/aurora/SKILLS.md ]
```

## Smoke check for bootstrap tooling

```bash
bash ~/timely-playbook/scripts/bootstrap-smoke.sh --smoke
```

Run this only when verifying the template bootstrap path end to end. To use the
repo Makefile convenience target, run:

```bash
make -C ~/timely-playbook test-smoke
```

## Tailor the seeded repository

1. Edit `.orchestrator/ownership.yaml` for the new stack, update
   `.orchestrator/state.json` with project goals and tasks, then run:

   ```bash
   python tools/orchestrator/orchestrator.py update-status
   ```

2. Regenerate `timely-playbook.yaml` with the new owner and email via
   `timely-playbook init-config`.
3. Update `AGENTS.md`, `Conductor-Orchestration.md`, `.github/workflows/*.yml`,
   and VS Code tasks to reflect the downstream repo’s specifics before pushing.

## Validate the seeded repository

Run the standard checks after seeding and before opening the repo to other
contributors:

```bash
python -m unittest discover -s tests -p 'test_*.py'
./scripts/run-markdownlint.sh
./scripts/check-doc-links.sh
bash scripts/chub.sh validate
```

If you plan to distribute the template or test the package path, also run:

```bash
make compile
bash scripts/bootstrap-smoke.sh --smoke
```

## Publish a refreshed template package

From the Timely repository root:

```bash
make compile
tar -tzf dist/timely-template.tgz | head
```

This confirms that the packaged export was rebuilt from the current source
files. Do not edit `dist/` directly.
