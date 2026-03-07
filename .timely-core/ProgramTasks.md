# Program Task Breakdown & Timeline

This document lists the actionable work needed to keep Timely Playbook usable as
a general-purpose repository template. Tasks are grouped by phase with owners,
dependencies, and the artifacts expected from each step.

## Legend
- **Owner**: Primary accountable role or team.
- **Dependencies**: Upstream tasks or preconditions.
- **Artifacts**: Docs, scripts, tests, or packaged outputs produced by the task.

## Testing plan
- Keep documentation, unit, and packaging validation aligned with each phase.
- Record structural validation runs in
  `.timely-playbook/local/timely-trackers/test-run-journal.md`.
- Update `.timely-playbook/local/timely-trackers/spec-traceability.md` when
  template expectations change.
- Prefer validations that are deterministic from a clean clone.

## Phase 0 — scope alignment
| Task | Owner | Dependencies | Artifacts |
| --- | --- | --- | --- |
| Reconfirm Timely’s role as a domain-neutral template | Repository steward | None | Updated planning docs and scope notes |
| Audit repository content for downstream-specific drift | Repository steward | None | Removal list and cleanup notes |
| Refresh governance docs after scope changes | Repository steward | Scope audit | Updated ledger, journal, traceability entries |
| Verify public-release hygiene | Repository steward | Licensing in place | Secret scrub notes, public repo checklist |

## Phase 1 — operator workflows
| Task | Owner | Dependencies | Artifacts |
| --- | --- | --- | --- |
| Keep `TimelyPlaybook.md` and `HOWTO.md` aligned with the actual bootstrap flow | Docs owner | Phase 0 complete | Updated operator guides |
| Maintain repo-local Context Hub wrappers and mirror generation docs | Docs owner, tooling owner | Node toolchain pinned | Updated `Context-Hub-Integration.md`, metadata overrides |
| Keep VS Code tasks and CLI commands discoverable | Tooling owner | Operator workflow review | Updated `.vscode/tasks.json`, guide references |
| Ensure tracker append flows remain documented | Docs owner | CLI available | Updated user guide and journal references |

## Phase 2 — validation baseline
| Task | Owner | Dependencies | Artifacts |
| --- | --- | --- | --- |
| Keep `python -m unittest discover -s .timely-core/tests -p 'test_*.py'` green | Tooling owner | Phase 1 docs aligned | Passing unit tests |
| Keep `bash .timely-playbook/bin/run-markdownlint.sh` and `bash .timely-playbook/bin/check-doc-links.sh` green | Docs owner | Phase 1 docs aligned | Passing docs checks |
| Validate the Timely Context Hub mirror from source-authored markdown | Tooling owner | Metadata overrides current | Passing `bash .timely-playbook/bin/chub.sh validate` run |
| Preserve bootstrap smoke coverage for the packaged template | Tooling owner | Packaging scripts current | Passing `bash .timely-playbook/bin/bootstrap-smoke.sh --smoke` run |

## Phase 3 — packaging and release
| Task | Owner | Dependencies | Artifacts |
| --- | --- | --- | --- |
| Rebuild package artifacts from source docs and scripts | Release owner | Phase 2 validations pass | Fresh `dist/timely-template` and archive |
| Verify seeded repo behavior from packaged and local sources | Release owner | Fresh package artifacts | Smoke notes and seed verification |
| Review contribution, license, and public-release docs before publish | Repository steward | Packaging complete | Final release checklist |
| Publish release notes describing template changes and migration impact | Repository steward | Prior tasks complete | Release summary and follow-up items |

## Phase 4 — adoption feedback
| Task | Owner | Dependencies | Artifacts |
| --- | --- | --- | --- |
| Collect downstream friction points from seeded repos | Repository steward | Released template | Backlog items and tracker notes |
| Improve metadata and search quality based on operator usage | Tooling owner | Context Hub usage data | Refined override file and mirror docs |
| Tighten guardrails where recurring mistakes appear | Repository steward | Backlog review | Updated `AGENTS.md` guidance |
| Keep template examples neutral and reusable | Repository steward | Periodic content audit | Refreshed examples across templates and guides |

## Testing TODO
- [ ] Add a CI-friendly smoke test that exercises `timely-playbook append journal`
  against a temporary tracker file.
- [ ] Add automated verification that `make compile` produces a package without
  generated-state drift.
- [ ] Expand unit coverage around template packaging exclusions and mirror source
  classification.
- [ ] Add a lightweight release checklist verifier for licensing, contribution,
  and secret-scrub expectations.

## Rolling TODO list
- [ ] Review examples in templates and guides quarterly for downstream-specific drift.
- [ ] Keep `Monitoring.md` aligned with the current validation and release signals.
- [ ] Revisit Context Hub metadata overrides after sustained operator usage.
- [ ] Add stronger packaging checks if public release frequency increases.
- [ ] Document migration notes whenever seeded repo expectations change.

Updates to this document should accompany any major shift in template scope,
timing, or ownership.
