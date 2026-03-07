# Timely Governance Trackers

> Central guidance for maintaining the Markdown trackers that power the Timely
> Playbook. Keep this doc nearby when updating tables manually or scripting CLI
> appends.

## Working with the Timely CLI

- Use `bash .timely-playbook/bin/timely-playbook run-weekly` to record a status
  sweep; it reads these
  trackers to summarize repo health and appends the outcome to the quality
  journal automatically.
- When adding single rows, prefer
  `bash .timely-playbook/bin/timely-playbook append <journal|ledger|backlog>`
  so column ordering stays consistent.
- Manual edits are fine when pairing with the CLI; keep table headers unchanged
  so automation continues to parse them.

## Control ledger (`.timely-playbook/local/timely-trackers/agent-control-ledger.md`)

- **Purpose:** capture owners, escalation paths, milestones, and decisions for
  every governance initiative.
- **Update cadence:** whenever ownership changes, a milestone moves, or a new
  decision is made. Also review during the weekly sync.
- **Key columns:** Date, Decision, Context / Link, Owner.
- **CLI helper:**
  `bash .timely-playbook/bin/timely-playbook append ledger --decision
  "<summary>" --context <path-or-url> [--owner "<name>"] [--date YYYY-MM-DD]`.
- **Manual tip:** keep chronology descending so the weekly summary reports the
  freshest decision first.

## Quality journal (`.timely-playbook/local/timely-trackers/test-run-journal.md`)

- **Purpose:** log automation and manual cadences with evidence links.
- **Update cadence:** after every link check, lint sweep, test run, packaging
  build, bootstrap smoke run, or weekly status sweep.
- **Key columns:** Run ID, Date, Trigger, Scope, Command(s), Result, Evidence.
- **CLI helper:**
  `bash .timely-playbook/bin/timely-playbook append journal --run-id <id>
  --trigger "<source>" --scope "<area>" --commands "<cmd1;cmd2>" --result
  Pass|Fail --evidence "<path1,path2>"`.
- **Manual tip:** keep `Run ID` unique; the CLI enforces this, but manual edits
  should check for duplicates before inserting.

## TODO / OKR backlog (`.timely-playbook/local/timely-trackers/todo-backlog.md`)

- **Purpose:** track near-term TODOs, risks, and quarterly objectives tied to
  governance.
- **Update cadence:** during the weekly sync and whenever the ledger records a
  new follow-up.
- **Key columns:** Priority, Item, Context / Link, Owner, Due Date, Status.
- **CLI helper:**
  `bash .timely-playbook/bin/timely-playbook append backlog --priority
  High|Medium|Low --item "<task>" --context <path-or-url> --owner "<name>"
  --due YYYY-MM-DD --status Todo|In\ Progress|Done`.
- **Manual tip:** keep overdue items visible by updating `Status` to `Done` only
  when the follow-up is truly complete.

## Spec traceability (`.timely-playbook/local/timely-trackers/spec-traceability.md`)

- **Purpose:** link requirements to specs, implementation, and validation.
- **Update cadence:** whenever a guardrail, operator flow, or verification path
  changes.
- **Manual tip:** maintain stable identifiers per row so automated scripts can
  diff coverage over time.

## Ceremony agendas (`.timely-playbook/local/timely-trackers/ceremony-agendas.md`)

- **Purpose:** ready-made checklists for syncs, gate reviews, and retros.
- **Update cadence:** refresh when agendas change or new ceremonies are
  introduced; reference this doc from calendar invites.
- **Manual tip:** add timestamps or owners inline so the weekly status sweep can
  call out stale agendas during reviews.

## When sharing or cloning the trackers

- Re-export the template bundle after edits with:
  `make compile`
  (this refreshes both the directory and `dist/timely-template.tgz`).
- Copy the updated `Timely-Governance-Trackers.md` alongside the trackers when
  bootstrapping a new repo so operators inherit the same instructions.
