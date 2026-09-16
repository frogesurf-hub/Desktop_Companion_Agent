# ADR 0016 - Factual Memory Uses Explicit Domains, Scopes, Lifecycle States, and Revision History

Status: Accepted

Date: 2026-09-15

## Context

Phase 4 introduces persistent Memory.

The roadmap previously listed User Profile, Working Context, Episodic Memory, Long-term Memory, Relationship Memory, Today Memory, and Fictional Ephemeral State as candidate areas.

Treating every candidate as a parallel domain would mix different dimensions:

- what a Memory means;
- who/what it is scoped to;
- how long it remains active;
- whether it is real or fictional.

The product also requires user inspection, editing, deletion, automatic learning, conflict handling, and preservation of correction history.

A flat collection of prompt strings cannot support these requirements reliably.

## Decision

Phase 4 factual Memory uses four semantic domains:

```text
USER_PROFILE
WORKING_CONTEXT
EPISODIC
RELATIONSHIP
```

Long-term and today-scoped behavior are lifecycle/retention semantics rather than parallel semantic domains.

Fictional Ephemeral State is not factual Memory and remains isolated from this persistence model.

Memory scope is orthogonal to domain.

Initial scope concepts are:

```text
GLOBAL_USER
CHARACTER
```

User Profile, Working Context, and ordinary Episodic Memory are globally user-scoped in Phase 4.

Relationship Memory is Character-scoped.

User Profile is shared across Characters.

Working Context may survive application restart until retention expiry or explicit clearing.

For Phase 4, Working Context uses a default retention of 7 days and supports user configuration from 1 through 30 days.

The application remains single-user first; the model must not hard-code one concrete human identity as a domain assumption.

A logical Memory has stable identity and revision history.

Corrections/edits create a new revision.

Successful replacement atomically supersedes the previous active revision and activates the new revision.

Initial lifecycle states are:

```text
ACTIVE
SUPERSEDED
EXPIRED
DELETED
```

Delete/forget is semantically distinct from supersede.

Deleted factual content must no longer participate in retrieval or normal history surfaces.

## Rationale

- keeps semantic domain separate from retention;
- prevents Today/Long-term categories from duplicating facts;
- keeps shared user facts independent from Character identity;
- isolates Character-specific shared history;
- supports user correction without silently destroying history;
- enables deterministic conflict behavior;
- preserves Real State / Fictional State separation;
- supports future multi-user evolution without implementing accounts in Phase 4.

## Consequences

- Memory domain models require explicit domain, scope, lifecycle, and provenance semantics;
- conflict handling works on revision/history rather than destructive replacement;
- active retrieval excludes superseded, expired, and deleted content;
- user-driven correction can preserve factual history;
- user-driven delete removes factual content from normal retrieval/history;
- Relationship Memory cannot be treated as global Character-agnostic history;
- future Internal State remains separate from Relationship Memory;
- persistence schema must support atomic revision transitions.

## Explicit Non-Decisions

This ADR does not decide:

- SQL table names or columns;
- Python domain-model implementation details;
- exact retention durations beyond separately approved defaults;
- automatic-learning extraction algorithm;
- confidence/importance scoring;
- vector search;
- multi-user authentication;
- Internal State model;
- Fictional Ephemeral State persistence.

## Relationship to Existing ADRs

This decision preserves and complements:

- ADR 0005 - Intent is not Permission;
- ADR 0006 - Real and fictional state separation;
- ADR 0010 - Runtime Events are facts; commands and requests remain explicit boundaries;
- ADR 0014 - Character consumes User Context; Memory owns User Profile persistence and retrieval;
- ADR 0015 - Runtime temporal truth comes from an explicit Clock context.
