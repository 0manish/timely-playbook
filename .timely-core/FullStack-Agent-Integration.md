# FullStack-Agent Integration Playbook

This playbook incorporates the method from arXiv `2602.03798` into the Timely orchestrator so future projects can run a repeatable full-stack agent pipeline.

## Source Alignment
- Paper: [FullStack-Agent: Enhancing Agentic Full-Stack Web Coding via Development-Oriented Testing and Repository Back-Translation](https://arxiv.org/abs/2602.03798)
- Upstream code: `mnluzimu/FullStack-Agent`, `mnluzimu/FullStack-Dev`, `mnluzimu/FullStack-Bench`, `mnluzimu/FullStack-Learn`
- Pinned refs are tracked in
  `.timely-core/tools/orchestrator/fullstack_defaults.json` and copied into
  `.timely-playbook/local/.orchestrator/fullstack-agent.json`.
- The shipped defaults execute phases with Codex, but
  `.timely-playbook/local/.orchestrator/fullstack-agent.json` now supports a
  provider registry so other agent CLIs can be selected with
  `default_provider` or `fullstack-run --provider`.

## What Was Added
- New orchestration module: `.timely-core/tools/orchestrator/fullstack.py`
- New skill overlay registry: `.timely-playbook/local/SKILLS.md` and
  `.timely-core/tools/orchestrator/helpers/kiss_bridge.py`
- New CLI commands exposed through `python .timely-playbook/bin/orchestrator.py`:
  - `fullstack-init-config`
  - `fullstack-sync`
  - `fullstack-bootstrap`
  - `fullstack-plan`
  - `fullstack-run`
  - `fullstack-run --provider`
  - `fullstack-run --skill`
  - `fullstack-status`
- Prompt pack for phased execution:
  - `.timely-core/tools/orchestrator/fullstack_prompts/01_architecture.md`
  - `.timely-core/tools/orchestrator/fullstack_prompts/02_backend.md`
  - `.timely-core/tools/orchestrator/fullstack_prompts/03_frontend.md`
  - `.timely-core/tools/orchestrator/fullstack_prompts/04_integration.md`
  - `.timely-core/tools/orchestrator/fullstack_prompts/05_backtranslation.md`

## Step-by-Step Operating Plan
1. Initialize config and pin upstream repositories.
2. Bootstrap a project from a FullStack-Dev template.
3. Generate a phase plan and sync it into
   `.timely-playbook/local/.orchestrator/state.json`.
4. Run phases sequentially with the configured provider, capturing artifacts
   after each phase.
5. Reuse generated back-translation traces in future project starts.

## Quick Start Commands
```bash
python .timely-playbook/bin/orchestrator.py fullstack-init-config
python .timely-playbook/bin/orchestrator.py fullstack-sync
python .timely-playbook/bin/orchestrator.py fullstack-bootstrap acme-portal \
  --brief-file /absolute/path/to/brief.md \
  --template nextjs-nestjs-postresql
python .timely-playbook/bin/orchestrator.py fullstack-plan acme-portal
# Option A: run phases one by one
python .timely-playbook/bin/orchestrator.py fullstack-run acme-portal architecture
python .timely-playbook/bin/orchestrator.py fullstack-run acme-portal backend
python .timely-playbook/bin/orchestrator.py fullstack-run acme-portal frontend
python .timely-playbook/bin/orchestrator.py fullstack-run acme-portal integration
python .timely-playbook/bin/orchestrator.py fullstack-run acme-portal backtranslation
# Optional: run with an explicit skill envelope
python .timely-playbook/bin/orchestrator.py fullstack-run acme-portal architecture --skill kiss-fullstack-core
# Optional: override the default provider for one run
python .timely-playbook/bin/orchestrator.py fullstack-run acme-portal architecture --provider other-agent
# Option B: run all ready phases sequentially
python .timely-playbook/bin/orchestrator.py fullstack-run-all acme-portal
python .timely-playbook/bin/orchestrator.py fullstack-run-all acme-portal --provider other-agent --skill kiss-fullstack-core
python .timely-playbook/bin/orchestrator.py fullstack-status acme-portal
```

## Template Choices
- Coupled template:
  - `nextjs-nestjs-postresql`
- Decoupled template pairs:
  - `nextjs__nestjs`
  - `nextjs__django`
  - `vue__nestjs`
  - `vue__django`

## Back-Translation Artifacts
Each phase run writes artifacts under:
- `fullstack-projects/<project-id>/.timely/runs/<timestamp>-<phase>/`
- `fullstack-projects/<project-id>/artifacts/backtranslation/trajectory.jsonl`

These artifacts capture prompt input, provider command metadata, validation
results, and changed-file traces to make future replay and adaptation
deterministic.

## Notes for Future Projects
- Keep `.timely-playbook/local/.orchestrator/fullstack-agent.json` in version
  control for reproducibility.
- Update pinned refs only with an explicit migration note.
- Add or tighten `validation_commands` per phase to match each project stack.
- Avoid copying upstream `.env` example secrets; always inject credentials through local/CI secret stores.
- Add `SKILLS.md`-governed overlays with `--skill` when you want strict prompt and
  scope constraints.

## A-E compatibility matrix (final manual approval)

The table below maps each KISS section to how it is enforced in this
Timely Playbook fullstack path and whether it is approved for this template.

| Section | FullStack integration behavior | Compatibility result | Manual review note |
| --- | --- | --- | --- |
| A – bounded prompt envelope | `--skill` loads `SKILLS.md` overlays and prepends phase-scoped guidance (`kiss_bridge.compose_skill_overlay`) to phase prompts in `run_phase`. `run_phase` writes the rendered prompt to `.timely/runs/<stamp>-<phase>/prompt.md`. | Approved | Keep defaults for all fullstack runs; allow custom overlays only when task scope is explicit. |
| B – structured progress logging | Each phase run stores `prompt.md`, `agent-stdout.log`, `agent-stderr.log`, `validation-*.log`, `changed-files.json`, optional `skill-overlay.md`, and optional `skill-policy.json` plus `artifacts/backtranslation/trajectory.jsonl` append entries. Codex runs also keep legacy `codex-*` aliases for compatibility. | Approved | Require one row per run in ledger/quality follow-up if any policy warning appears. |
| C – constrained editing surface | `SKILLS.md` declares `allowed_paths`, `forbidden_paths`, and `max_changed_files`; `run_phase` performs scope checks via `kiss_bridge.check_scope` and records violations. | Approved with controls | Only use strict profiles (`kiss-fullstack-relentless`) for high-risk edits; non-conforming edits require explicit task-level expansion approval. |
| D – bounded implementation cycles | `fullstack-run` executes exactly one phase invocation; `fullstack-run-all` iterates through ready/in-progress phases with optional `--continue-on-failure`. There is no autonomous optimizer loop in the base path. | Approved | Keep `--continue-on-failure` opt-in and only set intentionally. |
| E – compatibility control | Integration uses the existing orchestrator entry points and state/task graph only; no replacement of planner/implementer/reviewer/devops semantics. Skills are additive overlays and optional command flags. | Approved | Reject adding any unvetted optimizer/auto-evolution agents as part of this path. |
