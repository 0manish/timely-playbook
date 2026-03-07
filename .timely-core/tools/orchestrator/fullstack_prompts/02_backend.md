You are running the "{phase_title}" phase for project `{project_id}`.

Grounding source:
- Paper: {paper_title} ({paper_url})
- Project brief file: `{brief_file}`
- Working app directory: `{app_root}`
- Architecture checkpoint: `docs/fullstack-agent/architecture.md`

Execution requirements:
1. Implement backend features defined in the architecture checkpoint.
2. Keep endpoint behavior, validation, and persistence aligned with the documented contracts.
3. Apply development-oriented testing during coding:
   - Add or update backend tests for happy-path and edge cases.
   - Run the available backend validation command(s).
   - Fix failures before finalizing.
4. Do not break frontend compatibility while changing backend payloads.
5. Create or update `docs/fullstack-agent/backend-testing.md` with:
   - Implemented endpoints and data changes.
   - Commands executed for backend verification.
   - Test outcomes and unresolved risks.

Deliverable standard:
- Commit-ready backend code and tests in this workspace.
- A reproducible backend test log in `docs/fullstack-agent/backend-testing.md`.
