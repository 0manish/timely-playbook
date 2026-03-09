# Conductor orchestration blueprint

Use this document to roll the Timely Playbook template into an agent-ready,
multi-agent workspace. Codex is the shipped default path, but the surrounding
orchestrator and governance flow are designed to admit other providers.

## Target architecture

- **In-editor plane:** VS Code with your chosen agent extension or CLI bridge
  runs interactive and background agents. Humans (or a manager agent) use Plan
  mode, subagents, and Agent HQ to triage work, delegate tasks, and review
  diffs in real time.
- **Automation plane:** `python .timely-playbook/bin/orchestrator.py` plus the
  OpenAI Agents SDK (optional) execute deterministic workflows: parsing goals,
  spinning up specialist agents, editing files, tagging Git branches, and
  calling CI/CD APIs.
- **Shared context:** `.timely-playbook/local/.cxdb/cxdb.sqlite3` stores the
  canonical project-local context, `.timely-playbook/local/.leann/index.json`
  serves retrieval, and `.timely-playbook/local/.orchestrator/state.json` plus
  `.timely-playbook/local/.orchestrator/STATUS.md` remain portable projections
  for humans and compatibility tooling.

## Prerequisites

1. Install the VS Code extension or CLI for the agent provider you plan to use.
2. Configure `.timely-playbook/local/.orchestrator/fullstack-agent.json` so the
   orchestrator can call that provider. The shipped default is `codex`.
3. Install Python 3.11+ with the OpenAI Agents SDK (or plain `requests` for the
   included helper scripts).
4. Install Node `22.22.0+` (22.x), then run
   `npm ci --prefix .timely-playbook/runtime` so the repo-local Context Hub and
   Markdown validation tools are available.
5. Configure `.timely-playbook/config.yaml` using
   `bash .timely-playbook/bin/timely-playbook init-config` to stamp owner
   metadata into trackers.
6. In the Git hosting provider (e.g., GitHub), add the secrets your autofix
   path requires. The shipped default Codex flow uses `OPENAI_API_KEY`. Custom
   providers can use `.github/workflows/autofix.yml` with a
   `TIMELY_AUTOFIX_COMMAND` repository variable instead.

## Repository conventions

- `AGENTS.md` is a generated root stub; the canonical context pack lives at
  `.timely-playbook/local/AGENTS.md`.
- `.timely-playbook/local/.orchestrator/ownership.yaml` prevents agents from
  stepping on each other by mapping paths to personas and escalation owners.
- `.timely-playbook/local/.cxdb/cxdb.sqlite3` maintains the canonical tasks,
  dependencies, CI events, deployment decisions, and local context documents for
  the conductor.
- `.timely-playbook/local/.orchestrator/state.json` remains a portable
  import/export snapshot for seeded repos and manual edits.
- `.timely-playbook/local/.orchestrator/STATUS.md` offers a human-friendly
  dashboard. Refresh it via `python .timely-playbook/bin/orchestrator.py
  update-status` or the root VS Code task dispatcher.
- `.timely-playbook/local/.leann/index.json` is rebuilt from CXDB so agents can
  query local context quickly with `context-search`.
- Root `.vscode/tasks.json` declares one-click automation to run the conductor
  locally via `.timely-playbook/bin/*`.
- Root `.github/workflows/ci.yml` and `.github/workflows/autofix.yml`
  implement validation, packaging, bootstrap smoke checks, and provider-aware
  autofix.
- `.timely-playbook/bin/chub.sh`, `.timely-playbook/bin/chub-mcp.sh`, and
  `.timely-core/tools/chub/timely_registry.py` provide the repo-local Context
  Hub surface for mirrored Timely docs plus public API registry access.

## Agent roster and conductor design

