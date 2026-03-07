# Master Plan

Timely Playbook is the base template for teams that want a reusable governance,
automation, and packaging baseline for agent-assisted repositories. This plan
keeps the template focused on general-purpose workflows that can be exported
into many downstream projects.

## Workstream 1: governance baseline
- **Scope**: Maintain clear operator guidance, tracker hygiene, traceability,
  and review expectations across the repository.
- **Objectives**:
  - Keep the repo domain-neutral so seeded projects start from a clean baseline.
  - Ensure structural documentation changes are reflected in trackers and
    validation logs.
  - Preserve clear ownership and escalation paths for agent-driven work.
- **Key deliverables**:
  - Repository and directory guardrails in `AGENTS.md`.
  - Governance trackers under `timely-trackers/`.
  - Navigation artifacts such as `Timely-Governance-Index.md` and
    `Timely-Flowgraph.md`.

## Workstream 2: operator automation
- **Scope**: Provide a practical local toolchain for operators and coding agents.
- **Objectives**:
  - Keep the Timely CLI, orchestrator flows, and Context Hub wrappers easy to
    run from a fresh clone.
  - Make validation commands predictable and suitable for CI reuse.
  - Support bounded agent workflows without coupling the template to a single
    downstream product.
- **Key deliverables**:
  - `timely-playbook` CLI for packaging, seeding, and tracker updates.
  - Orchestrator commands and FullStack prompt pack under `tools/orchestrator/`.
  - Repo-local `chub` mirror and MCP startup wrappers.

## Workstream 3: packaging and reuse
- **Scope**: Keep the repository exportable as a clean template for new projects.
- **Objectives**:
  - Ensure `dist/timely-template` is reproducible from source-authored files.
  - Prevent generated artifacts and local state from becoming the source of
    truth.
  - Keep public-release hygiene, licensing, and bootstrap instructions current.
- **Key deliverables**:
  - `make compile` packaging path.
  - Bootstrap and smoke-test scripts.
  - Public-release docs covering licensing, contribution terms, and secret
    hygiene.

## High-level timeline
| Phase | Duration | Focus | Key outcomes |
| --- | --- | --- | --- |
| Phase 0 | Week 0 | Scope alignment | Confirm template purpose, remove downstream-specific drift, refresh governance docs |
| Phase 1 | Weeks 1-2 | Operator workflows | Stabilize CLI docs, tracker upkeep, and bootstrap guidance |
| Phase 2 | Weeks 3-4 | Validation baseline | Keep docs checks, unit tests, Context Hub validation, and smoke runs green |
| Phase 3 | Weeks 5-6 | Packaging & release | Rebuild export artifacts, verify seeded repo behavior, and prepare public release notes |
| Phase 4 | Ongoing | Adoption feedback | Fold downstream lessons back into the template without narrowing its scope |

## Cross-cutting requirements
- Source-authored docs and templates remain the only editable source of truth.
  Generated outputs such as `dist/` and `.chub/` must be regenerated, not hand-edited.
- Public-release hygiene is mandatory: no secrets, no personal data, and clear
  license and contribution terms.
- Every structural documentation change must maintain navigation, tracker
  integrity, and validation evidence.
- Tooling should be pinned and repo-local where practical so operators and
  coding agents see the same behavior.

## Testing plan
- **Documentation validation**: Run `./scripts/run-markdownlint.sh` and
  `./scripts/check-doc-links.sh` for documentation and governance changes.
- **Python/unit coverage**: Run `python -m unittest discover -s tests -p 'test_*.py'`
  whenever CLI helpers, mirror generation, or orchestration utilities change.
- **Context Hub validation**: Run `bash scripts/chub.sh validate` and a small
  search/get smoke pass when mirror scope or metadata changes.
- **Bootstrap packaging**: Run `bash scripts/bootstrap-smoke.sh --smoke` and
  `make compile` before public template releases.

## Immediate next steps
1. Keep planning and user-facing docs aligned to Timely’s template purpose.
2. Expand automated coverage only where it improves determinism for seeded repos.
3. Review Context Hub metadata quality after real operator usage and tighten
   overrides where search ranking is weak.
4. Rebuild package artifacts after source changes so exported templates stay in
   sync with the repository root.
