# Seeded `.agents/README.md` instruction

Timely seeds should include `.agents/README.md` from the start so projects can
opt into `.agents/agents/*.md` rosters without inventing a roster index format.

Seed behavior:

- Create `.agents/README.md` from
  `.timely-core/templates/agents-readme-template.md`.
- Leave `.agents/agents/` absent until the project adds local role files.
- When `.agents/agents/*.md` exists, keep `.agents/README.md` synchronized with
  exactly one relative Markdown link per role file.
- Validate with
  `python3 .timely-playbook/local/agent-harness/tools/check_agent_harness.py`.

The full example roster pattern lives at
`.timely-playbook/local/agent-harness/templates/agents-readme-sync.md`.
