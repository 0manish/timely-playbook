# CXDB workspace state

Timely stores project-local orchestration memory here.

- Canonical store: `cxdb.sqlite3`
- Source of truth: orchestrator state, local tracker/context documents, and
  structured run history
- Ownership: project-local and editable; never copied from `.timely-core/`

Generated database files are intentionally omitted from packaged template
exports. Rebuild or refresh local state with:

```bash
python .timely-playbook/bin/orchestrator.py context-sync
```
