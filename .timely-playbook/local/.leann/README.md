# LEANN retrieval index

Timely stores the project-local retrieval index here.

- Derived from: `.timely-playbook/local/.cxdb/cxdb.sqlite3`
- Default artifact: `index.json`
- Purpose: fast local retrieval across orchestrator state, guardrails, trackers,
  and status snapshots

Generated index files are intentionally omitted from packaged template exports.
Rebuild or query the local index with:

```bash
python .timely-playbook/bin/orchestrator.py context-sync
python .timely-playbook/bin/orchestrator.py context-search "planner tasks"
```
