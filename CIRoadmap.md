# CI Roadmap

## Objectives
- Keep Timely’s default validation commands runnable in CI from a clean clone.
- Ensure template packaging and bootstrap paths are exercised before public releases.
- Preserve fast feedback for documentation and tooling regressions.

## Pipeline milestones
1. **Foundation**
   - Run docs validation on every relevant change.
   - Run `python -m unittest discover -s tests -p 'test_*.py'` for tooling code.
   - Keep Node and Go versions pinned where the repository depends on them.
2. **Template validation**
   - Add or maintain CI coverage for `bash scripts/chub.sh validate`.
   - Run bootstrap smoke validation for packaged or seeded template flows.
   - Detect package drift by rebuilding artifacts in automation.
3. **Release readiness**
   - Gate public releases on license, contribution, and secret-scrub checks.
   - Preserve reproducible `make compile` output.
   - Publish validation evidence suitable for operator review.
4. **Ongoing hardening**
   - Tighten checks when recurring operator failures show up in the journal or backlog.
   - Expand automation only where it improves determinism for downstream repos.

## Cross-cutting requirements
- Prefer repo-local commands so CI and local runs match.
- Keep workflow steps scoped to the template’s actual contents.
- Avoid domain-specific assumptions in test fixtures, examples, or packaged docs.
- Record major validation changes in the planning and governance docs.

## Action items
- [ ] Keep docs, unit, Context Hub, and bootstrap checks wired into CI.
- [ ] Add a packaging drift check if `make compile` becomes part of the regular release path.
- [ ] Review CI signals quarterly against the issues surfaced in the tracker journal.
