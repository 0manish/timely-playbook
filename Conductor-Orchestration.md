# Conductor orchestration blueprint

Use this document to roll the Timely Playbook template into a Codex-enabled,
multi-agent workspace. Every section mirrors the modernized approach described
in `modplan.md`; that content now lives here.

## Target architecture

- **In-editor plane:** VS Code with the Codex extension runs interactive and
  background agents. Humans (or a manager agent) use Plan mode, subagents, and
  Agent HQ to triage work, delegate tasks, and review diffs in real time.
- **Automation plane:** `tools/orchestrator/orchestrator.py` plus the OpenAI
  Agents SDK (optional) execute deterministic workflows: parsing goals, spinning
  up specialist agents, editing files, tagging Git branches, and calling CI/CD
  APIs.
- **Shared context:** `.orchestrator/state.json`,
  `.orchestrator/ownership.yaml`, and `.orchestrator/STATUS.md` record project
  state so each plane—and every agent—reads from the same source of truth.

## Prerequisites

1. Install the OpenAI Codex VS Code extension and ensure it can access the repo.
2. Install Codex CLI plus MCP config (`~/.codex/config.toml`) so the
   orchestrator can call Codex as a tool.
3. Install Python 3.11+ with the OpenAI Agents SDK (or plain `requests` for the
   included helper scripts).
4. Install Node `22.22.0+` (22.x), then run `npm ci` so the repo-local
   Context Hub and Markdown validation tools are available.
5. Configure `timely-playbook.yaml` using `timely-playbook init-config` to stamp
   owner metadata into trackers.
6. In the Git hosting provider (e.g., GitHub), add an `OPENAI_API_KEY`
   repository secret so `.github/workflows/autofix.yml` can authenticate when
   Codex attempts CI repairs.

## Repository conventions

- `AGENTS.md` is the canonical context pack: architecture overview, doc
  guardrails, test cadence, and automation hooks. Always feed it into AI agents
  before editing docs.
- `.orchestrator/ownership.yaml` prevents agents from stepping on each other by
  mapping paths to personas and escalation owners.
- `.orchestrator/state.json` maintains tasks, dependencies, CI events, and
  deployment decisions for the conductor.
- `.orchestrator/STATUS.md` offers a human-friendly dashboard. Refresh it via
  `python tools/orchestrator/orchestrator.py update-status` or the VS Code task
  `Orchestrator: status`.
- `.vscode/tasks.json` declares one-click automation to run the conductor
  locally (plan, start ready tasks, record CI runs).
- `.github/workflows/ci.yml` and `.github/workflows/autofix.yml` implement
  validation, packaging, bootstrap smoke checks, and Codex-powered autofix.
- `scripts/chub.sh`, `scripts/chub-mcp.sh`, and `tools/chub/timely_registry.py`
  provide the repo-local Context Hub surface for mirrored Timely docs plus
  public API registry access.

## Agent roster and conductor design

- **Planner:** Breaks a product goal into structured tasks, updating
  `state.json` with dependencies and sequencing metadata.
- **Architect (optional):** Validates interface contracts and technology choices
  before coding tasks start.
- **Implementers (frontend/backend/docs/tests/infra):** Each implements tasks
  within its ownership area and commits to a scoped branch
  (`agent/<task-id>-<owner>`).
- **Tester:** Generates or runs automated checks and records CI URLs.
- **Reviewer / devil's advocate:** Performs code reviews or risk analysis before
  merge—captured via `orchestrator.py review <task> <verdict>`.
- **DevOps:** Manages deployment events
  (`orchestrator.py deploy staging succeeded`) and rollbacks.
- The conductor (`tools/orchestrator/orchestrator.py`) acts as the mission
  control layer. It uses Agents SDK patterns to call Codex via MCP, orchestrates
  git actions (see `tools/orchestrator/helpers/git_tools.py`), and records CI
  telemetry (`tools/orchestrator/helpers/ci_tools.py`).

## Implementation phases

1. **Phase A – Single-agent but structured:** Run the planner → implementer →
   tester flow sequentially using the provided script. Record progress in
   `.orchestrator/state.json` and open PRs manually.
2. **Phase B – Parallel implementers:** Planner assigns owners, conductor
   creates isolated branches/worktrees, and implementers run in parallel
   (background agents in VS Code or via CLI). Reviewer gates merges once CI is
   green.
3. **Phase C – CI failure auto-repair:** `.github/workflows/autofix.yml`
   triggers Codex-based remediation whenever the `CI` workflow fails, opening a
   follow-up PR.
4. **Phase D – Deployment agent + verification:** DevOps agent (backed by
   `orchestrator.py deploy`) records staging/prod deployments, triggers smoke
   tests, and initiates rollbacks when necessary.

## VS Code workflow

