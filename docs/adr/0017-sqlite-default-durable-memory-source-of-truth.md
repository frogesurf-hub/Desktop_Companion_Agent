# ADR 0017 - SQLite Is the Default Durable Memory Source of Truth

Status: Accepted

Date: 2026-09-15

## Context

Phase 4 requires durable Memory with:

- structured factual domains;
- revision history;
- lifecycle/status filtering;
- Character scope;
- transactional correction and deletion;
- governance queries;
- schema evolution;
- local-first desktop packaging.

The project is single-user and local-first in Phase 4.

The persistence design should avoid requiring users to install or operate an external database service.

Earlier project documents mentioned SQLite and SQLAlchemy as planned technologies, but Phase 4 did not treat those historical mentions as an approved Memory design until Memory requirements were established.

## Decision

SQLite is the default durable Memory source of truth for Phase 4.

SQLAlchemy is used inside the Memory persistence adapter.

SQLAlchemy persistence models/types must not become the Memory domain contract.

Conceptually:

```text
Memory Domain
    |
Memory Persistence Contract
    |
SQLite Persistence Adapter
    |
SQLAlchemy
    |
SQLite
```

Alembic manages Memory database schema migrations.

The Memory database is stored in a platform-appropriate application-data location, not in the Git repository, source tree, or a developer-specific fixed path.

Future caches, embeddings, or vector indexes are derived retrieval aids.

They must not become the only factual Memory source of truth.

Phase 4 does not introduce a vector database, embedding provider, RAG framework, Mem0, LangGraph, PostgreSQL service, Redis service, or MongoDB service.

## Rationale

SQLite provides:

- ACID transactions;
- structured queries;
- zero external database daemon;
- straightforward local deployment;
- mature Python/SQLAlchemy support;
- an appropriate operational profile for expected Phase 4 scale;
- a clear upgrade path through migrations.

SQLAlchemy keeps database access explicit while allowing persistence implementation details to stay behind a domain boundary.

Alembic provides a durable schema-evolution path suitable for packaged/open-source software upgrades.

## Consequences

- Memory persistence operations use explicit transactions;
- create/edit/delete operations that span multiple records must be atomic;
- database schema changes require migrations;
- domain code must not import SQLAlchemy persistence models as its public contract;
- application startup must initialize/migrate supported databases safely;
- Memory database health can be reported separately from chat availability;
- future retrieval indexes can be rebuilt from durable Memory data.

## Explicit Non-Decisions

This ADR does not decide:

- the initial table/column schema;
- exact SQLAlchemy mapping style;
- connection-pool tuning;
- SQLite journal/synchronous pragmas;
- backup UI;
- encryption-at-rest;
- cloud synchronization;
- multi-process database sharing;
- vector-index implementation.

Those belong to implementation or future architecture decisions when requirements justify them.

## Relationship to Existing ADRs

This decision preserves and complements:

- ADR 0004 - Local-first Provider abstraction;
- ADR 0014 - Memory owns User Profile persistence and retrieval.

It does not change the LLM Provider contract, WebSocket transport contract, Character TOML contract, or Clock semantics.
