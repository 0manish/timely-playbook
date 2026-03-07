You are running the "{phase_title}" phase for project `{project_id}`.

Grounding source:
- Paper: {paper_title} ({paper_url})
- Project brief file: `{brief_file}`
- Working app directory: `{app_root}`
- Prior checkpoints:
  - `docs/fullstack-agent/architecture.md`
  - `docs/fullstack-agent/backend-testing.md`
  - `docs/fullstack-agent/frontend-testing.md`

Execution requirements:
1. Resolve any contract mismatches between backend and frontend.
2. Verify end-to-end workflows including persistence behavior.
3. Add or update integration tests where possible.
4. Execute project validation commands and ensure they pass.
5. Create or update `docs/fullstack-agent/integration-report.md` with:
   - End-to-end scenarios tested.
   - Integration and migration notes.
   - Validation commands and outcomes.
   - Rollback strategy for risky changes.

Deliverable standard:
- Integrated full-stack behavior that is usable for handoff.
