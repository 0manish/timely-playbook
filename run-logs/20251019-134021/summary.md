# Timely Playbook Weekly Status

- Generated: 2025-10-19T13:40:21Z
- Overall status: On Track

| Focus | Status | Details | Recommended Action |
| --- | --- | --- | --- |
| Quality Journal | On Track | entries: 3; latest 2025-10-19 (2025-10-19-guardrails) | Append the latest cadence summary if a new run occurred. |
| Control Ledger | On Track | decisions logged: 8; latest 2025-10-19 (Adopt directory-specific guardrails and document them in Flowgraph.) | Continue logging decisions as governance evolves. |
| Backlog | On Track | open items: 2; next due 2025-10-20 | Review backlog during the weekly sync. |
| Docs Link Check | Informational | Not run automatically; review recent evidence or trigger when needed. | `./scripts/check-doc-links.sh` |
| golangci-lint | Informational | Manual signal; capture results in the journal when executed. | `golangci-lint run ./...` |
| Go Test (race) | Informational | Run on demand and append evidence to the journal. | `go test ./... -race` |
