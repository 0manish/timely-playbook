# DFD

```mermaid
flowchart LR
    Operator[Operator]
    Docs[Source Docs]
    Trackers[Trackers and Templates]
    CLI[Timely CLI]
    Orchestrator[Orchestrator Tools]
    Chub[Context Hub Mirror]
    CI[Validation and CI]
    Package[Packaged Template]
    Downstream[Seeded Repository]
    Retrieval[Search and Get]

    Operator -->|edits| Docs
    Operator -->|runs| CLI
    Docs -->|inform| Trackers
    Docs -->|mirror content| Chub
    CLI -->|updates| Trackers
    CLI -->|packages| Package
    Orchestrator -->|reads guides| Docs
    Orchestrator -->|records evidence| Trackers
    Chub -->|serves local search| Retrieval
    Docs -->|validated by| CI
    Trackers -->|validated by| CI
    Orchestrator -->|tested by| CI
    CI -->|verifies| Package
    Package -->|bootstraps| Downstream
    Downstream -->|feeds learnings back| Docs
```
