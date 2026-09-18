# Phase 4 Task 6-A Design Plan

## Goal

Introduce Memory Retrieval into Agent Runtime while keeping existing
boundaries.

Current:

User Message ↓ Agent ↓ TemporalContext ↓ Composer ↓ Provider

Target:

User Message ↓ Agent ├── TemporalContext ├── Memory Retrieval └──
Character ↓ Composer ↓ Provider

------------------------------------------------------------------------

# 1. Design Decision

## Memory Retrieval Location

Decision:

Agent orchestrates Memory retrieval.

Reason:

-   Agent is runtime coordinator.
-   Composer should remain a pure context renderer.
-   Memory subsystem remains independent.
-   Future Context Pipeline can replace this without changing Provider.

------------------------------------------------------------------------

# 2. New Interface

Add a retrieval abstraction.

Purpose:

Separate Agent from concrete Memory implementation.

Agent depends on:

MemoryRetriever

not:

SQLite Repository

not:

Database

not:

Governance Service

------------------------------------------------------------------------

# 3. Expected Data Flow

    Message

    ↓

    Agent.process_message()

    ↓

    MemoryRetriever.retrieve()

    ↓

    PreparedMemoryContext

    ↓

    PromptContextComposer

    ↓

    LLMRequest

    ↓

    Provider

------------------------------------------------------------------------

# 4. File Changes

## Add

### src/agent_core/memory/retriever.py

Responsibility:

Define Memory retrieval contract.

Contains:

-   Protocol/interface
-   Retrieval input
-   Retrieval output contract

Output:

PreparedMemoryContext

------------------------------------------------------------------------

## Modify

### src/agent_core/core/agent.py

Changes:

Add dependency:

MemoryRetriever

Runtime flow:

1.  Receive message
2.  Build TemporalContext
3.  Retrieve Memory Context
4.  Pass all prepared context to Composer
5.  Call Provider

Do not:

-   access Repository
-   know SQLite
-   modify Memory

------------------------------------------------------------------------

### src/agent_core/composition/composer.py

Changes:

Add input:

PreparedMemoryContext

Responsibilities remain:

Only compose LLMRequest.

Do not:

-   query Memory
-   retrieve Memory
-   modify Memory

------------------------------------------------------------------------

# 5. Testing Plan

## Agent Tests

Verify:

Fake MemoryRetriever

↓

PreparedMemoryContext

↓

Composer

↓

LLMRequest

Check:

-   Agent calls retrieval
-   Memory reaches prompt composition

------------------------------------------------------------------------

## Composer Tests

Verify:

PreparedMemoryContext renders correctly.

Check sections:

-   User Profile
-   Working Context
-   Relevant Episodes
-   Relationship Context

------------------------------------------------------------------------

# 6. Not Included

Do not implement:

-   Memory writing
-   Automatic learning
-   Cache
-   Vector database
-   UI
-   WebSocket protocol

------------------------------------------------------------------------

# 7. Acceptance Criteria

Task 6-A complete:

-   MemoryRetriever contract exists.
-   Agent can receive retrieval dependency.
-   Composer can consume PreparedMemoryContext.
-   Existing Provider contract unchanged.
-   Tests pass.
