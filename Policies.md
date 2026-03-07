# Policies

## Access and change control
- Repository changes must stay within the task’s approved scope and the active
  guardrails in `AGENTS.md`.
- Governance-critical changes require tracker updates and a validation record in
  `timely-trackers/test-run-journal.md`.
- Generated outputs are not edited manually; operators change source docs,
  templates, or scripts and then regenerate artifacts.

## Public release hygiene
- No secrets, credentials, or personal data may be committed.
- License and contribution terms must remain present and current before any
  public release.
- Examples in docs and templates must stay generic so the template is reusable
  across downstream repositories.

## Automation boundaries
- Repo-local tooling is preferred over undeclared global dependencies when
  practical.
- Agents may not widen scope into unrelated directories without explicit task
  approval.
- Validation commands should be deterministic and runnable from the repo root.

## Evidence and traceability
- Structural documentation changes update navigation or tracker artifacts as
  needed.
- Validation outcomes are logged in the journal, and follow-up work is captured
  in the backlog or ledger when required.
- New template expectations should map into `timely-trackers/spec-traceability.md`.
