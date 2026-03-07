You are running the "{phase_title}" phase for project `{project_id}`.

Grounding source:
- Paper: {paper_title} ({paper_url})
- Project brief file: `{brief_file}`
- Working app directory: `{app_root}`
- Template: `{template}`

Project brief content:

{brief_text}

Execution requirements:
1. Inspect the existing repository skeleton in `{app_root}` before editing.
2. Translate the brief into concrete full-stack contracts: domain entities, API endpoints, frontend routes, validation rules, and failure states.
3. Define development-oriented tests that can be run during implementation (API checks, UI flows, data persistence checks).
4. Keep architecture decisions practical for the chosen template and avoid speculative tech migrations.
5. Create or update `docs/fullstack-agent/architecture.md` with:
   - System context and architecture boundaries.
   - API contract table.
   - Data model table.
   - Test matrix for backend/frontend/integration.
   - Definition of done.
6. Update project README with a concise "Build Plan" section that links to `docs/fullstack-agent/architecture.md`.

Deliverable standard:
- Implement edits directly in the repository.
- Keep the output deterministic and suitable for later phases.
