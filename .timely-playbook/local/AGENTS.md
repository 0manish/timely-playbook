# Repository governance guardrail

## Scope

- Governs the root-level governance and operator assets in this repository:
  playbooks, guides, tracker docs, templates, snippets, and supporting diagrams.
- Includes `.timely-playbook/local/timely-trackers/`,
  `.timely-core/templates/`, and `.timely-core/snippets/`.
- Excludes generated output and caches such as `dist/`, `.chub/`, and
  `run-logs/` except when a task explicitly audits packaged or generated artifacts.
- Extends to agent execution behavior when changes are made through
  `.timely-playbook/bin/orchestrator.py` or direct agent CLI runs targeting
  this repository.

## Policy stack for integrated agents

- Governing order for agentic execution is: `AGENTS.md`, then
  `.timely-playbook/local/.orchestrator/ownership.yaml`, then `SKILLS.md`, then
  task-specific asks.
- `SKILLS.md` governs admissible skill behaviors in this repo.
- Any behavior not covered by this stack is disallowed by default in automation
  runs.

## Operator & contact

- **Primary operator:** Smoke Test (`smoke@example.com`)
- **Escalation backup:** self; note escalation in the ledger decision log.

## Decision rights & escalation

- Documentation steward listed in
  `.timely-playbook/local/timely-trackers/agent-control-ledger.md`
  approves structural or taxonomy changes.
- Escalate conflicts (e.g., spec vs. implementation discrepancies) via the
  ledger and capture mitigation tasks in
  `.timely-playbook/local/timely-trackers/todo-backlog.md`.
- Critical process docs (playbooks, governance artifacts) require review
  turnaround within 1 business day; note delays in the ledger entry.

## Writing conventions

- Format Markdown with the workspace standard
  (`.timely-core/.markdownlint.json` when present). Use sentence-case headings
  and active voice.
- Store diagrams as Mermaid inside `.md` files; commit source alongside any
  exported assets if used.
- For cross-doc links, prefer relative paths and keep titles synchronized with
  section headings.

## Testing / validation requirements

- Run link validation (`bash .timely-playbook/bin/check-doc-links.sh`) before
  merging structural updates; log results in
  `.timely-playbook/local/timely-trackers/test-run-journal.md`.
- Manual cadence: re-run `bash .timely-playbook/bin/check-doc-links.sh` plus
  `bash .timely-playbook/bin/run-markdownlint.sh` every Sunday retro and
  capture output in the journal.
- Preview diagrams locally (`Ctrl+Shift+V`) to ensure Mermaid renders; attach
  screenshots or notes in the quality journal for complex graphs.
- When updating templates, verify downstream docs adhere to the new schema and
  document spot checks in the journal.

## Documentation expectations

- Update the spec traceability matrix
  (`.timely-playbook/local/timely-trackers/spec-traceability.md`) whenever
  documentation adds or modifies requirements.
- For new governance processes, add corresponding entries to the control ledger
  and backlog to track adoption.
- Maintain version notes within each tracker (e.g., journal entries, backlog
  items) instead of duplicating them in narrative docs.
- Follow the checklists in
  `.timely-playbook/local/timely-trackers/ceremony-agendas.md` when preparing
  sync or retro notes.
- Keep the navigation hub (`.timely-core/Timely-Governance-Index.md`), tracker
  guidance (`.timely-core/Timely-Governance-Trackers.md`), and flowgraph
  (`.timely-core/Timely-Flowgraph.md`) current as new assets land.

## PR & review checklist

- Reference the ledger assignment and cite which tracker entries were touched.
- Highlight reader impact (who needs to re-read) and include TODO backlog items
  for training or follow-up.
- Ensure templates include clear placeholders and usage notes; remove stale
  sections when superseded.

## Automation hooks & interfaces

- Provide automation-ready formats (tables with consistent headers) so MCP
  agents can append rows deterministically.
- Keep the Mermaid flowgraph (`.timely-core/Timely-Flowgraph.md`) current by
  adding nodes and edges for every new artifact, template, or automation
  routine.
- Trigger `bash .timely-playbook/bin/check-doc-links.sh` via CI
  (`.github/workflows/ci.yml`) or MCP when doc changes land; if the script
  fails, document remediation steps in the backlog and update the ledger status.
- Use `timely-playbook append journal` when recording documentation validation
  runs to avoid manual table edits.
- When `@aisuite/chub` changes or Context Hub behavior shifts, review the
  generated `.chub/timely-mirror-metadata.json` snapshot and log downstream
  compatibility impact in the journal or backlog as needed.
- This template ships a single repository-level guardrail. Seeded repos may add
  scoped `AGENTS.md` files under component directories when those directories
  exist.

## Quality signals to report

- Log documentation review cycles (approvals, open questions) in the quality
  journal with resolution timestamps.
- Tag outstanding doc debt in the backlog with `docs` + priority labels to
  surface in weekly sync.

## Mini change log

- 2025-10-19 – Initial guardrail defining documentation stewardship, validation,
  and automation expectations.
- 2025-10-19 – Standardized Markdown link validation using
  `./scripts/check-doc-links.sh`.
- 2025-10-19 – Added ceremony agendas reference to keep rhythms consistent.
- 2025-10-19 – Personalized operator contacts and manual lint cadence.
- 2026-02-14 – Added FullStack-Agent integration workflow (arXiv `2602.03798`)
  with phased orchestrator commands and reusable prompt pack.
