---
name: project-agent-harness
description: Generic, project-agnostic reusable agent-role definitions and checks that keep AGENTS/SKILLS/trackers aligned in seeded repos.
---

# Project Agent Harness

Use this skill when a Timely-seeded repository is adding or realigning its agent
harness (agent roles, ownership map, tracker evidence, and skill registry
synchronization).

## Scope

- Keep role definitions and responsibilities in `.timely-playbook/local/agent-harness/roles/`.
- Keep validation commands and lightweight harness checks in `.timely-playbook/local/agent-harness/tools/`.
- Keep skill routing in `.timely-playbook/local/SKILLS.md`.
- Keep harness governance in `.timely-playbook/local/AGENTS.md` and related tracker files.

## Workflow

1. Identify required roles and ensure they are represented in policy/skill surfaces:
   - `AGENTS.md` (or local policy map) points to role/spec/docs surfaces.
   - `.timely-playbook/local/SKILLS.md` includes this skill and any new role bundles.
   - Role templates exist in `.timely-playbook/local/agent-harness/roles/`.
2. Add/refresh role behavior in
   `.timely-playbook/local/agent-harness/roles/*.md` before implementation
   changes to minimize drift.
3. Run the harness sanity check before merging governance-facing edits:

```bash
python3 .timely-playbook/local/agent-harness/tools/check_agent_harness.py
python3 .timely-playbook/local/agent-harness/tools/check_agent_harness.py --json
```

4. If the repository uses `.agents/agents/*.md`, sync roster documentation:

```bash
cp .timely-playbook/local/agent-harness/templates/agents-readme-sync.md \
  .agents/README.md
```

Then trim and update entries to match the actual role file names under
`.agents/agents/`.

5. Record check results in:
   - `.timely-playbook/local/timely-trackers/test-run-journal.md` for validation
     evidence.
   - `.timely-playbook/local/timely-trackers/todo-backlog.md` if gaps need follow-up.

## Install into an agent tool

```bash
bash .timely-playbook/bin/install-agent-skill.sh project-agent-harness
```
