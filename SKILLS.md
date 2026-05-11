# Timely Playbook Skill Registry

This file dispatches to the canonical local skill registry.

## Canonical Skill Sources

- Root dispatch surface: `.timely-playbook/local/SKILLS.md`
- Repo-local skill bundles:
  - `.timely-playbook/local/skills/chub-context-hub/SKILL.md`
  - `.timely-playbook/local/skills/agent-harness-governance/SKILL.md`

## Fullstack Profiles

- `kiss-fullstack-core`: default fullstack execution profile.
- `kiss-fullstack-relentless`: strict variant for tighter scope and non-disruptive
  integrations.

## Notes

- Use `bash .timely-playbook/bin/install-agent-skill.sh <skill-name>` to install
  repo-local skills before execution.
- Update this registry and local skill bundles together whenever skill behavior is
  added, removed, or materially re-scoped.
- For Timely-local governance and tracker workflows, use the
  `agent-harness-governance` skill path above.
