# Spec Traceability Matrix

> Seed matrix to map governance requirements to implementation artifacts.
> Expand as milestones progress.
> See [Timely-Governance-Trackers.md](../../../.timely-core/Timely-Governance-Trackers.md) for
> maintenance reminders.

- **Maintainer:** Smoke Test
- **Backup:** Smoke Test (self; schedule catch-up block if missed)

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
| GOV-REPO-001 | AGENTS.md | Repository governance process | .timely-playbook/local/AGENTS.md | Validation runs recorded in `.timely-playbook/local/timely-trackers/test-run-journal.md` | Complete | The root guardrail stub points at the canonical local governance policy pack |
| GOV-TRACKERS-001 | Timely-Governance-Trackers.md | Tracker maintenance workflow | .timely-playbook/local/timely-trackers/*.md; .timely-core/templates/*.md | `make validate` plus journal evidence | Complete | Tracker docs now match the relocated repository layout used by both the authoring repo and seeded repos |
| GOV-CLI-001 | TimelyPlaybook.md | `timely-playbook init-config`, `append`, `run-weekly`, `package`, `seed` | .timely-core/cmd/timely-playbook/main.go; .timely-core/cmd/timely-playbook/main_test.go | `.timely-core/cmd/timely-playbook` `go test ./...`; `.timely-core/tests/test_fullstack.py`; manual CLI checks logged in the journal | Complete | CLI defaults align with `.timely-playbook/config.yaml`, relocated tracker paths, and generated root launchers |
| GOV-LAYOUT-001 | TimelyPlaybook.md | `timely-playbook migrate-layout`, `refresh-core`, `validate-core` | .timely-core/cmd/timely-playbook/workspace.go; .timely-core/cmd/timely-playbook/main.go; .timely-core/tools/workspace.py | `.timely-core/cmd/timely-playbook` `go test ./...`; `.timely-core/tests/test_playbook_cli.py`; manual migration smoke logged in the journal | Complete | The authoring repo now uses the same `.timely-core/`, `.timely-playbook/local/`, `.timely-playbook/runtime/`, and `.chub/` layout emitted into seeded repos |
| GOV-VERIFY-001 | TimelyPlaybook.md | `bash .timely-playbook/bin/run-markdownlint.sh`, `bash .timely-playbook/bin/check-doc-links.sh`, source-repo `make verify` | Makefile; .timely-core/scripts/run-markdownlint.sh; .timely-core/scripts/check-doc-links.sh; .timely-core/scripts/bootstrap-smoke.sh; .github/workflows/ci.yml | `make verify`; `.timely-core/tests/test_playbook_cli.py`; fresh seeded install smoke | Complete | Repository validation and installability are expressed as repeatable repo-local commands and generated launchers |
| GOV-FULLSTACK-001 | FullStack-Agent-Integration.md | Full-stack orchestration workflow (`fullstack-*` commands) | .timely-core/tools/orchestrator/fullstack.py; .timely-core/tools/orchestrator/orchestrator.py; .timely-core/tools/orchestrator/fullstack_prompts/*.md | `.timely-core/tests/test_fullstack.py`; manual CLI smoke checks logged in the journal | Complete | Integrates arXiv `2602.03798` workflow into the template and supports provider-pluggable phase execution with Codex as the shipped default |
| GOV-AGENT-001 | AGENTS.md | Provider-pluggable agent execution and autofix defaults | .timely-core/tools/orchestrator/fullstack.py; .timely-core/tools/orchestrator/helpers/agent_tools.py; .timely-core/tools/orchestrator/fullstack_defaults.json; .github/workflows/autofix.yml | `.timely-core/tests/test_fullstack.py`; `.timely-core/tests/test_playbook_cli.py`; provider-specific checks logged in the journal when enabled | Complete | Timely exposes a default Codex path plus configurable providers for other agent CLIs and CI repair flows |
| GOV-CHUB-001 | Context-Hub-Integration.md | Repo-local Context Hub workflow (`bash .timely-playbook/bin/chub.sh`, `bash .timely-playbook/bin/chub-mcp.sh`, `bash .timely-playbook/bin/install-agent-skill.sh`) | .timely-core/tools/chub/timely_registry.py; .timely-core/scripts/chub.sh; .timely-core/scripts/chub-mcp.sh; .timely-core/scripts/install-agent-skill.sh; .timely-core/scripts/install-codex-skill.sh; .timely-playbook/local/skills/chub-context-hub/SKILL.md; .timely-playbook/runtime/package.json; generated `.chub/timely-mirror-metadata.json` | `.timely-core/tests/test_chub.py`; `.timely-core/tests/test_playbook_cli.py`; `.timely-core/tests/test_chub_wrappers.py`; manual wrapper validation logged in the journal | Complete | Mirrors source-authored Timely markdown into a local `chub` registry, ships a repo-local skill bundle, exposes a generic installer with Codex compatibility defaults, and records generated mirror metadata so Chub evolution can be reviewed against downstream impact |

## Coverage summary
- **Requirements total:** 8
- **Implemented:** 8
- **Missing tests:** 0
- **Deferred / backlog:** Review Context Hub metadata overrides and release
  verification ergonomics after sustained operator usage
