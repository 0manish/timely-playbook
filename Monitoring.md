# Monitoring

## Primary signals
- Documentation quality: `./scripts/run-markdownlint.sh` and
  `./scripts/check-doc-links.sh`.
- Tooling health: `python -m unittest discover -s tests -p 'test_*.py'`,
  `bash scripts/chub.sh validate`, and `bash scripts/bootstrap-smoke.sh --smoke`.
- Packaging freshness: successful `make compile` runs and absence of manual edits
  under generated output directories.
- Governance evidence: up-to-date entries in the journal, ledger, and
  traceability matrix after structural changes.

## Alert conditions
- Any default validation command fails on the current branch.
- Package output drifts from source-authored docs, templates, or scripts.
- Context Hub mirror generation fails or returns incomplete results.
- Public-release checks reveal missing license, contribution, or hygiene updates.

## Reporting cadence
- Log significant validation runs in `timely-trackers/test-run-journal.md`.
- Review open documentation or packaging regressions during weekly governance
  syncs.
- Promote repeated failures into `timely-trackers/todo-backlog.md` with an owner
  and due date.
