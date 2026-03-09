```mermaid
flowchart TD
    Playbook["Autonomous Agent Tracking Playbook\n(AutonomousAgentTracking.md)"]
    Runbook["Quickstart\n(AutomationPlaybook-GettingStarted.md)"]
    Guide["Operations Guide\n(TimelyPlaybook.md)"]
    Index["Governance Index\n(Timely-Governance-Index.md)"]

    subgraph Governance["Trackers (.timely-playbook/local/timely-trackers/)"]
        Ledger["Control Ledger"]
        Journal["Quality Journal"]
        Trace["Spec Traceability"]
        Backlog["TODO / OKR Backlog"]
        Agendas["Ceremony Agendas"]
    end

    subgraph Templates["Templates (.timely-core/templates/)"]
        AgentsTpl["AGENTS-template.md"]
        LedgerTpl["agent-execution-tracker.md"]
        JournalTpl["test-run-journal.md"]
        TraceTpl["spec-traceability-matrix.md"]
        BacklogTpl["todo-backlog.md"]
    end

    subgraph Automation["Automation"]
        RepoAgents["Repository Guardrail\n(AGENTS.md)"]
        TimelyCLI["Timely CLI\n(.timely-core/cmd/timely-playbook)"]
        Orchestrator["Orchestrator Launcher\n(.timely-playbook/bin/orchestrator.py)"]
        CXDB["CXDB Store\n(.timely-playbook/local/.cxdb/cxdb.sqlite3)"]
        LEANN["LEANN Index\n(.timely-playbook/local/.leann/index.json)"]
        Chub["Context Hub Mirror\n(.timely-core/tools/chub/timely_registry.py)"]
        ChubMeta["Chub Mirror Metadata\n(.chub/timely-mirror-metadata.json)"]
        ChubSkill["Context Hub Skill\n(.timely-playbook/local/skills/chub-context-hub)"]
        SkillInstall["Skill Installer\n(.timely-playbook/bin/install-agent-skill.sh)"]
        ReleaseBootstrap["Release Bootstrap\n(.timely-playbook/bin/bootstrap-timely-release.sh)"]
        Validate["Repo Validation\n(make validate)"]
        Package["Package Build\n(make compile)"]
        Smoke["Bootstrap Smoke\n(.timely-playbook/bin/bootstrap-smoke.sh --smoke)"]
        CI["CI Workflow\n(.github/workflows/ci.yml)"]
        Autofix["Autofix Workflow\n(.github/workflows/autofix.yml)"]
        ReleaseWF["Release Workflow\n(.github/workflows/release.yml)"]
    end

    Downstream["Seeded Repository"]

    Playbook -->|defines structure| RepoAgents
    Playbook -->|recommends| Governance
    Playbook -->|recommends| Templates
    Runbook -->|onboards operators into| Guide
    Index -->|links to| Guide
    Index -->|links to| Governance
    Index -->|links to| Templates

    AgentsTpl -->|seeds| RepoAgents
    LedgerTpl -->|instantiates| Ledger
    JournalTpl -->|instantiates| Journal
    TraceTpl -->|instantiates| Trace
    BacklogTpl -->|instantiates| Backlog

    RepoAgents -->|governs updates to| Governance
    RepoAgents -->|governs updates to| Guide
    Guide -->|documents| TimelyCLI
    Guide -->|documents| CXDB
    Guide -->|documents| LEANN
    Guide -->|documents| Chub
    Guide -->|documents| ChubMeta
    Guide -->|documents| ChubSkill
    Guide -->|documents| SkillInstall
    Guide -->|documents| ReleaseBootstrap
    Guide -->|documents| Package
    Orchestrator -->|records evidence in| Journal
    Orchestrator -->|feeds work into| Backlog
    Orchestrator -->|stores local context in| CXDB
    CXDB -->|feeds local retrieval| LEANN
    TimelyCLI -->|updates| Ledger
    TimelyCLI -->|updates| Journal
    TimelyCLI -->|updates| Backlog
    Chub -->|mirrors| Guide
    Chub -->|mirrors| Governance
    Chub -->|writes| ChubMeta
    SkillInstall -->|installs| ChubSkill
    Validate -->|checks| Guide
    Validate -->|checks| Governance
    Validate -->|checks| RepoAgents
    Validate -->|checks| ChubSkill
    Package -->|exports| Downstream
    ReleaseBootstrap -->|seeds from published assets| Downstream
    Smoke -->|verifies| Downstream
    CI -->|runs| Validate
    CI -->|runs| Package
    CI -->|runs| Smoke
    Autofix -->|repairs failures from| CI
    ReleaseWF -->|publishes assets from| Package

    click Playbook "AutonomousAgentTracking.md" "Open playbook"
    click Runbook "AutomationPlaybook-GettingStarted.md" "Open quickstart"
    click Guide "TimelyPlaybook.md" "Open operations guide"
    click Index "Timely-Governance-Index.md" "Open governance index"
    click Ledger "../.timely-playbook/local/timely-trackers/agent-control-ledger.md" "Open control ledger"
    click Journal "../.timely-playbook/local/timely-trackers/test-run-journal.md" "Open quality journal"
    click Trace "../.timely-playbook/local/timely-trackers/spec-traceability.md" "Open traceability matrix"
    click Backlog "../.timely-playbook/local/timely-trackers/todo-backlog.md" "Open backlog"
    click Agendas "../.timely-playbook/local/timely-trackers/ceremony-agendas.md" "Open ceremony agendas"
    click AgentsTpl "templates/AGENTS-template.md" "Open AGENTS template"
    click LedgerTpl "templates/agent-execution-tracker.md" "Open ledger template"
    click JournalTpl "templates/test-run-journal.md" "Open journal template"
    click TraceTpl "templates/spec-traceability-matrix.md" "Open traceability template"
    click BacklogTpl "templates/todo-backlog.md" "Open backlog template"
    click RepoAgents "../.timely-playbook/local/AGENTS.md" "Open repository guardrail"
    click TimelyCLI "cmd/timely-playbook/main.go" "Open Timely CLI"
    click Orchestrator "tools/orchestrator/orchestrator.py" "Open orchestrator"
    click CXDB "../.timely-playbook/local/.cxdb/README.md" "Open CXDB notes"
    click LEANN "../.timely-playbook/local/.leann/README.md" "Open LEANN notes"
    click Chub "tools/chub/timely_registry.py" "Open Context Hub mirror generator"
    click ChubSkill "../.timely-playbook/local/skills/chub-context-hub/SKILL.md" "Open Context Hub skill bundle"
    click SkillInstall "scripts/install-agent-skill.sh" "Open skill installer"
    click ReleaseBootstrap "scripts/bootstrap-timely-release.sh" "Open release bootstrap"
    click CI "../.github/workflows/ci.yml" "Open CI workflow"
    click Autofix "../.github/workflows/autofix.yml" "Open autofix workflow"
    click ReleaseWF "../.github/workflows/release.yml" "Open release workflow"
```
