# Spec Traceability Matrix Template

> Ensures every requirement maps to implementation artifacts and automated tests. Update whenever specs or APIs move.

## Legend
- **Requirement ID** – Stable identifier from product or functional spec.
- **Spec Source** – Link to the narrative or feature description.
- **API / Contract** – Endpoint, CLI command, or module representing the requirement.
- **Implementation** – Code path (module/function) that fulfills the requirement.
- **Tests** – Automated coverage that exercises the requirement.
- **Status** – Planned / In Progress / Complete / At Risk.

## Matrix
| Requirement ID | Spec Source | API / Contract | Implementation | Tests | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| <!-- GOV-TEMPLATE-001 --> | <!-- AGENTS.md#template-purpose --> | <!-- `timely-playbook package` --> | <!-- `cmd/timely-playbook/main.go` --> | <!-- `python -m unittest discover -s tests -p 'test_*.py'` --> | <!-- In Progress --> | <!-- Traceability comments --> |

## Coverage summary
- **Requirements total:** <!-- auto/manual count -->
- **Implemented:** <!-- number -->
- **Missing tests:** <!-- number and list -->
- **Deferred / backlog:** <!-- number and reason -->

Review this table during milestone readiness checks and update AGENTS
instructions when new coverage expectations emerge.
