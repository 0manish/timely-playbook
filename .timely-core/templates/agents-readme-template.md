# Agent roster

This repository is ready to host project-local agent role definitions under
`.agents/agents/`.

## Runtime roster

No project-local agents are registered yet.

When this project adds `.agents/agents/*.md`, replace this section with one
relative Markdown link per role file. Keep entries ordered and run:

```bash
python3 .timely-playbook/local/agent-harness/tools/check_agent_harness.py
```

The check fails when `.agents/agents/` exists but this roster is missing,
incomplete, or stale.