- 2026-02-17 – Added KISS-to-Codex policy stack and skill execution posture.
- 2026-02-17 – Added `SKILLS.md` registry-driven fullstack skill overlays and
  scope guardrails.
- 2026-03-07 – Aligned the guardrail to the repository’s root-based layout and
  repo-local validation tooling.
- 2026-03-07 – Generalized execution surfaces beyond Codex while keeping Codex
  as the default provider path.
- 2026-03-07 – Added generated Context Hub mirror metadata so Chub evolution can
  be tracked against downstream compatibility expectations.
- 2026-03-07 – Relocated seeded repos to `.timely-core/` plus
  `.timely-playbook/` with generated root dispatcher files only.
- 2026-03-07 – Self-migrated the authoring repository to the same relocated
  `.timely-core/` plus `.timely-playbook/` layout used by seeded repos.

## Template purpose

- This repository is the base template for orchestrated, agent-ready projects.
- The shipped provider defaults target Codex, but the orchestrator, CI, and
  skill flows are designed to be provider-pluggable.
  Seed new repos with `.timely-playbook/bin/bootstrap-timely-template.sh`,
  `timely-playbook seed`, or a packaged `dist/timely-template.tgz` export.
- Codify new learnings in this repo first, then re-export so downstream
  projects stay consistent.
- Keep examples generic so seeded repos start from a domain-neutral baseline.

## Orchestrator architecture

- VS Code is the operator console (planning, delegation, review). Automation
  enters seeded repos through `.timely-playbook/bin/orchestrator.py` and
  `.timely-core/tools/orchestrator/`.
- `.timely-playbook/local/.orchestrator/ownership.yaml` defines agent blast
  radii; `.timely-playbook/local/.orchestrator/state.json` tracks tasks, CI
  events, and deployments.
- Root `.vscode/tasks.json` exposes the orchestrator commands (`plan`,
  `start-ready`, `record-ci`, `update-status`, and FullStack commands) so
  agents can run them deterministically.
- Root `.github/workflows/ci.yml` keeps validation and orchestrator status in
  CI; root `.github/workflows/autofix.yml` runs provider-aware repairs on CI
  failures.

## KISS-to-agent incorporation policy (A-E)

- Section A — bounded prompt envelopes: every skilled run must include scope,
  phase assumptions, and explicit non-goals in the instruction prompt.
- Section B — structured progress logging: every skilled run must write run
  metadata and changed-file traces suitable for back-translation review.
- Section C — constrained edit surface: each skilled run must state allowed edit
  areas and forbidden paths, and avoid widening that envelope without approval.
- Section D — bounded iteration: each skilled run remains one explicit phase
  pass; full-stack automation loops remain opt-in and bounded by
  `--continue-on-failure`.
- Section E — compatibility control: only features with deterministic CI value
  and reversible changes are allowed in skilled agent flows.
- Not adopted by default: `RepoOptimizer`, `CreateAndOptimizeAgent`,
  `KISSEvolve`, `GEPA`, `SelfEvolvingMultiAgent`, and auto-optimization loops.
- Required for each skilled run: include success outcome, summary, changed
  files, and rollback hint in final output.
- Fullstack integration must remain command-driven via
  `.timely-core/tools/orchestrator/fullstack.py` and
  `python .timely-playbook/bin/orchestrator.py`; provider-specific wrappers may
  extend the configured `providers` surface, but must not replace baseline
  orchestrator semantics.

## Fullstack skill execution guardrails

- Default fullstack path remains direct agent CLI execution with optional skill
  overlay. The shipped config uses Codex until another provider is configured.
- Any skill run must honor ownership paths and can only widen scope with
  explicit task-level approval.
- Skilled runs must output actionable verification notes and include any risk or
  exception in the same run artifact for follow-up.
- No skilled run may alter governance-critical files unless the task explicitly
  names them and includes a manual approval checkpoint.
- Skilled run output should include success status, summary, changed file
  digest, and rollback hint.

## Repo automation quick links

- `bash .timely-playbook/bin/run-markdownlint.sh` — Markdown lint wrapper using
  the repo-local runtime tooling.
- `bash .timely-playbook/bin/check-doc-links.sh` — link validation wrapper
  using the repo-local runtime tooling; log results in
  `.timely-playbook/local/timely-trackers/test-run-journal.md`.
- `.timely-core/tools/orchestrator/fullstack.py` — FullStack-Agent integration manager
  (config/init, upstream sync, bootstrap, planning, phase execution, status).
- `.timely-core/tools/orchestrator/fullstack_prompts/*.md` — phase prompt templates for
  architecture/backend/frontend/integration/back-translation runs.
- `.timely-core/tools/orchestrator/helpers/*.py` — Git, agent, and CI helper shims for
  Agents SDK integrations.
- `python .timely-playbook/bin/orchestrator.py` — entry point controlling
  Planner/Implementer/Tester/Reviewer/DevOps agents.
- `bash .timely-playbook/bin/chub.sh` and
  `bash .timely-playbook/bin/chub-mcp.sh` — repo-local Context Hub CLI/MCP
  wrappers.
- Default autofix secret: add or update `OPENAI_API_KEY` so the shipped Codex
  autofix path can run. Custom providers should add the secrets required by
  their `TIMELY_AUTOFIX_COMMAND`.
