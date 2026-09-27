# ADR 0022 — Situations Have Evidence, Temporal Validity and Explicit Ownership

Status: Accepted

Date: 2026-09-27

## Context

Phase 5 introduces a semantic interpretation of runtime facts. An interpretation
can become stale, be incomplete, or be contradicted. Treating it as durable user
Memory or a behavior command would violate existing boundaries.

The owner accepted deterministic rules first and an internal Situation chain
before prompt integration. Concrete lifecycle details remain subject to this
document's review.

## Decision

1. Situation owns bounded evidence aggregation, deterministic interpretation,
   situation identity, revision and temporal validity.
2. A Situation is an evidence-backed interpretation. Its existence and transition
   can be published as facts about the engine; its content is not promoted to an
   unconditional world fact merely by publication.
3. Immutable snapshots preserve evidence references, rule identity/version,
   observation times, evaluation times and a validity boundary.
4. ACTIVE, ENDED and EXPIRED are distinct. Loss of timely support does not prove
   that the user's task succeeded. Degraded capability state is represented
   separately from a normal empty set of active situations.
5. Active identity is grouped by an explicit kind and subject. An ended or expired
   instance is not revived under the same identity. A later matching episode
   receives a new identity.
6. Situation state is transient and bounded for Phase 5. It does not survive Core
   restart and does not write to Memory.
7. Clock remains runtime time authority. Late, duplicate, future and expired facts
   follow explicit deterministic policies, described in the design and verified
   at the boundaries. Numeric confidence probabilities are not invented.
8. Situation does not own Attention, behavior execution, resource admission,
   Permission, Provider construction, desktop observation or Memory governance.
9. First implementation rules do not require Memory or an LLM. Future factual
   Memory inputs must preserve provenance, scope and freshness rather than
   turning prepared prompt strings into authoritative evidence.

## Alternatives considered

- Persist every inferred Situation as Working Context: rejected for this phase;
  it would mix transient interpretations with governed factual Memory.
- Free-form LLM labels as the first contract: deferred; it complicates repeatable
  validation and adds latency/failure and uncertainty handling before boundaries exist.
- One mutable global dictionary shared with all modules: rejected; ownership,
  validity and consistent reads would be implicit.

## Consequences

The implementation needs explicit domain types, a bounded state owner, read-only
snapshots and deterministic lifecycle tests. Rule parameters may evolve without
changing the architectural ownership boundary.

Recognized situations do not authorize actions. A later Prompt integration must
review inference labeling and Memory-learning contamination explicitly.

## Non-decisions

No desktop collector, Unity integration, embeddings, Situation persistence,
user-facing notification policy, cloud/local switching, or Behavior implementation
is selected here. Initial rule thresholds belong to the design and tests.

## Relationship

Preserves ADR 0005, 0006, 0010, 0015, 0016, 0018 and 0019.
Companion decision: ADR 0023.
Design: `../PHASE_5_SITUATION_ENGINE_DESIGN.md`.

## Acceptance record

The owner accepted the Phase 5 scope and prioritized the engineering workflow on
2026-09-27. The Assistant reviewed the detailed design against the current source,
accepted ADRs, and the owner-supplied complete staged diff. This is the accepted
design decision for Task 2; it is not an independent review, code implementation,
or runtime acceptance. Product-scope changes still require an Owner Decision.
