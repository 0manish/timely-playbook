# TODO / OKR Backlog

> Shared backlog for governance scaffolding tasks and follow-ups.
> Refer to [Timely-Governance-Trackers.md](../../../.timely-core/Timely-Governance-Trackers.md)
> for backlog upkeep guidance.

- **Maintainer:** Smoke Test
- **Backup:** Smoke Test (self; schedule catch-up if unavailable)

## Quarterly Objectives
| Objective | Key Results | Owner | Status |
| --- | --- | --- | --- |
| Q4: Establish autonomous governance scaffolding | KR1: Repository guardrail lives; KR2: trackers staffed with owners; KR3: automation hooks documented; KR4: verification path remains runnable from a clean seed | Smoke Test | In Progress |

## Near-term TODOs
| Priority | Item | Context / Link | Owner | Due Date | Status |
| --- | --- | --- | --- | --- | --- |
| High | Assign permanent owners to guardrail maintenance and update the ledger | .timely-playbook/local/timely-trackers/agent-control-ledger.md | Smoke Test | 2025-10-19 | Done |
| High | Keep Markdown link checking wired into governance validation | .timely-playbook/local/timely-trackers/test-run-journal.md | Smoke Test | 2025-10-19 | Done |
| Medium | Attach CI artifact links to future journal entries where helpful | .timely-playbook/local/timely-trackers/test-run-journal.md | Smoke Test | 2025-10-20 | Todo |
| High | Re-review `make verify` after the next release-path change to ensure the seed/install flow still matches docs | TimelyPlaybook.md | Smoke Test | 2026-03-21 | Todo |
| Medium | Review Context Hub mirror search quality after operator usage and extend `.timely-core/tools/chub/metadata_overrides.json` if ranking is weak | Context-Hub-Integration.md | Smoke Test | 2026-03-21 | Todo |
| Medium | Review CXDB / LEANN retrieval quality after operator usage and tighten indexing sources or ranking if results are weak | CXDB-LEANN-Integration.md | Smoke Test | 2026-03-23 | Todo |
| Medium | Review `.chub/timely-mirror-metadata.json` after each `@aisuite/chub` version change and log any downstream compatibility implications | Context-Hub-Integration.md | Smoke Test | 2026-03-21 | Todo |
| Medium | Add a lightweight pre-release scan that flags downstream-specific examples before packaging | MasterPlan.md | Smoke Test | 2026-03-21 | Todo |
| Medium | Add one fully documented non-Codex provider example and record the operator steps for `fullstack-run --provider` plus `TIMELY_AUTOFIX_COMMAND` | TimelyPlaybook.md | Smoke Test | 2026-03-28 | Todo |

## Backlog Candidates
- Roll out a CI job to validate Mermaid rendering on pull requests.
- Add a release note helper for template exports.

## Blockers & Requests
- None; maintain single-operator escalation notes in the ledger decision log.
