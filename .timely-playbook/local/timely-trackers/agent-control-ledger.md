# Agent Control Ledger

> Instance of the agent execution tracker capturing ownership of repository
> guardrails and governance scaffolding.
> For upkeep guidance see [Timely-Governance-Trackers.md](../../../.timely-core/Timely-Governance-Trackers.md).

## Overview
- **Milestone / Epic:** Guardrail rollout and governance bootstrap
- **Last Updated:** 2026-03-09
- **Primary Owner (agent or human):** Smoke Test
- **Escalation Contact:** <smoke@example.com> (self-escalate; log outcome in decision log)

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
| Smoke Test | Primary operator across code and docs | <smoke@example.com> | Runs all cadences; single-owner escalation |
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
| 7 | Align docs, scripts, and CI to the relocated Timely layout and self-install path. | Tasks 1-6 | TimelyPlaybook.md | 2026-03-07 | Done |
| 8 | Generalize execution and autofix surfaces beyond Codex while preserving the default Codex path. | Tasks 1-7 | AGENTS.md | 2026-03-07 | Done |
| 9 | Self-migrate the authoring repository so source, docs, and automation all use the relocated layout. | Tasks 1-8 | TimelyPlaybook.md | 2026-03-07 | Done |
| 10 | Add CXDB and LEANN as the default project-local context plane while preserving packaged template portability. | Tasks 1-9 | CXDB-LEANN-Integration.md | 2026-03-09 | Done |
| 11 | Publish release-ready CLI binaries and a packaged-template bootstrap flow so end users can install Timely without a source checkout. | Tasks 1-10 | TimelyPlaybook.md | 2026-03-09 | Done |
| 12 | Generalize agent and skill governance into a reusable harness skill and registry pattern. | Tasks 1-11 | AGENTS.md; SKILLS.md | 2026-05-11 | Done |

## Quality Gates
- **Required tests:** `make validate`, `make compile`, and
  `bash .timely-playbook/bin/bootstrap-smoke.sh --smoke` for release-path
  changes.
- **Regression cadence:** weekly review during governance sync until all
  trackers are stable.
- **Link to latest run:**
  `.timely-playbook/local/timely-trackers/test-run-journal.md`
  (Run ID: `2026-03-07-authoring-self-migration`)

## Risk & Mitigation Log
| Date | Risk | Impact | Mitigation / Owner | Status |
| --- | --- | --- | --- | --- |
| 2025-10-19 | Owners not assigned for newly created guardrails. | Medium | Assign maintainers in trackers; review during weekly sync. | Closed |
| 2026-03-07 | Docs drifted from the actual root layout and install surface. | High | Align guides, scripts, and CI; add repo-local validation tools and a repeatable verification path. | Closed |
| 2026-03-07 | Codex-specific naming in orchestration and CI could block adoption by other agent providers. | Medium | Add provider abstraction, generic skill installer, and provider-aware autofix hooks while retaining Codex compatibility. | Closed |
| 2026-03-07 | The authoring repo layout diverged from the relocated layout emitted into seeded repos. | High | Self-migrate the source repo, regenerate dispatchers, and verify packaging/bootstrap from the relocated tree. | Closed |
| 2026-03-09 | File-only orchestrator state would not scale well enough for default local retrieval and long-lived agent context. | Medium | Make CXDB the canonical local store, keep `state.json` as the portable export, and rebuild LEANN from project-local sources. | Closed |
| 2026-03-09 | End users would still need a source checkout and local Go toolchain to start a new Timely repo. | Medium | Publish platform CLI archives, checksummed template assets, and a release bootstrap script that installs the binary and seeds the repo directly. | Closed |

## Decision & Change Log
| Date | Decision | Context / Link | Owner |
| --- | --- | --- | --- |
| 2025-10-19 | Adopt repository guardrails and document them in the flowgraph. | Timely-Flowgraph.md | Smoke Test |
| 2025-10-19 | Standardize Markdown link validation via `bash .timely-playbook/bin/check-doc-links.sh`. | .timely-core/scripts/check-doc-links.sh | Smoke Test |
| 2025-10-19 | Wire validation into the CI workflow. | .github/workflows/ci.yml | Smoke Test |
| 2025-10-19 | Assign maintainers to governance trackers. | .timely-playbook/local/timely-trackers/spec-traceability.md | Smoke Test |
| 2025-10-19 | Publish governance ceremony agendas for syncs, gates, and retros. | .timely-playbook/local/timely-trackers/ceremony-agendas.md | Smoke Test |
| 2025-10-19 | Author the getting-started export runbook for reuse. | AutomationPlaybook-GettingStarted.md | Smoke Test |
| 2025-10-19 | Introduce the Timely Playbook CLI for packaging and tracker updates. | .timely-core/cmd/timely-playbook/main.go | Smoke Test |
| 2026-02-14 | Add FullStack-Agent integration commands, prompt phases, and back-translation artifacts. | FullStack-Agent-Integration.md | Smoke Test |
| 2026-03-07 | Adopt a repo-local Context Hub mirror with pinned `@aisuite/chub`, wrapper scripts, and documented MCP startup flow. | Context-Hub-Integration.md | Smoke Test |
| 2026-03-07 | Remove stale downstream-specific docs and examples so the repository remains a general-purpose template. | MasterPlan.md | Smoke Test |
| 2026-03-07 | Make the repository self-consistent and self-installable with repo-local validation tooling, root-based docs, and a repeatable `make verify` path. | TimelyPlaybook.md | Smoke Test |
| 2026-03-07 | Generalize agent execution, skill installation, and autofix defaults so Codex remains the default path without being the only supported path. | AGENTS.md | Smoke Test |
| 2026-03-07 | Record generated Context Hub mirror metadata so `@aisuite/chub` changes can be reviewed for downstream compatibility impact. | Context-Hub-Integration.md | Smoke Test |
| 2026-03-07 | Self-migrate the authoring repository to the relocated `.timely-core/` plus `.timely-playbook/` layout so source and generated repos match. | TimelyPlaybook.md | Smoke Test |
| 2026-03-09 | Adopt CXDB and LEANN as the default project-local context plane, with `.timely-core/` staying read-only and generated project state living under `.timely-playbook/local/`. | CXDB-LEANN-Integration.md | Smoke Test |
| 2026-03-09 | Standardize distribution on GitHub release assets: platform Go binaries, `timely-template.tgz`, checksums, and a bootstrap script that seeds new repos from the published template. | TimelyPlaybook.md | Smoke Test |
| 2026-05-11 | Add generalized agent harness governance so Timely-seeded repos can maintain AGENTS/SKILLS maps, repo-local skill bundles, tracker evidence, and doc-gardening loops without project-specific assumptions. | AGENTS.md; SKILLS.md | Smoke Test |
