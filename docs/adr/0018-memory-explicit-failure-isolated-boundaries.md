# ADR 0018 - Memory Retrieval, Learning, and Governance Use Explicit Failure-Isolated Boundaries

Status: Accepted

Date: 2026-09-15

## Context

Phase 4 must add Memory to the existing Agent runtime without turning PromptContextComposer, Character, EventBus, Provider, or future Behavior infrastructure into Memory infrastructure.

The product also requires automatic learning while prioritizing stability and user control.

Directly allowing extraction logic or an LLM classifier to write arbitrary durable facts would make factual Memory vulnerable to hallucination and weak inference.

Making every Memory interaction an Event would also conflict with the existing Event architecture, where Events represent facts/notifications rather than commands or request/response queries.

Memory availability must not become a single point of failure for ordinary chat.

## Decision

Phase 4 separates Memory into explicit use-case boundaries:

```text
Retrieval
Learning / Recording
Governance
Persistence
```

### Retrieval

Retrieval is a query path.

It produces prepared Memory context for PromptContextComposer.

PromptContextComposer does not query persistence, resolve conflicts, apply retention, or mutate Memory.

Prepared Memory context remains bounded rather than inserting all accumulated Memory into every prompt.

### Learning / Recording

Automatic learning is enabled by default and can be disabled by user configuration.

When disabled, existing Memory retrieval and manual governance continue.

Accepted automatic learning becomes active immediately.

Automatic learning follows:

```text
candidate extraction
 -> eligibility/policy validation
 -> conflict handling
 -> durable commit
```

Candidate extraction does not receive unrestricted direct persistence authority.

The first implementation prioritizes explicit/high-certainty user statements and does not promote unsupported model inference into factual User Profile.

### Governance

Governance provides user-driven inspection, edit, delete, and history capabilities.

User-governance writes are fail-closed: a persistence failure must be reported as failure and must never be presented as success.

### Failure isolation

A recoverable Memory retrieval failure degrades to empty prepared Memory context and ordinary chat continues.

An automatic-learning write failure does not retroactively fail an otherwise valid chat response, but the failure remains observable.

A serious persistence health problem may leave ordinary chat available while exposing Memory as unavailable.

### Event boundary

Memory retrieval and governance are not implemented as EventBus request/response operations.

Memory Events are added only when a real asynchronous fact-notification consumer requires them.

### Permission boundary

Memory content, Character intent, future Behavior proposals, and runtime admission decisions do not grant Tool or Action permission.

## Rationale

- preserves PromptContextComposer as composition rather than service location;
- isolates Memory failure from core conversation availability;
- prevents extraction logic from bypassing factual Memory policy;
- keeps automatic learning user-configurable;
- preserves Event != Command;
- preserves Intent != Permission;
- allows future retrieval algorithms to evolve behind a stable prepared-context boundary.

## Consequences

- Agent integration requires an explicit Memory retrieval dependency or use-case boundary;
- Composer receives prepared Memory context instead of a repository/service;
- automatic learning can evolve independently from persistence;
- governance APIs can later be exposed through WebSocket/WPF without exposing database internals;
- tests must cover memory-unavailable chat fallback;
- tests must cover truthful governance failure reporting;
- future LLM-based extraction/classification remains policy-constrained;
- future Unified Decision logic does not take ownership of Memory persistence or governance.

## Explicit Non-Decisions

This ADR does not decide:

- the exact Memory retrieval ranking algorithm;
- whether automatic candidate extraction is deterministic, rule-based, or LLM-assisted;
- an embedding provider;
- vector search;
- background extraction workers;
- Memory-related Event definitions;
- WPF layout details;
- future Permission implementation;
- future runtime resource/admission algorithms.

## Relationship to Existing ADRs

This decision preserves and complements:

- ADR 0005 - Intent is not Permission;
- ADR 0006 - Real and fictional state separation;
- ADR 0010 - Runtime Events are facts; commands and requests remain explicit boundaries;
- ADR 0014 - Character consumes User Context; Memory owns User Profile persistence and retrieval;
- ADR 0015 - Runtime temporal truth comes from an explicit Clock context.

It does not require changing the existing Provider contract.
