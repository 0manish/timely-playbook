# .agents/README.md Sync Pattern

Use this template when your seeded project adopts `.agents/agents/*.md` rosters.

## Purpose

Keep the roster discoverable and explicit by maintaining a synchronized index from
agent role files to one clickable path each.

## Required structure

- Add a short heading.
- Keep one row per file in `.agents/agents/`.
- Each row links directly to its file using a relative Markdown path.
- Group by `domain` only when needed; keep the list canonical and ordered.

## Suggested template

```markdown
# Agent roster

Canonical agent role definitions for this repository.

## Runtime roster

- [`autonomous-builder-agent.md`](.agents/agents/autonomous-builder-agent.md)
- [`constraints-and-guardrails-agent.md`](.agents/agents/constraints-and-guardrails-agent.md)
- [`feedback-agent.md`](.agents/agents/feedback-agent.md)
- [`generator-agent.md`](.agents/agents/generator-agent.md)
- [`orchestrator-agent.md`](.agents/agents/orchestrator-agent.md)
- [`skeptical-evaluator-agent.md`](.agents/agents/skeptical-evaluator-agent.md)
- [`spec-doc-sync-agent.md`](.agents/agents/spec-doc-sync-agent.md)
- [`spec-planner-agent.md`](.agents/agents/spec-planner-agent.md)
- [`state-manager-agent.md`](.agents/agents/state-manager-agent.md)
```

## Validation note

When `.agents/agents/` exists, run:

```bash
python3 .timely-playbook/local/agent-harness/tools/check_agent_harness.py
```

The check enforces: every file in `.agents/agents/` is listed in
`.agents/README.md` and no missing/stale links remain.
