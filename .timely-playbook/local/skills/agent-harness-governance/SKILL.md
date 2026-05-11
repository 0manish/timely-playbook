---
name: agent-harness-governance
description: Maintain generalized agent and skill governance in Timely-seeded repos. Use when changing AGENTS.md, SKILLS.md, repo-local skill bundles, ownership policy, trackers, documentation maps, or recurring doc-gardening and mechanical-governance loops.
---

# Agent Harness Governance

Use this skill when a Timely-seeded repo needs clearer agent-legibility,
skill routing, tracker evidence, or reusable governance workflows.

## Repo assumption

This skill is meant to be installed into an agent skill directory, but executed
from the root of a Timely-seeded repository. In the Timely authoring repo, the
canonical editable governance content is under `.timely-playbook/local/`.

## Core rule

Keep each kind of repo knowledge in its owning surface:

- policy and routing: `AGENTS.md`;
- skill registry and overlay definitions: `SKILLS.md`;
- reusable skill procedures: `.timely-playbook/local/skills/*/SKILL.md`;
- ownership and blast radius: `.timely-playbook/local/.orchestrator/ownership.yaml`;
- traceability and validation evidence:
  `.timely-playbook/local/timely-trackers/*`;
- durable product or project docs: normal project docs, specs, or playbooks;
- generated or runtime state: `.chub/`, `dist/`, `run-logs/`, and similar
  runtime directories unless the active task explicitly targets them.

## Workflow

1. Identify the owner before editing.
   - repo policy belongs in `AGENTS.md`
   - skill discovery belongs in `SKILLS.md`
   - reusable procedure belongs in a skill bundle
   - validation evidence belongs in the test-run journal
   - requirement evidence belongs in the traceability matrix
2. Keep `AGENTS.md` map-like.
   - add links and routing pointers, not full project manuals
3. Keep `SKILLS.md` synchronized.
   - add or remove repo-local skill rows when skill bundles change
   - preserve the machine-readable registry block
4. Convert recurring ambiguity into a durable surface.
   - add a skill step, tracker row, ownership note, template update, or
     mechanical check instead of relying on chat history
5. Record governance changes.
   - update the ledger for new governance processes
   - update the backlog for planned follow-up checks
   - update the test-run journal after validation

## Validation

Run the narrowest applicable commands:

```bash
bash .timely-playbook/bin/run-markdownlint.sh
bash .timely-playbook/bin/check-doc-links.sh
```

For release-path or template packaging changes, use the repo's stronger lane:

```bash
make validate
```

If a command cannot run because a local dependency is missing, record the
dependency gap in the final answer and, when appropriate, in the test-run
journal.

## Install into an agent tool

Install this repo-local skill with the generic installer:

```bash
bash .timely-playbook/bin/install-agent-skill.sh agent-harness-governance
```

Examples:

```bash
# Default agent skills home resolution
bash .timely-playbook/bin/install-agent-skill.sh agent-harness-governance

# Explicit destination for any agent tool
bash .timely-playbook/bin/install-agent-skill.sh agent-harness-governance \
  --dest /path/to/agent/skills
```

Restart your agent tool after installation if it caches skills.

## Boundaries

- Do not use skills for one-off task acceptance criteria.
- Do not put workflow manuals into product specs.
- Do not edit `.timely-core/` unless the task explicitly changes the template
  core or release package.
- Do not treat generated/runtime directories as disposable cleanup targets.
