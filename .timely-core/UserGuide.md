# Timely Playbook User Guide

This guide covers the common operator workflows for the Timely Playbook
repository itself: setup, validation, Context Hub usage, packaging, and template
export.

## Prerequisites
- Go 1.24 or newer
- Python 3 with `unittest`
- Node.js 22.22.0+ (22.x) and npm 10.x
- Git and Bash

## Initial setup
1. Install the pinned Node dependencies:

   ```bash
   npm ci --prefix .timely-playbook/runtime
   ```

2. Review the main operator docs:
   - `TimelyPlaybook.md`
   - `HOWTO.md`
   - `Context-Hub-Integration.md`
   - `Conductor-Orchestration.md`

3. Build package artifacts only when you need a fresh distributable export:

   ```bash
   make compile
   ```

## Common validation workflows
### Documentation checks

```bash
bash .timely-playbook/bin/run-markdownlint.sh
bash .timely-playbook/bin/check-doc-links.sh
```

### Unit and tooling checks

```bash
python -m unittest discover -s .timely-core/tests -p 'test_*.py'
bash .timely-playbook/bin/chub.sh validate
bash .timely-playbook/bin/bootstrap-smoke.sh --smoke
```

### Context Hub usage

```bash
bash .timely-playbook/bin/chub.sh search timely-playbook --json
bash .timely-playbook/bin/chub.sh get timely-playbook/timely-playbook --json
```

## Seeding a new repository
Use the Timely CLI or the bootstrap script to create a fresh downstream repo.
`HOWTO.md` documents both the local-source and packaged-artifact paths.

For a quick seed from the current checkout:

```bash
timely-playbook seed \
  --output ~/projects/aurora \
  --owner "Aurora Ops" \
  --email "ops@example.com" \
  --repo "aurora"
```

This default seed path also installs `.timely-playbook/runtime/node_modules`
and prepares `.chub/` so Context Hub is ready immediately.

## Packaging and publishing
- Run `make compile` after source changes so `dist/timely-template` matches the
  repository root.
- Re-run the smoke check against the packaged output before publishing.
- Confirm license, contribution guidance, and secret-scrub expectations are
  still satisfied for the public release.

## Troubleshooting
- If `npm ci --prefix .timely-playbook/runtime` fails, verify the local Node
  version meets the documented floor.
- If Context Hub commands fail, re-run
  `bash .timely-playbook/bin/chub.sh validate` from the repo root to
  regenerate the local mirror.
- If packaging output looks stale, delete `dist/timely-template` and rerun
  `make compile`.
- If tracker evidence is missing, append the validation run before closing the task.
