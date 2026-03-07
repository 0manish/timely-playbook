You are running the "{phase_title}" phase for project `{project_id}`.

Grounding source:
- Paper: {paper_title} ({paper_url})
- Project brief file: `{brief_file}`
- Working app directory: `{app_root}`
- Architecture checkpoint: `docs/fullstack-agent/architecture.md`

Execution requirements:
1. Implement frontend features and flows defined in the architecture checkpoint.
2. Integrate the frontend with real backend endpoints and error states.
3. Apply development-oriented testing while coding:
   - Add or update frontend tests (unit/component/e2e depending on stack).
   - Execute available frontend validation commands.
   - Fix rendering, state, or contract bugs before finalizing.
4. Preserve accessibility basics (labels, keyboard navigation, and clear error messaging).
5. Create or update `docs/fullstack-agent/frontend-testing.md` with:
   - Implemented views/components.
   - API integration notes.
   - Commands executed and results.
   - Known UI or UX risks.

Deliverable standard:
- Frontend code, tests, and docs updated in this workspace.
