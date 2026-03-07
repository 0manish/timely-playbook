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
   npm ci
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
./scripts/run-markdownlint.sh
./scripts/check-doc-links.sh
```

### Unit and tooling checks

```bash
python -m unittest discover -s tests -p 'test_*.py'
bash scripts/chub.sh validate
bash scripts/bootstrap-smoke.sh --smoke
```

### Context Hub usage

```bash
bash scripts/chub.sh search timely-playbook --json
bash scripts/chub.sh get timely-playbook/timely-playbook --json
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

## Packaging and publishing
- Run `make compile` after source changes so `dist/timely-template` matches the
  repository root.
- Re-run the smoke check against the packaged output before publishing.
- Confirm license, contribution guidance, and secret-scrub expectations are
  still satisfied for the public release.

## Troubleshooting
- If `npm ci` fails, verify the local Node version meets the documented floor.
- If Context Hub commands fail, re-run `bash scripts/chub.sh validate` from the
  repo root to regenerate the local mirror.
- If packaging output looks stale, delete `dist/timely-template` and rerun
  `make compile`.
- If tracker evidence is missing, append the validation run before closing the task.
