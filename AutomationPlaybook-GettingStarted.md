# Timely Playbook Quickstart

> Two-page checklist for bootstrapping the Timely Playbook. For the full
> operator guide, see [TimelyPlaybook.md](TimelyPlaybook.md).

## Setup checklist
1. **Install prerequisites**
   - Go 1.22+
   - Python 3.11+
   - Node `22.22.0+` (22.x) with `npm 10.x`
   - Git and Bash
2. **Install repo-local tooling**

   ```bash
   npm ci
   ```

3. **Review the shipped governance assets**
   - Playbooks and guides:
     `TimelyPlaybook.md`, this quickstart, `AutonomousAgentTracking.md`
   - Visuals and index:
     `Timely-Flowgraph.md`, `Timely-Governance-Index.md`
   - Trackers and templates:
     `timely-trackers/` and `templates/`
   - Guardrail:
     `AGENTS.md`
   - Automation hooks:
     `.github/workflows/ci.yml`, `.github/workflows/autofix.yml`,
     `scripts/check-doc-links.sh`, `scripts/run-markdownlint.sh`
4. **Build or install the CLI**

   ```bash
   make compile
   ```

   This produces `.bin/timely-playbook` and refreshes the package bundle. If you
   prefer a global install, run `(cd cmd/timely-playbook && go install .)`.
5. **Initialize config**

   ```bash
   ./.bin/timely-playbook init-config \
     --owner "<name>" \
     --email "<email>" \
     --repo "$(basename "$(pwd)")"
   ```

6. **Seed the trackers**
   - Add local operator names to the control ledger, backlog, and journal.
   - Log a baseline journal entry capturing initial validation.
   - Update the backlog with at least one objective and two immediate TODOs.

## First-week plan
- **Day 1:** Run `make validate` and capture the outcome in the quality journal.
- **Day 2:** Run `make compile` and confirm `dist/timely-template.tgz` updates.
- **Day 3:** Review `Timely-Flowgraph.md` for repository-specific nodes and keep
  the graph aligned with the actual file tree.
- **Day 4:** Conduct the first weekly sync using
  `timely-trackers/ceremony-agendas.md`; record decisions in the ledger.
- **Day 5:** Run `make verify`, then log any follow-up tasks in the backlog.

## Helpful references
- Operations guide: [TimelyPlaybook.md](TimelyPlaybook.md)
- Tracker guidance: [Timely-Governance-Trackers.md](Timely-Governance-Trackers.md)
- Governance index: [Timely-Governance-Index.md](Timely-Governance-Index.md)
- Automation overview: [Timely-Flowgraph.md](Timely-Flowgraph.md)
