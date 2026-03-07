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

- Repository guardrail: [AGENTS.md](../AGENTS.md)
- Contribution guide: [CONTRIBUTING.md](CONTRIBUTING.md)
- Seeded repos may add scoped `AGENTS.md` files under component directories when
  those directories exist.

## Automation and evidence

- **Seeded orchestrator launcher:** `python .timely-playbook/bin/orchestrator.py`
  (implemented from
  [tools/orchestrator/orchestrator.py](tools/orchestrator/orchestrator.py))
- **Seeded Context Hub wrappers:** `bash .timely-playbook/bin/chub.sh` and
  `bash .timely-playbook/bin/chub-mcp.sh`
- **Seeded Context Hub skill installer:**
  `bash .timely-playbook/bin/install-agent-skill.sh`
- **Seeded Context Hub Codex compatibility installer:**
  `bash .timely-playbook/bin/install-codex-skill.sh`
- **Seeded Context Hub agent skill bundle:** `.timely-playbook/local/skills/chub-context-hub/SKILL.md`
- **Context Hub mirror generator source:**
  [tools/chub/timely_registry.py](tools/chub/timely_registry.py)
- **Context Hub mirror metadata:** `.chub/timely-mirror-metadata.json` —
  generated snapshot of the pinned `@aisuite/chub` version, mirrored doc set,
  registry hash, and local build paths for compatibility review
- **Validation path:** `make validate`
- **Full verification path:** `make verify`
- **Status sweep logs:** `run-logs/` — time-stamped summaries written by
  `timely-playbook run-weekly`; generated at runtime and omitted from packaged
  exports unless explicitly included
- **CI workflow:** [../.github/workflows/ci.yml](../.github/workflows/ci.yml)
- **Autofix workflow:** [../.github/workflows/autofix.yml](../.github/workflows/autofix.yml)

## Tracker shortcuts

- Control ledger:
  [../.timely-playbook/local/timely-trackers/agent-control-ledger.md](../.timely-playbook/local/timely-trackers/agent-control-ledger.md)
- Quality journal:
  [../.timely-playbook/local/timely-trackers/test-run-journal.md](../.timely-playbook/local/timely-trackers/test-run-journal.md)
- TODO / OKR backlog:
  [../.timely-playbook/local/timely-trackers/todo-backlog.md](../.timely-playbook/local/timely-trackers/todo-backlog.md)
- Spec traceability:
  [../.timely-playbook/local/timely-trackers/spec-traceability.md](../.timely-playbook/local/timely-trackers/spec-traceability.md)
- Ceremony agendas:
  [../.timely-playbook/local/timely-trackers/ceremony-agendas.md](../.timely-playbook/local/timely-trackers/ceremony-agendas.md)

## When templates leave this repository

- Re-run `make compile` after manual edits so `dist/timely-template` and
  `dist/timely-template.tgz` stay current.
- Verify baseline portability before publishing:

```bash
tar -tzf dist/timely-template.tgz | grep -E '\.timely-core/manifest\.json|\.timely-core/scripts/bootstrap-timely-template\.sh|\.timely-playbook/bin/install-agent-skill\.sh|\.timely-playbook/bin/install-codex-skill\.sh|\.timely-playbook/local/skills/chub-context-hub/SKILL\.md'
```

- Sync the updated bundle into long-lived template locations before cloning the
  playbook into other projects.
