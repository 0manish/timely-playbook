# Timely Playbook Governance Surface

## Scope

- This repository is the seeded Timely template and execution harness.
- Canonical governance and operational contracts are in:
  - `.timely-playbook/local/AGENTS.md`
  - `.timely-playbook/local/SKILLS.md`
- Root files act as dispatchers into the canonical local files when this repository
  is used as a template seed.

## Document Roles

- `AGENTS.md`: dispatcher and repo-local policy map for template-level governance.
- `.timely-playbook/local/AGENTS.md`: canonical repo-local policy, skill routing,
  tracker expectations, and automation requirements.
- `SKILLS.md`: dispatcher and canonical root view of available skill surfaces.
- `.timely-playbook/local/SKILLS.md`: canonical registry and skill policy.
- `.timely-playbook/local/skills/*/SKILL.md`: reusable workflow procedures.
- `.timely-playbook/local/timely-trackers/*`: validation and governance evidence.
- `.timely-core/` and `.timely-playbook/`: core templates, scripts, and launcher
  mechanics.

## Policy Stack for Agentic Work

- Order for scoped agent execution: root `AGENTS.md` -> `.timely-playbook/local/AGENTS.md`
  -> root `SKILLS.md` -> `.timely-playbook/local/SKILLS.md` -> scoped task docs.
- `SKILLS.md` and `.timely-playbook/local/SKILLS.md` define admissible skill
  behavior.
- Keep edits constrained to the relevant owning surface listed in the active skill
  profile; avoid duplicating one-off guidance in policy files.

## Editing and Routing Rules

- Add or remove repo-local skills in `.timely-playbook/local/SKILLS.md`, then keep
  root `SKILLS.md` aligned with that registry.
- Keep `.timely-core/` read-only except when the task explicitly changes template
  core behavior.
- Treat generated or runtime artifacts (`dist/`, `.chub/`, `run-logs/`, caches)
  as out-of-band unless the task explicitly targets packaging or release surfaces.
- For recurring review feedback, convert it into:
  - tracker entries,
  - skill updates,
  - or reusable task documents,
  instead of leaving only conversational context.
