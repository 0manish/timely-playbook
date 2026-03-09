# Autonomous Agent Tracking Playbook

Early-stage automation needs explicit guardrails so agents can own planning,
execution, and quality gates without losing context. This playbook recommends
the scaffolding to introduce now so future teams can grow into it without
guessing how Timely expects the repo to work.

> Jump to the quick links in [Timely-Governance-Index.md](Timely-Governance-Index.md)
> for the latest governance pointers.

## Core governance artifacts to add

| Artifact | Purpose | Where to keep it | Template |
| --- | --- | --- | --- |
| **Control ledger (`.timely-playbook/local/timely-trackers/agent-control-ledger.md`)** | Single source of truth for which agents own milestones, their operating parameters, and escalation paths. | Under `.timely-playbook/local/timely-trackers/`. | [templates/agent-execution-tracker.md](templates/agent-execution-tracker.md) |
| **Quality journal (`.timely-playbook/local/timely-trackers/test-run-journal.md`)** | Rolling log of scheduled and manual validation runs with links to evidence. | Under `.timely-playbook/local/timely-trackers/`. | [templates/test-run-journal.md](templates/test-run-journal.md) |
| **Spec traceability matrix (`.timely-playbook/local/timely-trackers/spec-traceability.md`)** | Connects governance requirements to implementation and validation. | Under `.timely-playbook/local/timely-trackers/`. | [templates/spec-traceability-matrix.md](templates/spec-traceability-matrix.md) |
| **Repository-level `AGENTS.md`** | Sets the operating rules for work in the template repository. | Repository root. | [templates/AGENTS-template.md](templates/AGENTS-template.md) |
| **Living TODO / OKR board (`.timely-playbook/local/timely-trackers/todo-backlog.md`)** | Captures unassigned TODOs, risks, and quarterly objectives to seed agent pickup lists. | Under `.timely-playbook/local/timely-trackers/`. | [templates/todo-backlog.md](templates/todo-backlog.md) |

Add the above incrementally: start with the repository guardrail and the control
ledger so agents always know who owns what and how to operate, then layer the
journal and traceability matrix once the first milestone enters execution.

## Operational rhythms to capture

1. **Weekly synchronization** — Document a checkpoint cadence for backlog review,
   validation updates, and spec refresh. Use the control ledger and ceremony
   agendas to anchor the routine.
2. **Automated quality gates** — Require every material change to reference a
   journal entry or CI run. Agents should append run IDs and evidence links.
3. **Traceability grooming** — Whenever a guardrail, script, or operator flow
   changes, update the traceability matrix before merging.
4. **Milestone readiness reviews** — Add a checklist that validates: requirements
   locked, verification path documented, package output refreshed.
5. **Post-incident updates** — After regressions or spec gaps, update `AGENTS.md`
   and the backlog so the same class of issue is less likely to recur.

## Suggested directory tree

```text
.
├── AGENTS.md
├── .timely-core/
│   ├── AutomationPlaybook-GettingStarted.md
│   ├── AutonomousAgentTracking.md
│   ├── TimelyPlaybook.md
│   ├── Timely-Governance-Index.md
│   ├── Timely-Governance-Trackers.md
│   ├── Timely-Flowgraph.md
│   └── templates/
│       ├── AGENTS-template.md
│       ├── agent-execution-tracker.md
│       ├── spec-traceability-matrix.md
│       ├── test-run-journal.md
│       └── todo-backlog.md
└── .timely-playbook/local/
    └── timely-trackers/
        ├── agent-control-ledger.md
        ├── ceremony-agendas.md
        ├── spec-traceability.md
        ├── test-run-journal.md
        └── todo-backlog.md
```

Scoped `AGENTS.md` files under component directories are optional and should be
added only when those component directories actually exist in a seeded repo.

## How to roll out

1. **Seed the root guardrail** — Start with repository-wide expectations in
   `AGENTS.md`.
2. **Stand up the trackers** — Instantiate the tracker files and link them from
   the primary guide so operators know where to look.
3. **Embed in workflows** — Update validation and release flows to require:
   - Reference to the control ledger entry assigning the work.
   - New or updated checks recorded in the quality journal.
   - Traceability updates for changed operator expectations.
4. **Automate ingestion** — Long term, expose these artifacts via the Timely CLI
   and Context Hub mirror so agents can query and append entries programmatically.
   In the default Timely architecture, sync them into CXDB and rebuild LEANN so
   project-local retrieval stays aligned with the Markdown sources.

## Additional suggestions for early-stage projects

- **Strategy articulation** — Pair this playbook with an `AutomationStrategy.md`
  or similar note detailing which areas will be agent-owned versus human-led
  over the next two to three milestones.
- **Risk register** — Encourage agents to log automation risks into the backlog
  with severity tags.
- **Telemetry hooks** — Add a lightweight spec for logging automation events
  (agent runs, decisions, escalations) to keep audit coverage high.
- **Onboarding runbooks** — Create short runbooks for setting up new agents and
  validation tooling from a clean clone.
