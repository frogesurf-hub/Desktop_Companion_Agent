# ADR 0013 - Character Definitions Are Structured Domain Data; Prompts Are Derived Representations

Status: Accepted

Date: Phase 3 design baseline

## Context

Phase 3 introduces the Character System.

The product must support multiple user-defined Characters with stable properties such as:

```text
Identity
Persona
Speech Style
Preferences
Core Values
Fictional Background
```

A simple implementation could store each Character as one large system-prompt string.

That would couple Character identity to the current LLM prompt representation and make it difficult to:

- validate Character data;
- distinguish identity, fiction, preferences, and speech style;
- preserve Real State / Fictional State separation;
- compose runtime temporal context and future user context independently;
- support future Providers or local models without rewriting Character definitions;
- build future Character editors against a stable domain model;
- test Character data independently from prompt rendering.

Phase 3 therefore requires a stable distinction between Character domain data and the representation eventually sent to an LLM.

## Decision

Character definitions are structured domain data.

Conceptually:

```text
Character Definition File
        -> Character Loader
        -> CharacterDefinition
        -> Prompt / Context Composer
        -> provider-neutral LLMMessage[]
```

The Character domain does not store or expose one complete raw system prompt as its primary representation.

Phase 3 uses TOML as the human-editable serialization format for Character definitions.

TOML is an external representation:

```text
TOML
    -> Character Loader
    -> CharacterDefinition
```

The Character domain does not depend on TOML parsing.

Character content may contain free-form text inside structured sections such as Persona, Speech Style, Preferences, Core Values, and Fictional Background.

Prompt rendering remains the responsibility of the Prompt / Context Composer.

## Rationale

- preserves a stable Character domain independent from the current Provider;
- allows Character definitions to be validated before use;
- keeps Runtime Policy separate from Character-authored content;
- allows Temporal Context and future User Context to be composed independently;
- enables deterministic Composer tests;
- allows future serialization sources without redesigning Character Core;
- prevents the Character file format from becoming the entire application prompt architecture.

## Consequences

- Character models require explicit structured fields;
- a Character Loader translates TOML into Character domain models;
- malformed or invalid Character definitions fail through explicit parsing or domain validation;
- prompt-rendering changes do not require Character-definition changes unless the underlying domain meaning changes;
- future Character editors can operate on Character data rather than raw LLM prompts;
- users retain free-form expression inside descriptive Character fields while runtime prompt structure remains controlled by the application;
- multiple Character definitions can share one stable domain contract.

## Explicit Non-Decisions

This ADR does not decide:

- the final complete Character TOML schema;
- the exact Python model layout;
- Character editor UI;
- Character package or distribution format;
- database-backed Character storage;
- Character hot reload;
- runtime multi-character conversations;
- local-model-specific prompt formatting.

## Relationship to Existing ADRs

This decision preserves and complements:

- ADR 0004 - Local-first runtime and provider abstraction;
- ADR 0005 - Intent is not Permission;
- ADR 0006 - Real and fictional state separation;
- ADR 0007 - Async non-streaming Provider contract;
- ADR 0010 - Runtime Events are facts; commands and requests remain explicit boundaries.

It does not require changing the existing Provider contract.
