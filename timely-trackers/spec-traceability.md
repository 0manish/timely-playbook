# Spec Traceability Matrix

> Seed matrix to map governance requirements to implementation artifacts.
> Expand as milestones progress.
> See [Timely-Governance-Trackers.md](../Timely-Governance-Trackers.md) for
> maintenance reminders.

- **Maintainer:** {{OWNER_NAME}}
- **Backup:** {{OWNER_NAME}} (self; schedule catch-up block if missed)

## Legend
- **Requirement ID** – Stable identifier from governance or template charter.
- **Spec Source** – Link to the narrative or feature description.
- **API / Contract** – CLI command, script, or workflow representing the requirement.
- **Implementation** – Code path or file that fulfills the requirement.
- **Tests** – Automated or manual coverage that exercises the requirement.
- **Status** – Planned / In Progress / Complete / At Risk.

## Matrix
| Requirement ID | Spec Source | API / Contract | Implementation | Tests | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| GOV-REPO-001 | AGENTS.md | Repository governance process | AGENTS.md | Validation runs recorded in `timely-trackers/test-run-journal.md` | Complete | Root guardrail defines the baseline operator policy stack |
| GOV-TRACKERS-001 | Timely-Governance-Trackers.md | Tracker maintenance workflow | timely-trackers/*.md; templates/*.md | `make validate` plus journal evidence | Complete | Tracker docs now match the root-based repository layout |
| GOV-CLI-001 | TimelyPlaybook.md | `timely-playbook init-config`, `append`, `run-weekly`, `package`, `seed` | cmd/timely-playbook/main.go; cmd/timely-playbook/main_test.go | cmd/timely-playbook `go test ./...`; tests/test_fullstack.py; manual CLI checks logged in the journal | Complete | CLI defaults align with `timely-playbook.yaml` and root tracker paths |
| GOV-VERIFY-001 | TimelyPlaybook.md | `make validate` and `make verify` | Makefile; scripts/run-markdownlint.sh; scripts/check-doc-links.sh; scripts/bootstrap-smoke.sh; .github/workflows/ci.yml | `make verify`; tests/test_playbook_cli.py; fresh seeded install smoke | Complete | Repository validation and installability are expressed as repeatable repo-local commands |
| GOV-FULLSTACK-001 | FullStack-Agent-Integration.md | Full-stack orchestration workflow (`fullstack-*` commands) | tools/orchestrator/fullstack.py; tools/orchestrator/orchestrator.py; tools/orchestrator/fullstack_prompts/*.md | tests/test_fullstack.py; manual CLI smoke checks logged in the journal | Complete | Integrates arXiv `2602.03798` workflow into the template |
| GOV-CHUB-001 | Context-Hub-Integration.md | Repo-local Context Hub workflow (`scripts/chub.sh`, `scripts/chub-mcp.sh`, `scripts/install-codex-skill.sh`) | tools/chub/timely_registry.py; scripts/chub.sh; scripts/chub-mcp.sh; scripts/install-codex-skill.sh; skills/chub-context-hub/SKILL.md; package.json | tests/test_chub.py; tests/test_playbook_cli.py; manual wrapper validation logged in the journal | Complete | Mirrors source-authored Timely markdown into a local `chub` registry, ships a proper Codex skill bundle, and exposes an installer into `~/.codex/skills` |

## Coverage summary
- **Requirements total:** 6
- **Implemented:** 6
- **Missing tests:** 0
- **Deferred / backlog:** Review Context Hub metadata overrides and release
  verification ergonomics after sustained operator usage
