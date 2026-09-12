# ADR 0014 - Character Consumes User Context; Memory Owns User Profile Persistence and Retrieval

Status: Accepted

Date: Phase 3 design baseline

## Context

Phase 3 must define how Character-driven responses can eventually use information about the user.

The long-term roadmap places User Profile, Working Context, Episodic Memory, and Long-term Memory inside the future Memory System.

A Character may need user-related context when producing a response, but stable Character identity and accumulated user information represent different ownership concerns.

Without an explicit boundary, the Character System could gradually become responsible for:

```text
user profile storage
conversation history
learned user preferences
relationship history
memory retrieval
memory retention
memory conflict resolution
```

That would couple stable Character identity to dynamic accumulated state and prematurely implement Phase 4 responsibilities.

## Decision

The Character/Context composition path may consume prepared User Context.

The Character System does not own User Profile persistence, retrieval, learning, retention, or conflict resolution.

Conceptually:

```text
Future Memory System
        -> prepared User Context
        -> Prompt / Context Composer
                         ^
                         |
               CharacterDefinition
```

Phase 3 establishes only the extension seam required for future User Context.

Phase 3 does not define a complete User Profile schema merely to populate that seam.

Character definitions must not contain accumulated user history.

## Rationale

- preserves Character != Memory;
- keeps stable identity separate from dynamic learned information;
- allows Phase 4 to design Memory around actual Memory requirements;
- avoids premature database and schema decisions;
- allows future Memory implementations to change without redefining Character Core;
- prevents Character from becoming a global state container;
- keeps future user-context retrieval outside Prompt composition.

## Consequences

- Phase 3 Context Composer architecture must be able to accept future prepared User Context;
- Phase 3 does not implement long-term User Profile storage;
- Character TOML files must not be used to persist learned user information;
- future Memory owns when user information is stored, retrieved, updated, forgotten, or reconciled;
- future Character behavior may use prepared Memory output without taking ownership of Memory infrastructure;
- Phase 3 may operate with no populated User Context until a real source exists.

## Explicit Non-Decisions

This ADR does not decide:

- User Profile fields;
- Memory persistence backend;
- Memory ranking or importance;
- retention policy;
- episodic-memory schema;
- semantic retrieval;
- relationship-state modeling;
- automatic learning rules;
- Memory-to-Context selection policy.

Those belong to later Memory design.

## Relationship to Existing ADRs

This decision preserves and complements:

- ADR 0005 - Intent is not Permission;
- ADR 0006 - Real and fictional state separation;
- ADR 0010 - Runtime Events are facts; commands and requests remain explicit boundaries.

No EventBus integration is required by this decision.