- **Planner:** Breaks a product goal into structured tasks, updating the
  CXDB-backed state store and compatibility export with dependencies and
  sequencing metadata.
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
- The conductor launcher (`python .timely-playbook/bin/orchestrator.py`) acts
  as the mission control layer. It delegates into
  `.timely-core/tools/orchestrator/orchestrator.py`, uses Agents SDK patterns
  to call the configured provider via CLI or MCP, orchestrates git actions (see
  `.timely-core/tools/orchestrator/helpers/git_tools.py`), and records CI
  telemetry (`.timely-core/tools/orchestrator/helpers/ci_tools.py`).

## Implementation phases

1. **Phase A – Single-agent but structured:** Run the planner → implementer →
   tester flow sequentially using the provided script. Record progress in
   `.timely-playbook/local/.cxdb/cxdb.sqlite3`, keep the exported
   `.timely-playbook/local/.orchestrator/state.json` in sync, and open PRs
   manually.
2. **Phase B – Parallel implementers:** Planner assigns owners, conductor
   creates isolated branches/worktrees, and implementers run in parallel
   (background agents in VS Code or via CLI). Reviewer gates merges once CI is
   green.
3. **Phase C – CI failure auto-repair:** `.github/workflows/autofix.yml`
   triggers provider-selected remediation whenever the `CI` workflow fails. The
   shipped template uses Codex by default and can be switched to another
   provider by setting `TIMELY_AUTOFIX_COMMAND`.
4. **Phase D – Deployment agent + verification:** DevOps agent (backed by
   `orchestrator.py deploy`) records staging/prod deployments, triggers smoke
   tests, and initiates rollbacks when necessary.

## VS Code workflow

- Launch Plan mode to convert vague work items into structured steps; either
  hand off tasks through the UI or paste them into `orchestrator.py plan`.
- Use Agent Sessions / Agent HQ to monitor background agents, ensuring each maps
  to a single task/branch defined in
  the CXDB-backed state store and exported `.timely-playbook/local/.orchestrator/state.json`.
- Run the `.vscode` tasks to keep state files in sync without memorizing CLI
  commands.
- When subagents need extra context (docs, diagrams), hand them relative paths
  so their edits respect the guardrail in `AGENTS.md`.

## Guardrails

- Enforce ownership boundaries through
  `.timely-playbook/local/.orchestrator/ownership.yaml` and
  guardrails described in `AGENTS.md`.
- Keep `.github/workflows/ci.yml` green before merging: orchestrator status
  refresh plus the repo-local validation commands. Template maintainers should
  also run `make compile` and the bootstrap smoke path before publishing.
- Require reviewer approvals (human or AI) for infra/auth/db changes; record the
  verdict with `orchestrator.py review`.
- Use branch protections and limit CI/autofix workflows to least privilege (no
  production secrets, principle of least access).
- Record doc validation evidence in
  `.timely-playbook/local/timely-trackers/test-run-journal.md` using
  `timely-playbook append journal`.

## Deliverables & automation hooks

- `.timely-core/tools/orchestrator/` provides sample
  Planner/Implementer/Tester/Reviewer/DevOps agent classes plus helper
  utilities.
- `.timely-core/tools/orchestrator/fullstack.py` adds a reusable FullStack-Agent phase
  pipeline (architecture, backend, frontend, integration, back-translation).
- Root `.github/workflows/ci.yml` standardizes lint + link validation;
  root `.github/workflows/autofix.yml` runs the default Codex repair loop or a
  custom provider command.
- `.timely-playbook/bin/run-markdownlint.sh` and
  `.timely-playbook/bin/check-doc-links.sh` simplify
  validation calls locally and in CI.
- `.timely-core/requirements.txt` enumerates Python dependencies (`requests`
  for CI queries). Extend as your orchestrator grows.
- `.timely-playbook/runtime/package.json` pins `@aisuite/chub` so
  `.timely-playbook/bin/chub.sh` and `.timely-playbook/bin/chub-mcp.sh`
  resolve a stable local Context Hub toolchain.
