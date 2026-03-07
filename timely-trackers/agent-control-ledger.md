# Agent Control Ledger

> Instance of the agent execution tracker capturing ownership of repository
> guardrails and governance scaffolding.
> For upkeep guidance see [Timely-Governance-Trackers.md](../Timely-Governance-Trackers.md).

## Overview
- **Milestone / Epic:** Guardrail rollout and governance bootstrap
- **Last Updated:** 2026-03-07
- **Primary Owner (agent or human):** {{OWNER_NAME}}
- **Escalation Contact:** {{OWNER_EMAIL}} (self-escalate; log outcome in decision log)

## Operating Parameters
| Field | Value |
| --- | --- |
| Mission statement | Stand up repository guardrails and trackers so every key operator surface has clear guidance and reporting hooks. |
| Entry criteria | `AGENTS.md` template available; backlog capacity allocated for documentation updates. |
| Exit criteria | Guardrails merged, ledger and journal populated, remaining trackers instantiated with owners. |
| Tooling surface | VS Code, CLI editing, Markdown governance assets, Context Hub wrappers, orchestrator tools. |
| Observability hooks | Quality journal entries for validation runs, backlog tasks for follow-ups, retro feedback loop captured in the flowgraph. |

## Agent Roster
| Agent ID | Role | Contact | Notes |
| --- | --- | --- | --- |
| {{OWNER_NAME}} | Primary operator across code and docs | {{OWNER_EMAIL}} | Runs all cadences; single-owner escalation |
| Agent-Triage | Future optional assistant for backlog grooming | tbd | Placeholder; activate when team expands |

## Work Breakdown
| Sequence | Task | Dependencies | Linked Spec / Issue | Target Date | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | Author the repository guardrail and seed tracker templates. | Template ready | templates/AGENTS-template.md | 2025-10-19 | Done |
| 2 | Log guardrail rollout in the ledger and quality journal. | Task 1 | Timely-Flowgraph.md | 2025-10-19 | Done |
| 3 | Instantiate governance trackers and assign maintenance owners. | Task 1 | AutonomousAgentTracking.md | 2025-10-19 | Done |
| 4 | Integrate FullStack-Agent (`2602.03798`) as a reusable orchestrator workflow for future projects. | Tasks 1-3 | FullStack-Agent-Integration.md | 2026-02-14 | Done |
| 5 | Add Context Hub (`chub`) mirror and MCP workflow for Timely docs and public API retrieval. | Tasks 1-4 | Context-Hub-Integration.md | 2026-03-07 | Done |
| 6 | Remove downstream-specific drift so the template stays general-purpose. | Tasks 1-5 | MasterPlan.md | 2026-03-07 | Done |
| 7 | Align docs, scripts, and CI to the repository’s actual root-based layout and self-install path. | Tasks 1-6 | TimelyPlaybook.md | 2026-03-07 | Done |

## Quality Gates
- **Required tests:** `make validate`, `make compile`, and
  `bash scripts/bootstrap-smoke.sh --smoke` for release-path changes.
- **Regression cadence:** weekly review during governance sync until all
  trackers are stable.
- **Link to latest run:** `timely-trackers/test-run-journal.md`
  (Run ID: `2026-03-07-self-consistency-repair`)

## Risk & Mitigation Log
| Date | Risk | Impact | Mitigation / Owner | Status |
| --- | --- | --- | --- | --- |
| 2025-10-19 | Owners not assigned for newly created guardrails. | Medium | Assign maintainers in trackers; review during weekly sync. | Closed |
| 2026-03-07 | Docs drifted from the actual root layout and install surface. | High | Align guides, scripts, and CI; add repo-local validation tools and a repeatable verification path. | Closed |

## Decision & Change Log
| Date | Decision | Context / Link | Owner |
| --- | --- | --- | --- |
| 2025-10-19 | Adopt repository guardrails and document them in the flowgraph. | Timely-Flowgraph.md | {{OWNER_NAME}} |
| 2025-10-19 | Standardize Markdown link validation via `scripts/check-doc-links.sh`. | scripts/check-doc-links.sh | {{OWNER_NAME}} |
| 2025-10-19 | Wire validation into the CI workflow. | .github/workflows/ci.yml | {{OWNER_NAME}} |
| 2025-10-19 | Assign maintainers to governance trackers. | timely-trackers/spec-traceability.md | {{OWNER_NAME}} |
| 2025-10-19 | Publish governance ceremony agendas for syncs, gates, and retros. | timely-trackers/ceremony-agendas.md | {{OWNER_NAME}} |
| 2025-10-19 | Author the getting-started export runbook for reuse. | AutomationPlaybook-GettingStarted.md | {{OWNER_NAME}} |
| 2025-10-19 | Introduce the Timely Playbook CLI for packaging and tracker updates. | cmd/timely-playbook/main.go | {{OWNER_NAME}} |
| 2026-02-14 | Add FullStack-Agent integration commands, prompt phases, and back-translation artifacts. | FullStack-Agent-Integration.md | {{OWNER_NAME}} |
| 2026-03-07 | Adopt a repo-local Context Hub mirror with pinned `@aisuite/chub`, wrapper scripts, and documented MCP startup flow. | Context-Hub-Integration.md | {{OWNER_NAME}} |
| 2026-03-07 | Remove stale downstream-specific docs and examples so the repository remains a general-purpose template. | MasterPlan.md | {{OWNER_NAME}} |
| 2026-03-07 | Make the repository self-consistent and self-installable with repo-local validation tooling, root-based docs, and a repeatable `make verify` path. | TimelyPlaybook.md | {{OWNER_NAME}} |
