# AGENTS.md Template

## Scope
Describe the directory this file governs (for example `timely-trackers/`,
`cmd/`, `tools/`, or `web/`). Mention any subdirectories explicitly included or
excluded.

## Coding / Writing Conventions
- Summarize formatting expectations (Go fmt, Markdown lint rules, UI naming patterns).
- Reference authoritative style guides or lint configurations.
- Call out forbidden patterns (for example, no TODOs without issue links).

## Testing Requirements
- List mandatory tests before commit.
- Include commands and when they are required.
- Indicate how to record results in the
  [quality journal](../timely-trackers/test-run-journal.md).

## Documentation Expectations
- Specify when to update specs, API docs, or changelogs.
- Point to the
  [spec traceability matrix](../timely-trackers/spec-traceability.md) and note
  how to add entries.

## PR & Review Checklist
- Required PR message sections and citation rules.
- Links to security or privacy checklists.
- Approval requirements (for example, "Needs review from the docs steward for
  governance changes").

## Automation Hooks
- Describe available bots or agents and how they interact with this directory.
- List commands or MCP tools agents should call before merging.

---
Customize each section, remove placeholders, and keep the template concise so
future agents can scan it quickly.
