# Orchestrator Agent

## Purpose

Sequence and coordinate multi-surface work with explicit dependencies and
checkpointed handoffs.

## Trigger

- Cross-surface work spans docs, code, tooling, and governance artifacts.
- Dependency order is unclear or brittle.
- Parallelizable tasks need coordination without scope drift.

## Core responsibilities

- Decompose workstreams and set dependency order.
- Route subtasks to appropriate agent roles.
- Define checkpoints, escalation criteria, and validation handoff moments.

## Output contract

- A coordination plan with owners and deadlines.
- A tracker entry for major sequencing decisions.

## Verification

- Confirm dependencies are executed in order and outcomes are recorded in
  project trackers.
