# FullStack-Agent Integration Playbook

This playbook incorporates the method from arXiv `2602.03798` into the Timely orchestrator so future projects can run a repeatable full-stack agent pipeline.

## Source Alignment
- Paper: [FullStack-Agent: Enhancing Agentic Full-Stack Web Coding via Development-Oriented Testing and Repository Back-Translation](https://arxiv.org/abs/2602.03798)
- Upstream code: `mnluzimu/FullStack-Agent`, `mnluzimu/FullStack-Dev`, `mnluzimu/FullStack-Bench`, `mnluzimu/FullStack-Learn`
- Pinned refs are tracked in
  `.timely-core/tools/orchestrator/fullstack_defaults.json` and copied into
  `.timely-playbook/local/.orchestrator/fullstack-agent.json`.
- The shipped defaults now resolve an orchestration stack first and an
  execution provider second. `codex_symphony` is the default shipped stack, and
  `.timely-playbook/local/.orchestrator/fullstack-agent.json` supports both a
  `stacks` registry and a `providers` registry so projects can switch to other
  agent CLIs or other orchestration patterns with `default_stack`,
  `fullstack-run --stack`, or `fullstack-run --provider`.

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
  - `fullstack-run --stack`
  - `fullstack-run --provider`
  - `fullstack-run --skill`
  - `fullstack-reconcile`
  - `autofix-config`
  - `autofix-dispatch`
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
   the CXDB-backed orchestrator state store, keeping
   `.timely-playbook/local/.orchestrator/state.json` as the portable export.
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
# Optional: override the default orchestration stack for one run
python .timely-playbook/bin/orchestrator.py fullstack-run acme-portal architecture --stack codex_cli
# Optional: override the default provider for one run
python .timely-playbook/bin/orchestrator.py fullstack-run acme-portal architecture --provider other-agent
# Reconcile a Symphony-managed phase after the external run completes
python .timely-playbook/bin/orchestrator.py fullstack-reconcile acme-portal architecture done \
  --summary "Symphony run completed successfully" \
  --external-run-id sym-123
# Option B: run all ready phases sequentially
python .timely-playbook/bin/orchestrator.py fullstack-run-all acme-portal
python .timely-playbook/bin/orchestrator.py fullstack-run-all acme-portal --stack codex_cli --provider other-agent --skill kiss-fullstack-core
python .timely-playbook/bin/orchestrator.py fullstack-status acme-portal
```

## Stack and adapter model
- `default_stack` selects the repo-wide orchestration posture.
- `providers` define how Timely invokes an execution engine.
- `adapters` define how Timely hands work to an orchestration layer such as
  Symphony.
- `stacks` bind one provider plus one adapter into a reusable profile.
- `codex_symphony` is the shipped default. When
  `adapters.symphony.submit_command` is configured, Timely submits a
  `symphony-payload.json` handoff packet to that command. When the command is
  left empty, Timely falls back to direct provider execution for compatibility.

Example override surface in `.timely-playbook/local/.orchestrator/fullstack-agent.json`:

```json
{
  "default_stack": "claude_symphony_example",
  "adapters": {
    "symphony": {
      "submit_command": [
        "bash",
        ".timely-playbook/bin/symphony-submit.sh",
        "--payload",
        "{payload_file}",
        "--prompt",
        "{prompt_file}",
        "--run-dir",
        "{run_dir}"
      ]
    }
  },
  "providers": {
    "claude_code_example": {
      "exec_command": [
        "bash",
        "-lc",
        "claude-code --project \"{workdir}\""
      ],
      "stdin_prompt": true
    }
  }
}
```

The template ships `.timely-playbook/bin/symphony-submit.sh` as a concrete
starter wrapper. Set `TIMELY_SYMPHONY_SUBMIT` to your real submit command, then
copy `adapters.symphony.sample_submit_command` into `submit_command` to turn on
external handoff without inventing a wrapper shape from scratch.

The provider examples now ship concrete wrappers too:
- `providers.claude_code_example.sample_exec_command` pairs with
  `.timely-playbook/bin/claude-code-example.sh` and `TIMELY_CLAUDE_CODE_COMMAND`
- `providers.open_source_agent_example.sample_exec_command` pairs with
  `.timely-playbook/bin/open-source-agent-example.sh` and
  `TIMELY_OPEN_SOURCE_AGENT_COMMAND`

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
- Prefer changing `default_stack` for project-wide posture and reserving
  `--provider` for narrower execution overrides.
- The shipped defaults include `claude_symphony_example` and
  `open_source_symphony_example` as documented starting points; customize their
  provider commands before using them in a live repo.
- Keep `.timely-playbook/local/.cxdb/` and `.timely-playbook/local/.leann/`
  project-local; regenerate them with `context-sync` instead of copying them
  between repos.
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
| E – compatibility control | Integration uses the existing orchestrator entry points and state/task graph only; no replacement of planner/implementer/reviewer/devops semantics. Stacks are declarative profiles layered over provider selection, and skills remain additive overlays and optional command flags. | Approved | Reject adding any unvetted optimizer/auto-evolution agents as part of this path. |
