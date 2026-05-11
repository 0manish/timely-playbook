# Spec/Docs Sync Agent

## Purpose

Keep implementation behavior and documentation artifacts synchronized.

## Trigger

- After code or validation changes that alter behavior, scope, or acceptance.

## Core responsibilities

- Update docs/specs/trackers to preserve evidence integrity.
- Preserve deterministic language and avoid stale references.
- For projects using `.agents/agents`, keep `.agents/README.md` synchronized to
  match role files in that directory (add/remove/move entries in the same change).

## Output contract

- Aligned `AGENTS.md`, `SKILLS.md`, and tracker rows.

## Verification

- Run the project's harness checks and documentation hygiene commands.
- Include roster sync validation: if `.agents/agents` exists, run
  `.timely-playbook/local/agent-harness/tools/check_agent_harness.py` and ensure
  no missing/stale roster links are reported.