- Launch Plan mode to convert vague work items into structured steps; either
  hand off tasks through the UI or paste them into `orchestrator.py plan`.
- Use Agent Sessions / Agent HQ to monitor background agents, ensuring each maps
  to a single task/branch defined in `.orchestrator/state.json`.
- Run the `.vscode` tasks to keep state files in sync without memorizing CLI
  commands.
- When subagents need extra context (docs, diagrams), hand them relative paths
  so their edits respect the guardrail in `AGENTS.md`.

## Guardrails

- Enforce ownership boundaries through `.orchestrator/ownership.yaml` and
  guardrails described in `AGENTS.md`.
- Keep `.github/workflows/ci.yml` green before merging: orchestrator status
  refresh, `make validate`, `make compile`, and bootstrap smoke.
- Require reviewer approvals (human or AI) for infra/auth/db changes; record the
  verdict with `orchestrator.py review`.
- Use branch protections and limit CI/autofix workflows to least privilege (no
  production secrets, principle of least access).
- Record doc validation evidence in `timely-trackers/test-run-journal.md` using
  `timely-playbook append journal`.

## Deliverables & automation hooks

- `tools/orchestrator/` provides sample
  Planner/Implementer/Tester/Reviewer/DevOps agent classes plus helper
  utilities.
- `tools/orchestrator/fullstack.py` adds a reusable FullStack-Agent phase
  pipeline (architecture, backend, frontend, integration, back-translation).
- `.github/workflows/ci.yml` standardizes lint + link validation;
  `.github/workflows/autofix.yml` runs the Codex repair loop.
- `scripts/run-markdownlint.sh` and `scripts/check-doc-links.sh` simplify
  validation calls locally and in CI.
- `requirements.txt` enumerates Python dependencies (`requests` for CI queries).
  Extend as your orchestrator grows.
- `package.json` pins `@aisuite/chub` so `scripts/chub.sh` and
  `scripts/chub-mcp.sh` resolve a stable local Context Hub toolchain.
- Update `.orchestrator/state.json` and `.orchestrator/STATUS.md` after every
  orchestrator run so Agent HQ and CI stay synchronized.

## Context Hub workflow

- Use `bash scripts/chub.sh validate` to verify the generated Timely mirror.
- Use `bash scripts/chub.sh search <query>` and `bash scripts/chub.sh get <id>`
  when agents need current public API docs or repo-authored Timely guidance from
  the same interface.
- Use `bash scripts/chub-mcp.sh` to expose the merged registry as MCP tools for
  Codex or other MCP-capable clients.
- Keep the dedicated operator instructions in
  [`Context-Hub-Integration.md`](Context-Hub-Integration.md) synchronized with
  wrapper behavior and CI expectations.

## FullStack-Agent workflow

Run this flow to execute a reusable full-stack build pipeline inspired by arXiv
`2602.03798`:

1. `python tools/orchestrator/orchestrator.py fullstack-init-config`
1. `python tools/orchestrator/orchestrator.py fullstack-sync`
1.

   ```bash
   python tools/orchestrator/orchestrator.py fullstack-bootstrap \
     <project_id> \
     --brief-file <file> \
     --template <template>
   ```

1. `python tools/orchestrator/orchestrator.py fullstack-plan <project_id>`
1. Either run phases one-by-one with `fullstack-run`, or execute
   `python tools/orchestrator/orchestrator.py fullstack-run-all <project_id>`.
1. Optional strict profile runs can pass `--skill` to use `SKILLS.md` overlays.
1. If running one-by-one, execute: `architecture`, `backend`, `frontend`,
   `integration`, `backtranslation`.
1. `python tools/orchestrator/orchestrator.py fullstack-status <project_id>`

Reference: `FullStack-Agent-Integration.md`.

## OpenAI Agents SDK usage

- Treat `tools/orchestrator/orchestrator.py` as a minimal entry point. Expand it
  into a full Agents SDK workflow by:
  - Running `codex` as an MCP server exposed to your orchestrator.
  - Defining specialized planner/tester/reviewer tools that call Codex via MCP
    or CLI wrappers (`tools/orchestrator/helpers/codex_tools.py`).
  - Using state files as deterministic memory that travels between Agents SDK
    runs and VS Code sessions.

## Next steps

1. Seed each new project via the one-shot flow:
   - `bash`:

     ```bash
     bash scripts/bootstrap-timely-template.sh \
       --template-repo <repo-url> \
       --output <path> \
       --owner "<name>" \
       --email "<email>" \
       --repo "<repo-name>" \
       [--init-git]
     ```

2. Edit `.orchestrator/ownership.yaml` to match your stack.
3. Replace placeholder tasks inside `.orchestrator/state.json`.
4. Add per-project scripts/tests and wire them into `.github/workflows/ci.yml`.
5. Keep `TimelyPlaybook.md` in sync with lessons learned so the template evolves
   over time.
