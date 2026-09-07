# ADR 0004 - Local-First Runtime and Provider Abstraction

Status: Accepted

Date: Phase 0 design baseline

## Context

The companion is intended to remain useful even when cloud services are unavailable and should not be permanently tied to one model vendor.

## Decision

Design runtime modes around:

- Offline
- Local AI
- Hybrid
- Cloud

All external intelligence capabilities should be replaceable through provider/adapter boundaries where practical.

DeepSeek is the planned first cloud LLM provider, not the permanent Agent Core interface.

## Consequences

- provider-specific SDK types must not leak into core Agent contracts
- failure / fallback semantics need explicit design
- local model adapters can be added later without rewriting presentation or memory architecture

## Phase 0 Evidence

Settings already expose runtime mode and provider identity, but no provider implementation exists yet.
