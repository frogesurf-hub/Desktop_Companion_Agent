# ADR 0015 - Runtime Temporal Truth Comes From an Explicit Clock Context

Status: Accepted

Date: Phase 3 design baseline

## Context

Real Phase 2 runtime testing showed that the LLM can answer the current date or weekday incorrectly when no reliable temporal context is supplied.

Current real-world time is runtime state.

It must not depend on:

```text
model prior knowledge
Character fictional background
Character assumptions
WPF-injected user text
periodic TimeChangedEvent publication
```

Future systems such as Memory, Situation, Behavior, and Scheduler may also require consistent temporal semantics.

Phase 3 introduces Prompt / Context composition, making this the appropriate point to establish the minimum temporal-truth boundary.

## Decision

Real runtime temporal truth originates from an explicit Clock abstraction.

The minimum source contract is conceptually:

```text
Clock.now()
    -> timezone-aware datetime
```

A request-specific Temporal Context snapshot is derived from that value:

```text
Clock
    -> TemporalContext
    -> Prompt / Context Composer
    -> LLMRequest
```

Clock is the temporal authority.

TemporalContext is a derived snapshot and does not act as a second independent source of time.

Production runtime uses a system-backed Clock.

Tests use a deterministic controlled Clock.

Phase 3 Clock functionality is limited to obtaining current time.

## Rationale

- fixes an observed real-runtime failure;
- provides deterministic temporal tests;
- makes current time independent from model prior knowledge;
- preserves Real State / Fictional State separation;
- creates a stable time-source boundary for future runtime systems;
- avoids introducing Scheduler semantics into Phase 3;
- avoids high-frequency TimeChanged Events without a real consumer requirement.

## Consequences

- current date, weekday, timezone, and similar runtime context are derived from one timezone-aware datetime;
- Prompt / Context Composer consumes prepared Temporal Context rather than becoming the authoritative clock;
- Character fiction cannot override real runtime time;
- tests can control time without patching global datetime behavior across the application;
- future Scheduler design remains separate from the Clock query boundary;
- naive datetimes must not silently become authoritative runtime temporal state.

## Explicit Non-Decisions

This ADR does not decide:

- Scheduler architecture;
- reminders;
- timers;
- recurring jobs;
- TimeChanged Events;
- simulated or fictional world clocks;
- user time-zone preference persistence;
- future scheduling commands.

## Relationship to Existing ADRs

This decision preserves and complements:

- ADR 0006 - Real and fictional state separation;
- ADR 0010 - Runtime Events are facts; commands and requests remain explicit boundaries.

Current time remains a query/context dependency.

Future time-triggered actions may later produce Events, but that is outside Phase 3.
