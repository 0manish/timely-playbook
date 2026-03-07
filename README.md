# Timely Playbook

Timely Playbook is a repository template for orchestrated, Codex-ready projects.

## Quick start

Use this flow to adopt Timely in a new project repository.

### 1) Install dependencies and build the CLI

```bash
npm ci
make compile
```

This installs the pinned Node tooling and builds `./.bin/timely-playbook`.

### 2) Seed a new repository

```bash
./.bin/timely-playbook seed \
  --output /path/to/new-repo \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "new-repo"
```

This creates the template scaffold with governance files, trackers, templates, scripts,
skills, and runtime defaults.

### 3) Initialize configuration

```bash
cd /path/to/new-repo
./.bin/timely-playbook init-config \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "$(basename "$(pwd)")"
```

### 4) Validate and verify installability

```bash
make validate
```

Use `make verify` for a full installability check including template packaging and bootstrap smoke test.

### 5) Start operating

- `timely-playbook append journal|ledger|backlog ...`
- `timely-playbook run-weekly`
- `bash scripts/chub.sh build`
- `bash scripts/chub.sh validate`
- `bash scripts/install-codex-skill.sh chub-context-hub`

## Existing repository migration

`seed` is safest for clean directories. For an existing populated repo, seed first to a
temporary location, then copy only the pieces you want.

```bash
# 1) create a clean mirror
./.bin/timely-playbook seed \
  --output /tmp/timely-seed \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "your-repo"

# 2) copy selected assets into your existing repo
cp -R /tmp/timely-seed/AGENTS.md /tmp/timely-seed/SKILLS.md \
  /tmp/timely-seed/timely-trackers /tmp/timely-seed/templates \
  /tmp/timely-seed/scripts /path/to/existing-repo/
cp -R /tmp/timely-seed/skills /path/to/existing-repo/
cp -R /tmp/timely-seed/.vscode /tmp/timely-seed/.github /tmp/timely-seed/.orchestrator \
  /path/to/existing-repo/
```

If you must seed directly into an existing directory, use `--allow-existing` only after a
full backup.

```bash
./.bin/timely-playbook seed \
  --output /path/to/existing-repo \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "your-repo" \
  --allow-existing
```

## Publishing this repository

Before pushing to GitHub, run:

```bash
make verify
make compile
```

Then push:

```bash
git init
git add .
git commit -m "Initial Timely Playbook release"
git remote add origin <your-github-remote-url>
git branch -M main
git push -u origin main
```

Optional pre-push checks:

```bash
git status --short
git log --oneline --decorate -n 1
```

If your branch name is `master`, adjust accordingly:

```bash
git push -u origin master
```

## References

- [TimelyPlaybook.md](TimelyPlaybook.md)
- [AutomationPlaybook-GettingStarted.md](AutomationPlaybook-GettingStarted.md)
- [Timely-Governance-Index.md](Timely-Governance-Index.md)
- [Context-Hub-Integration.md](Context-Hub-Integration.md)
