# Phase 4 Task 6 Implementation Plan

## Task

Agent + Composer Integration

Status: Design Approved

## Goal

Connect the completed Memory Retrieval pipeline into the Agent Runtime.

Current:

Memory Storage ↓ Repository ↓ MemoryRetrievalService ↓
PreparedMemoryContext

Target:

User Message ↓ Agent.process_message() ↓
MemoryRetrievalService.retrieve() ↓ PreparedMemoryContext ↓
PromptContextComposer ↓ LLMRequest ↓ Provider

------------------------------------------------------------------------

# Design Decision

## Retrieval Strategy

Use request-level Memory Retrieval.

Reason:

-   Memory is dynamic factual context.
-   Current project scale does not require caching.
-   Correctness is prioritized before optimization.
-   Avoid premature cache invalidation complexity.

------------------------------------------------------------------------

# Architecture Boundary

Agent responsibilities:

-   Receive message
-   Orchestrate runtime context preparation
-   Request Memory Context
-   Call Composer
-   Call Provider

Composer responsibilities:

-   Combine prepared contexts
-   Generate LLMRequest

Composer must not:

-   Query Memory
-   Access Repository
-   Decide Memory policy
-   Modify Memory

------------------------------------------------------------------------

# Expected Changes

## src/agent_core/core/agent.py

Add:

-   MemoryRetrievalService dependency

Runtime flow:

1.  Receive Message
2.  Generate TemporalContext
3.  Retrieve Memory Context
4.  Call Composer
5.  Call Provider

------------------------------------------------------------------------

## src/agent_core/composition/composer.py

Add:

PreparedMemoryContext input.

Before:

compose( character, temporal_context, user_message )

After:

compose( character, temporal_context, memory_context, user_message )

Composer only renders prepared data.

------------------------------------------------------------------------

## Tests

Update:

-   Agent tests
-   Composer tests

Verify:

-   Agent triggers retrieval
-   Memory reaches Composer
-   Existing context ordering remains stable

------------------------------------------------------------------------

# Out of Scope

Do not implement:

-   Automatic learning
-   Memory write pipeline
-   Memory UI
-   WebSocket Memory protocol
-   Cache
-   Vector search

------------------------------------------------------------------------

# Acceptance Criteria

Task complete when:

-   Runtime uses Memory Retrieval.
-   PreparedMemoryContext reaches Composer.
-   Provider layer remains unchanged.
-   pytest passes.
-   ruff passes.
-   mypy passes.
-   git diff --check passes.

------------------------------------------------------------------------

# Implementation Order

1.  Inspect existing tests.
2.  Add Memory Retrieval dependency.
3.  Extend Composer input.
4.  Update rendering.
5.  Update tests.
6.  Run validation.
7.  Review diff.
8.  Commit.
