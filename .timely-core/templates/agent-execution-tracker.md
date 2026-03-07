# Agent Execution Tracker Template

> Duplicate this file into
> `.timely-playbook/local/timely-trackers/agent-control-ledger.md` (or similar)
> and keep it updated weekly.

## Overview
- **Milestone / Epic:** <!-- e.g., Template release readiness -->
- **Last Updated:** <!-- YYYY-MM-DD -->
- **Primary Owner (agent or human):** <!-- name or identifier -->
- **Escalation Contact:** <!-- email/Slack -->

## Operating Parameters
| Field | Value |
| --- | --- |
| Mission statement | <!-- Short sentence describing expected outcomes. --> |
| Entry criteria | <!-- Definition of "ready" before the agent starts work. --> |
| Exit criteria | <!-- What must be true before the milestone is closed. --> |
| Tooling surface | <!-- CLI, MCP tool, REST API, etc. --> |
| Observability hooks | <!-- Metrics or logs agents must emit. --> |

## Work Breakdown
| Sequence | Task | Dependencies | Linked Spec / Issue | Target Date | Status |
| --- | --- | --- | --- | --- | --- |
| 1 | <!-- e.g., Refresh packaging docs before a public template release --> | <!-- Dependent tasks --> | <!-- Link --> | <!-- YYYY-MM-DD --> | <!-- Todo/In Progress/Blocked/Done --> |

_Add more rows as needed._

## Quality Gates
- **Required tests:** <!-- e.g., `make validate`, `make compile`, smoke tests. -->
- **Regression cadence:** <!-- e.g., nightly, weekly. -->
- **Link to latest run:** <!-- URL or log reference; update after each run. -->

## Risk & Mitigation Log
| Date | Risk | Impact | Mitigation / Owner | Status |
| --- | --- | --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- e.g., Missing release verification coverage --> | <!-- High/Med/Low --> | <!-- Planned mitigation --> | <!-- Open/Monitoring/Closed --> |

## Decision & Change Log
| Date | Decision | Context / Link | Owner |
| --- | --- | --- | --- |
| <!-- YYYY-MM-DD --> | <!-- e.g., Move validation tooling to repo-local dependencies --> | <!-- Link to doc/PR --> | <!-- Agent or person --> |

Maintain one tracker per milestone or major epic so automation can reason about
ownership, dependencies, and quality posture at a glance.
