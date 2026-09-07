# ADR 0001 - C# WPF Desktop + Python Agent Core

Status: Accepted

Date: Phase 0

## Context

The project requires deep Windows integration and a flexible AI ecosystem.

A single-language implementation would force a trade-off between Windows-native desktop capabilities and Python's AI tooling.

## Decision

Use a split runtime:

```text
C# WPF Desktop
  <-> local transport
Python Agent Core
```

C# owns Windows presentation/integration responsibilities.

Python owns Agent intelligence, providers, memory, situation/attention/behavior, and future AI-oriented subsystems.

## Consequences

Positive:

- Windows integration remains natural in C#.
- AI/provider ecosystem remains flexible in Python.
- process boundaries force explicit contracts.

Costs:

- IPC/transport is required.
- protocol compatibility must be maintained across languages.
- process lifecycle/orchestration becomes a future concern.

## Phase 0 Evidence

The split architecture completed a real WPF -> Python -> Agent -> WPF round trip.
