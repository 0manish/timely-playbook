# Timely Playbook

Timely Playbook is a repository template for orchestrated, Codex-ready projects.

## Use Timely in your project repository

This is the simplest path to adopt Timely for a new repository.

### 1) Install dependencies and build the CLI

```bash
npm ci
make compile
```

This installs the repo-local Node tooling and builds `./.bin/timely-playbook`.

### 2) Seed a new repo from the template

```bash
./.bin/timely-playbook seed \
  --output /path/to/new-repo \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "new-repo"
```

This creates a fresh repo with Timely governance files, trackers, templates, scripts,
skills, and default configuration scaffold.

### 3) Initialize configuration

```bash
cd /path/to/new-repo
./.bin/timely-playbook init-config \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "$(basename "$(pwd)")"
```

### 4) Run standard checks

```bash
make validate
```

Use `make verify` for full installability and packaging validation, including the
bootstrap smoke test.

### 5) Start operating

- `timely-playbook append journal|ledger|backlog ...`
- `timely-playbook run-weekly`
- `bash scripts/chub.sh build` / `bash scripts/chub.sh validate`
- `bash scripts/install-codex-skill.sh chub-context-hub`

## Using Timely with an existing repo

`seed` works best on a clean destination directory. For an existing populated repo,
seed into a new directory first, then merge the governance files you want into your
project, or initialize a fresh project from a new directory.

Proper CLI migration flow:

```bash
# Step 1: create a clean mirror in a temp location
./.bin/timely-playbook seed \
  --output /tmp/timely-seed \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "your-repo"

# Step 2: copy only what you want into an existing repo
cp -R /tmp/timely-seed/AGENTS.md /tmp/timely-seed/SKILLS.md /tmp/timely-seed/timely-trackers /tmp/timely-seed/templates /tmp/timely-seed/scripts /path/to/existing-repo/
cp -R /tmp/timely-seed/skills /path/to/existing-repo/
cp -R /tmp/timely-seed/.vscode /tmp/timely-seed/.github /tmp/timely-seed/.orchestrator /path/to/existing-repo/
```

If you want to force-seed directly into an existing directory, use `--allow-existing`,
but only after you have a manual backup of that directory:

```bash
./.bin/timely-playbook seed \
  --output /path/to/existing-repo \
  --owner "Your Name" \
  --email "you@example.com" \
  --repo "your-repo" \
  --allow-existing
```

See [AutomationPlaybook-GettingStarted.md](AutomationPlaybook-GettingStarted.md) and
[TimelyPlaybook.md](TimelyPlaybook.md) for the full command reference and
workflow details.

## Public release checklist

Before pushing this repo to a public GitHub remote, run:

```bash
make verify
make compile
```

Then initialize git, commit, and push:

```bash
git init
git add .
git commit -m "Initial Timely Playbook release"
git remote add origin <your-github-remote-url>
git branch -M main
git push -u origin main
```

Optional verification before first push:

```bash
git status --short
git log --oneline --decorate -n 1
```
