# Contributing

Thanks for contributing to Timely Playbook.

## License terms

This repository is licensed under the Apache License 2.0. By submitting a
patch, pull request, issue comment with proposed code or docs, or any other
contribution intended for inclusion in this repository, you agree that your
contribution is provided under the same Apache License 2.0 terms, consistent
with Section 5 of the license.

In practice, that means:

- You must have the right to submit the contribution.
- Your contribution is provided under Apache 2.0 unless you explicitly state
  otherwise in writing before submission and that exception is accepted by the
  maintainer.
- If you modify files, keep existing copyright, license, and attribution
  notices intact where they apply.

See [LICENSE](LICENSE) for the full license text.

## Before you contribute

- Review [AGENTS.md](AGENTS.md) for repository guardrails.
- For documentation changes, review
  [Timely-Governance-Index.md](Timely-Governance-Index.md) and the linked
  tracker guidance.
- Do not commit secrets, API keys, personal tokens, `.env` files, or generated
  local caches.

## Development expectations

- Keep changes scoped to the task.
- Update docs when behavior, setup, or workflows change.
- Preserve repository automation semantics unless the change explicitly targets
  them.

## Validation

Run the relevant checks for your change before opening a PR.

Common checks in this repository:

- `./scripts/run-markdownlint.sh`
- `./scripts/check-doc-links.sh`
- `python -m unittest discover -s tests -p 'test_*.py'`

If you update governance or tracker docs, record the validation run in
`timely-trackers/test-run-journal.md`.

## Pull requests

When opening a PR, include:

- A short summary of what changed.
- The commands you ran for validation.
- Any follow-up work or known risks.

If your change affects governance artifacts, note reader impact and any tracker
entries you updated.
