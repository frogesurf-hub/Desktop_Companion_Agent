# ADR 0020 - Automatic Learning Uses Explicit Logical Memory Identity Keys

Status: Accepted

Date: 2026-09-19

## Context

Phase 4 automatic learning must distinguish between:

```text
new fact
duplicate fact
update to an existing logical fact
```

The existing Memory model has:

```text
memory_id
domain
scope
revision history
```

`memory_id` provides durable database identity after a Memory exists,
but a new automatic-learning Candidate still needs a deterministic way
to identify which existing logical Memory it refers to.

Text equality alone can detect some duplicates but cannot reliably
identify updates such as:

```text
User prefers C#.
User now prefers Rust.
```

Embedding similarity or unrestricted semantic guessing would introduce
additional uncertainty and infrastructure that Phase 4 does not require.

## Decision

Phase 4 introduces an optional `MemoryIdentityKey`.

The key represents the semantic identity of one logical factual slot.

Example:

```text
user_profile.preference.programming_language
```

Different revisions may contain:

```text
C#
Rust
Python
```

while retaining the same logical identity.

The identity key:

- belongs to logical Memory, not MemoryRevision;
- may also be carried by an uncommitted MemoryCandidate;
- is normalized before use;
- must not contain whitespace;
- is limited to 256 characters;
- does not replace `memory_id`;
- does not grant persistence or Tool authority.

The key is optional because some event-like or legacy Memory may not
have a stable semantic slot.

Existing-Memory Resolution will use domain, scope, and identity key
before conflict handling.

Exact-content duplicate detection may remain as a fallback for
keyless or legacy Memory.

## Consequences

Automatic learning gains a deterministic boundary between:

```text
identity resolution
and
conflict resolution
```

`MemoryConflictPolicy` remains responsible only for deciding whether a
known existing Memory should be replaced.

Persistence must later store the identity key with logical Memory.

Candidate extraction is responsible for assigning an identity key when
the extracted fact has a stable logical identity.

Phase 4 still does not introduce:

- embeddings;
- vector search;
- fuzzy semantic matching;
- numeric confidence;
- Candidate persistence.

## Relationship to Existing ADRs

This decision extends:

- ADR 0016 - factual Memory domains, scopes, lifecycle and revisions;
- ADR 0017 - SQLite as durable Memory source of truth.

It preserves the distinction between logical Memory identity and
revision history.
