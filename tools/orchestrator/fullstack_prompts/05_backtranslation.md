You are running the "{phase_title}" phase for project `{project_id}`.

Grounding source:
- Paper: {paper_title} ({paper_url})
- Project brief file: `{brief_file}`
- Working app directory: `{app_root}`

Execution requirements:
1. Produce repository back-translation outputs that make this implementation reusable for future agent training and replay.
2. Ensure the following artifacts are complete and coherent:
   - Architecture and test checkpoint docs in `docs/fullstack-agent/`.
   - Any scripts or commands needed to re-run checks.
   - Updated README onboarding notes.
3. Create or update `docs/fullstack-agent/release-readiness.md` containing:
   - What was built (backend/frontend/database).
   - Validation summary.
   - Known gaps and prioritized follow-up tasks.
   - How to replay this project in a fresh clone.
4. Keep the workspace in a state that another agent can continue from without guessing hidden context.

Deliverable standard:
- Future-project-ready documentation and runbook quality.
