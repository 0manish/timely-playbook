# SKILLS registry for Timely Playbook

This file defines two Timely skill surfaces:
- KISS-derived overlay profiles accepted in direct agent CLI runs and
  `fullstack-*` orchestrator flows
- Repo-local agent skill bundles shipped under `.timely-playbook/local/skills/`

## A-E adoption map (used by fullstack runs)

- Section A — bounded prompt envelope: keep each task prompt scoped to current
  phase, repository boundaries, and explicit skip/stop conditions.
- Section B — structured output and progress logging: record run command,
  timestamped outcomes, validation outputs, and file deltas in reusable
  artifacts.
- Section C — constrained editing and bounded mutation scope: only edit files that
  are explicitly in scope; avoid touching governance-critical paths without
  approval.
- Section D — bounded implementation cycles: one phase = one iteration unless
  governance or user instruction asks for retries.
- Section E — non-disruptive integration: keep all overlays compatible with
  existing `fullstack.py` and
  `.timely-playbook/local/.orchestrator/ownership.yaml` ownership paths across
  configured agent providers.

## Active skills

- `kiss-fullstack-core`: default fullstack profile for standard phases.
- `kiss-fullstack-relentless`: same prompt envelope with stricter scope and
  stricter file mutation limits for high-risk phase edits.

## Repo-local skill bundles

- `chub-context-hub`: repo-local agent skill bundle at
  `.timely-playbook/local/skills/chub-context-hub/SKILL.md` for repo-local
  `chub`/`chub-mcp` usage, Timely mirror validation, and public API doc
  retrieval through Context Hub.
- Install with `bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub`.
- Installed copies are intended to be used while the agent is operating from a
  Timely-seeded repo root so the skill can call
  `bash .timely-playbook/bin/chub.sh ...`.
- The legacy `bash .timely-playbook/bin/install-codex-skill.sh chub-context-hub`
  wrapper remains available for Codex-specific workflows.

## Skill compatibility notes

- `kiss-fullstack-core` and `kiss-fullstack-relentless` are compatible with
  FullStack-Agent phase phases and back-translation logging.
- The following KISS classes are intentionally out-of-band in this repository:
  - `RepoOptimizer`
  - `CreateAndOptimizeAgent`
  - `KISSEvolve`
  - `GEPA`
  - `SelfEvolvingMultiAgent`
- Optimization-style loops require explicit governance review before introducing any
  additional loop controls.

## Machine-readable skill registry

```json
{
  "version": 1,
  "default_skill": "kiss-fullstack-core",
  "repo_local_skills": {
    "chub-context-hub": {
      "path": ".timely-playbook/local/skills/chub-context-hub/SKILL.md",
      "description": "Repo-local agent skill for chub wrappers, Timely mirror validation, and Context Hub MCP setup.",
      "install_command": "bash .timely-playbook/bin/install-agent-skill.sh chub-context-hub",
      "supports_fullstack": false
    }
  },
  "skills": {
    "kiss-fullstack-core": {
      "status": "active",
      "description": "Default fullstack execution profile with KISS A-E constraints.",
      "supports_fullstack": true,
      "prompt_prefix": "You are running under Timely Playbook fullstack governance. Apply only repository changes needed for this phase. Preserve previous phase artifacts and keep changes reviewable.",
      "sections": {
        "A": "Use a bounded prompt envelope and refuse to infer missing requirements beyond this phase request.",
        "B": "Write deterministic artifacts: prompt snapshot, stdout/stderr, validation logs, changed-file manifest, and skill policy report.",
        "C": "Edit only scoped paths and avoid touching governance-critical files unless explicitly listed in task scope.",
        "D": "Complete one phase pass per invocation and capture a clear continuation plan only.",
        "E": "Do not alter orchestrator semantics beyond fullstack command wrappers without explicit approval."
      },
      "scope": {
        "allowed_paths": [
          "*",
          "docs/fullstack-agent/**",
          "artifacts/**",
          ".timely/**",
          ".timely-playbook/local/**",
          ".timely-playbook/config.yaml",
          "PROJECT_BRIEF.md",
          "README.md"
        ],
        "forbidden_paths": [
          ".timely-core/**",
          ".github/**",
          ".vscode/tasks.json",
          "run-logs/**",
          "dist/**",
          "vendor/**",
          ".timely-core/scripts/**",
          ".timely-core/templates/**",
          "AGENTS.md",
          "SKILLS.md"
        ],
        "applicable_phases": [
          "architecture",
          "backend",
          "frontend",
          "integration",
          "backtranslation"
        ],
        "max_changed_files": 120,
        "on_policy_violation": "warn"
      },
      "required_outputs": [
        "success outcome",
        "summary",
        "changed files",
        "rollback hint"
      ]
    },
    "kiss-fullstack-relentless": {
      "status": "active",
      "description": "Higher discipline profile for riskier changes with tighter scope and stronger guardrails.",
      "supports_fullstack": true,
      "prompt_prefix": "Operate as a strict phase executor: complete the request directly, keep changes minimal, and report blocking risks before proceeding to speculative improvements.",
      "sections": {
        "A": "Keep command text minimal and refuse any edits that are not needed for current phase outcomes.",
        "B": "Return explicit evidence for each changed file and a concise run summary in the final run artifact.",
        "C": "No edits outside allowed paths; require explicit approval before scope expansion.",
        "D": "Only one deterministic iteration unless task explicitly asks for rerun.",
        "E": "Preserve fullstack orchestration invariants and do not change ownership or agent boundaries."
      },
      "scope": {
        "allowed_paths": [
          "src/**",
          "libs/**",
          "apps/**",
          "services/**",
          "docs/fullstack-agent/**",
          "artifacts/**",
          "README.md",
          "PROJECT_BRIEF.md"
        ],
        "forbidden_paths": [
          ".timely-core/**",
          ".github/**",
          ".vscode/tasks.json",
          "run-logs/**",
          "dist/**",
          "vendor/**",
          ".timely-playbook/local/.orchestrator/**",
          "AGENTS.md",
          "SKILLS.md"
        ],
        "applicable_phases": [
          "architecture",
          "backend",
          "frontend",
          "integration"
        ],
        "max_changed_files": 60,
        "on_policy_violation": "fail"
      },
      "required_outputs": [
        "success outcome",
        "summary",
        "changed files",
        "rollback hint"
      ]
    }
  }
}
```
