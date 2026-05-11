# Generic Agent Harness (Project-Agnostic)

This directory provides a reusable, project-agnostic harness for agent role
separation, registry maintenance, and lightweight harness checks.

## Why this exists

Different projects need different technical stacks but share recurring governance
patterns:

- role-based agents for planning, orchestration, and execution,
- skill registry/agent roster synchronization,
- and a small, deterministic set of checks that confirm harness metadata is
  consistent.

## How to use

- Use these role definitions as templates when seeding a new repo.
- Keep implementation surfaces and tracker evidence in your project's canonical
  locations (root `AGENTS.md`, root `.timely-playbook/local/AGENTS.md`, root
  `SKILLS.md`, and `.timely-playbook/local/SKILLS.md`).
- Run `python .timely-playbook/local/agent-harness/tools/check_agent_harness.py` as a
  lightweight harness sanity check in CI when your repo opts into this pattern.

## Included templates

- `roles/generator-agent.md`: implementation generator role that maps to execution
  responsibilities.
- `roles/spec-planner-agent.md`: turns behavior or ambiguity into spec or roadmap
  updates.
- `roles/orchestrator-agent.md`: sequences dependencies and multi-surface
  workstreams.
- `roles/autonomous-builder-agent.md`: executes bounded implementation tasks
  with evidence updates.
- `roles/spec-doc-sync-agent.md`: keeps docs/spec/trackers aligned after
  behavior or validation changes.
- `roles/constraints-and-guardrails-agent.md`: owns ongoing constraints,
  quality limits, and guardrail policy.
- `roles/state-manager-agent.md`: tracks progress, checkpoints, and handoff state
  for deterministic resume.
- `roles/skeptical-evaluator-agent.md`: injects risk checks and constraint
  challenge points.
- `roles/feedback-agent.md`: consolidates feedback and closes loop between
  execution and documentation/tracker surfaces.
- `templates/agents-readme-sync.md`: canonical `.agents/README.md` sync pattern
  for seeded repos that adopt `.agents/agents` rosters.

## Seeding pattern for `.agents/agents` rosters

For projects that choose project-level agent rosters:

- Keep role definitions in `.agents/agents/*.md`.
- Keep `.agents/README.md` as the authoritative roster index and update it whenever
  new roles are added/renamed/removed.
- Use the template at `templates/agents-readme-sync.md`.
- Validate with:

```bash
python3 .timely-playbook/local/agent-harness/tools/check_agent_harness.py
```
