# Timely Governance Index

> Quick map of the governance assets that support the Timely Playbook. Use this
> page to jump between the operating guide, quickstart checklists, automations,
> and trackers.

## Operate the playbook

- **Operations guide:** [TimelyPlaybook.md](TimelyPlaybook.md) — full CLI usage,
  configuration, validation, and packaging expectations.
- **Quickstart checklist:**
  [AutomationPlaybook-GettingStarted.md](AutomationPlaybook-GettingStarted.md) —
  condensed setup and first-week plan.
- **Tracker upkeep:**
  [Timely-Governance-Trackers.md](Timely-Governance-Trackers.md) — shared
  guidance for the ledger, journal, backlog, and related tables.
- **FullStack-Agent integration:**
  [FullStack-Agent-Integration.md](FullStack-Agent-Integration.md) —
  step-by-step full-stack pipeline aligned to arXiv `2602.03798`.
- **Context Hub integration:**
  [Context-Hub-Integration.md](Context-Hub-Integration.md) — repo-local `chub`
  and `chub-mcp` workflow for Timely docs and public API retrieval.

## Visualize the system

- **Governance flowgraph:** [Timely-Flowgraph.md](Timely-Flowgraph.md) —
  Mermaid dependency map linking guardrails, trackers, automation, and rhythms.
- **Autonomous agent playbook:**
  [AutonomousAgentTracking.md](AutonomousAgentTracking.md) — broader context for
  how governance artifacts fit into agent operations.

## Guardrails

- Repository guardrail: [AGENTS.md](AGENTS.md)
- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Seeded repos may add scoped `AGENTS.md` files under component directories when
  those directories exist.

## Automation and evidence

- **Orchestrator CLI:**
  [tools/orchestrator/orchestrator.py](tools/orchestrator/orchestrator.py)
- **Context Hub wrappers:** [scripts/chub.sh](scripts/chub.sh) and
  [scripts/chub-mcp.sh](scripts/chub-mcp.sh)
- **Context Hub skill installer:**
  [scripts/install-codex-skill.sh](scripts/install-codex-skill.sh)
- **Context Hub Codex skill bundle:**
  [skills/chub-context-hub/SKILL.md](skills/chub-context-hub/SKILL.md)
- **Context Hub mirror generator:**
  [tools/chub/timely_registry.py](tools/chub/timely_registry.py)
- **Validation path:** `make validate`
- **Full verification path:** `make verify`
- **Status sweep logs:** `run-logs/` — time-stamped summaries written by
  `timely-playbook run-weekly`; generated at runtime and omitted from packaged
  exports unless explicitly included
- **CI workflow:** [.github/workflows/ci.yml](.github/workflows/ci.yml)
- **Autofix workflow:** [.github/workflows/autofix.yml](.github/workflows/autofix.yml)

## Tracker shortcuts

- Control ledger:
  [timely-trackers/agent-control-ledger.md](timely-trackers/agent-control-ledger.md)
- Quality journal:
  [timely-trackers/test-run-journal.md](timely-trackers/test-run-journal.md)
- TODO / OKR backlog:
  [timely-trackers/todo-backlog.md](timely-trackers/todo-backlog.md)
- Spec traceability:
  [timely-trackers/spec-traceability.md](timely-trackers/spec-traceability.md)
- Ceremony agendas:
  [timely-trackers/ceremony-agendas.md](timely-trackers/ceremony-agendas.md)

## When templates leave this repository

- Re-run `make compile` after manual edits so `dist/timely-template` and
  `dist/timely-template.tgz` stay current.
- Verify baseline portability before publishing:

```bash
tar -tzf dist/timely-template.tgz | grep -E 'AGENTS\.md|SKILLS\.md|scripts/bootstrap-timely-template\.sh|scripts/install-codex-skill\.sh|skills/chub-context-hub/SKILL\.md'
```

- Sync the updated bundle into long-lived template locations before cloning the
  playbook into other projects.