- Update `.timely-playbook/local/.orchestrator/STATUS.md` after every
  orchestrator run and keep `.timely-playbook/local/.cxdb/`,
  `.timely-playbook/local/.leann/`, and the exported
  `.timely-playbook/local/.orchestrator/state.json` synchronized with
  `context-sync` or `update-status`.

## Context Hub workflow

- Use `bash .timely-playbook/bin/chub.sh validate` to verify the generated
  Timely mirror.
- Use `bash .timely-playbook/bin/chub.sh search <query>` and
  `bash .timely-playbook/bin/chub.sh get <id>`
  when agents need current public API docs or repo-authored Timely guidance from
  the same interface.
- Use `bash .timely-playbook/bin/chub-mcp.sh` to expose the merged registry as
  MCP tools for Codex or other MCP-capable clients.
- Keep the dedicated operator instructions in
  [`Context-Hub-Integration.md`](Context-Hub-Integration.md) synchronized with
  wrapper behavior and CI expectations.

## CXDB and LEANN workflow

- Use `python .timely-playbook/bin/orchestrator.py context-sync` to import the
  portable state snapshot and refresh project-local retrieval data.
- Use `python .timely-playbook/bin/orchestrator.py context-search <query>` when
  agents need project-local context rather than external docs.
- Keep the dedicated operator instructions in
  [`CXDB-LEANN-Integration.md`](CXDB-LEANN-Integration.md) synchronized with
  orchestrator behavior and packaging expectations.

## FullStack-Agent workflow

Run this flow to execute a reusable full-stack build pipeline inspired by arXiv
`2602.03798`:

1. `python .timely-playbook/bin/orchestrator.py fullstack-init-config`
1. `python .timely-playbook/bin/orchestrator.py fullstack-sync`
1.

   ```bash
   python .timely-playbook/bin/orchestrator.py fullstack-bootstrap \
     <project_id> \
     --brief-file <file> \
     --template <template>
   ```

1. `python .timely-playbook/bin/orchestrator.py fullstack-plan <project_id>`
1. Either run phases one-by-one with `fullstack-run`, or execute
   `python .timely-playbook/bin/orchestrator.py fullstack-run-all <project_id>`.
1. Optional strict profile runs can pass `--skill` to use `SKILLS.md` overlays.
1. If running one-by-one, execute: `architecture`, `backend`, `frontend`,
   `integration`, `backtranslation`.
1. `python .timely-playbook/bin/orchestrator.py fullstack-status <project_id>`

Reference: `FullStack-Agent-Integration.md`.

## OpenAI Agents SDK usage

- Treat `python .timely-playbook/bin/orchestrator.py` as a minimal entry point.
  Expand the underlying `.timely-core/tools/orchestrator/orchestrator.py` into
  a full Agents SDK workflow by:
  - Running your selected agent CLI or MCP server exposed to your orchestrator.
  - Defining specialized planner/tester/reviewer tools that call that provider
    via MCP or CLI wrappers
    (`.timely-core/tools/orchestrator/helpers/agent_tools.py`).
  - Using CXDB as deterministic project memory, with exported state files for
    portability between Agents SDK runs and VS Code sessions.

## Next steps

1. Seed each new project via the one-shot flow:
   - `bash`:

     ```bash
     bash ./.timely-playbook/bin/bootstrap-timely-template.sh \
       --template-repo <repo-url> \
       --output <path> \
       --owner "<name>" \
       --email "<email>" \
       --repo "<repo-name>" \
       [--init-git]
     ```

2. Edit `.timely-playbook/local/.orchestrator/ownership.yaml` to match your
   stack.
3. Replace placeholder tasks inside
   `.timely-playbook/local/.orchestrator/state.json`.
   Then run `python .timely-playbook/bin/orchestrator.py context-sync`.
4. Add per-project scripts/tests and wire them into `.github/workflows/ci.yml`.
5. Keep `TimelyPlaybook.md` in sync with lessons learned so the template evolves
   over time.
