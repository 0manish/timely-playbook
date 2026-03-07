# Test Run Journal Template

> Use this log to prove regular unit, integration, and regression coverage. Agents append a new entry each time a suite runs.

## Run Log
| Run ID | Date | Trigger | Scope | Command(s) | Result | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| <!-- 2024-05-01-regression --> | <!-- YYYY-MM-DD --> | <!-- Scheduled/Nightly/PR# --> | <!-- Unit / Integration / Regression / Smoke --> | <!-- e.g., `make validate` --> | <!-- Pass/Fail --> | <!-- Link to logs, artifacts, dashboard --> |

## Observations & Follow-ups
- **Failures noted:** <!-- Summaries + links to issues. -->
- **Coverage deltas:** <!-- Lines/areas with improved coverage, or gaps discovered. -->
- **Next actions:** <!-- e.g., add new regression case, update flake guard. -->

## Scheduling
- **Unit tests cadence:** <!-- e.g., every PR via CI. -->
- **Regression cadence:** <!-- e.g., nightly + pre-release. -->
- **Data refresh policy:** <!-- e.g., synthetic fixtures rotated weekly. -->

Keep historical entries—automation can mine the table to detect missed cadences or repeated failures.
