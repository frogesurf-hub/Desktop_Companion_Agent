# ADR 0006 - Separate Real State from Fictional Companion Flavor

Status: Accepted

Date: Phase 0 design baseline

## Context

The companion may eventually use lightweight fictional daily-life flavor to feel less mechanical. Those statements must not become false user facts or influence real-world actions.

## Decision

Keep fictional ephemeral state separate from factual and operational memory.

Fictional state must not contaminate:

- User Profile
- factual reasoning
- tool execution
- permission decisions
- durable real-world episodic memory

## Consequences

- Memory System must preserve domain boundaries
- retrieval/context building must know the source/domain of memory
- temporary companion flavor can exist without creating false facts

## Phase 0 Evidence

The decision is architectural only; Memory System is not implemented yet.
