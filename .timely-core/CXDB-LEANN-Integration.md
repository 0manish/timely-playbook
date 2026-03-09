# CXDB and LEANN integration

> Timely Playbook now ships a default three-layer context plane:
> `chub` for external docs, CXDB for project-local context storage, and LEANN
> for local retrieval.

## Default architecture

```text
external docs/APIs -> chub -> CXDB -> LEANN -> agents / orchestrator
```

- `chub` remains the source for current Timely docs and public API docs.
- CXDB is the canonical project-local context store for orchestrator state,
  local governance files, tracker content, and structured execution history.
- LEANN is a derived local retrieval index built from CXDB documents so agents
  can query project context quickly without walking the filesystem.

## Read-only versus project-local layout

The packaged template keeps code and project state separate:

- Read-only implementation: `.timely-core/`
- Project-local configuration and editable docs: `.timely-playbook/local/`
- Project-local CXDB store: `.timely-playbook/local/.cxdb/cxdb.sqlite3`
- Project-local LEANN index: `.timely-playbook/local/.leann/index.json`
- Compatibility export: `.timely-playbook/local/.orchestrator/state.json`
- Human status projection: `.timely-playbook/local/.orchestrator/STATUS.md`

This preserves the existing packaged-template contract: the core ships as an
immutable snapshot, while project-specific state stays under
`.timely-playbook/local/`.

## What CXDB stores

CXDB persists:

- active goal and coordination plan
- tasks, CI runs, and decisions
- local guardrails and tracker documents
- status snapshots and imported state exports

`state.json` remains in the template as a portable import/export surface, but
CXDB is the canonical store once the orchestrator runs.

## What LEANN indexes

LEANN indexes the documents written into CXDB, including:

- orchestrator state summaries
- task, CI, and decision records
- local `AGENTS.md`, `SKILLS.md`, ownership rules, and tracker files
- generated `STATUS.md`

Use LEANN for project-local retrieval. Use `chub` for current Timely docs and
public API documentation.

## Default commands

Sync or rebuild local context state:

```bash
python .timely-playbook/bin/orchestrator.py context-sync
```

Search the project-local LEANN index:

```bash
python .timely-playbook/bin/orchestrator.py context-search "ready tasks"
```

Refresh the status projection and local context state:

```bash
python .timely-playbook/bin/orchestrator.py update-status
```

## Operational guidance

- Do not hand-edit `cxdb.sqlite3` or `index.json`.
- If you manually edit `.timely-playbook/local/.orchestrator/state.json`,
  `AGENTS.md`, trackers, or ownership rules, rerun `context-sync`.
- Packaged template exports include the `.cxdb/` and `.leann/` directories with
  tracked README files, but omit generated databases and indexes.
- Keep `.chub/`, `.timely-playbook/local/.cxdb/`, and
  `.timely-playbook/local/.leann/` out of the immutable `.timely-core/`
  snapshot.
