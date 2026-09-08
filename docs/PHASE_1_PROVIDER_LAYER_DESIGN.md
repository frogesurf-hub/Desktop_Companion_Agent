# Phase 1 - Provider Layer Design

Status: Accepted design baseline for Phase 1 implementation

## 1. Purpose

Phase 1 completes the original AI MVP by replacing the Phase 0 echo-only Agent behavior with a real, provider-agnostic LLM path while preserving the existing C# WPF <-> Python Agent Core architecture.

This document defines the Provider Layer boundary before any DeepSeek-specific implementation is selected.

Phase 0 code state is defined by the latest Phase 0 repository snapshot. Historical checkpoint documentation may contain stale implementation details.

## 2. Phase 1 Goal

Target vertical slice:

```text
WPF Desktop
  -> WebSocket / JSON protocol
  -> Python WebSocketServer
  -> Agent
  -> LLM Provider contract
  -> concrete cloud provider adapter
  -> external LLM
  -> provider-neutral response
  -> Agent
  -> protocol response
  -> WPF Desktop
```

Phase 1 is complete only when the real WPF -> Python -> LLM -> Python -> WPF path has been implemented and manually accepted.

## 3. Scope

### In Scope

- provider-neutral LLM contract
- provider-neutral request / response models
- asynchronous Agent -> Provider call chain
- dependency injection from the Python composition root
- fake provider for deterministic tests
- one real DeepSeek adapter after its design decisions are made
- safe configuration usage
- provider failure isolation
- mapping internal provider failures to the desktop protocol after the protocol error contract is designed
- targeted tests
- quality checks
- documentation updates
- Git commits following the project workflow

### Out of Scope

The following remain outside Phase 1 unless a later explicit requirement changes the scope:

- memory
- character system
- emotion
- situation engine
- attention engine
- perception
- behavior engine
- avatar
- voice
- desktop tools
- permission system
- autonomous desktop actions
- local model implementation
- fallback orchestration
- conversation persistence
- tool calling

## 4. Requirements Baseline

### 4.1 Functional Requirements

1. The Agent must be able to request an LLM response through a provider-neutral contract.
2. The Agent must not depend on DeepSeek-specific SDK, HTTP, request, response, or exception types.
3. The concrete provider must be created in the composition root and injected into the Agent.
4. The existing WebSocket protocol model must remain separate from Provider Layer models.
5. A fake provider must allow Agent behavior to be tested without network access or API credentials.
6. The real provider path must eventually support a successful end-to-end WPF -> Python -> provider -> Python -> WPF interaction.

### 4.2 Non-Functional Requirements

- preserve provider replaceability from ADR 0004
- preserve the existing asynchronous Python runtime
- prevent provider-specific types from leaking into Core
- avoid logging API keys or sensitive request content by default
- keep external-network behavior out of ordinary deterministic unit tests
- use explicit type annotations for new public interfaces
- keep new dependencies canonical in `pyproject.toml`
- do not add new dependency declarations to the legacy `src/agent_core/requirements.txt`
- use targeted tests during implementation
- do not run the full pytest suite unless the project owner explicitly requests it

## 5. Architectural Boundary

The dependency direction is:

```text
Composition Root
      |
      +------ creates concrete provider
      |
      +------ creates Agent(provider)
                     |
                     v
              LLM Provider Contract
                     ^
                     |
              Concrete Adapter
```

Core code may depend on the provider abstraction.

Core code must not depend on a concrete provider implementation.

The concrete provider implementation may depend on vendor-specific libraries or transport details once those are selected.

## 6. Proposed Module Structure

Phase 1 introduces a Provider Layer under the Python Agent Core:

```text
src/agent_core/
├── communication/
├── config/
├── core/
├── observability/
├── providers/
│   ├── __init__.py
│   ├── base.py
│   └── models.py
└── main.py
```

A concrete DeepSeek adapter is intentionally not part of the initial Provider Layer commit.

After DeepSeek adapter design is accepted:

```text
src/agent_core/providers/
├── __init__.py
├── base.py
├── models.py
└── deepseek.py
```

Tests continue to live under:

```text
src/agent_core/tests/
```

## 7. Provider-Neutral Data Boundary

The existing `agent_core.core.message.Message` represents the Desktop <-> Agent Core protocol envelope and must not become the provider request model.

The conversion boundary is:

```text
Protocol Message
      |
      v
    Agent
      |
      v
LLMRequest
      |
      v
LLMProvider
      |
      v
LLMResponse
      |
      v
    Agent
      |
      v
Protocol Message
```

Initial provider-neutral concepts:

```text
LLMMessage
- role
- content

LLMRequest
- messages

LLMResponse
- content
```

Vendor-specific fields are not part of the common contract unless a demonstrated cross-provider requirement justifies them.

## 8. Async Contract Decision

The Provider contract is asynchronous.

Conceptual contract:

```python
async def generate(request: LLMRequest) -> LLMResponse:
    ...
```

Reasoning:

- the Python runtime is already based on an asynchronous WebSocket server
- real cloud-provider calls are I/O-bound
- blocking provider calls must not block the event loop
- cancellation and timeout handling are easier to model correctly around an async boundary
- future providers can adapt synchronous libraries internally without forcing Core to become synchronous

The Agent call chain therefore moves toward:

```text
WebSocketServer
    -> await Agent.process_message(...)
    -> await provider.generate(...)
```

The exact implementation type (`Protocol`, abstract base class, or another explicit Python contract mechanism) is an implementation-level decision for the Provider Contract task and must preserve the boundary defined here.

## 9. Streaming Decision for Phase 1

Phase 1 uses a non-streaming request/response baseline.

Target contract:

```text
LLMRequest
   -> await generate(...)
   -> LLMResponse
```

Rationale:

1. The current Phase 1 requirement is to complete the original real-LLM MVP.
2. Streaming is not currently a product requirement.
3. Streaming would expand the change across:
   - Provider contract
   - chunk models
   - Python Agent behavior
   - WebSocket protocol
   - C# receive semantics
   - WPF incremental rendering
   - cancellation and partial-failure behavior
4. Adding those changes before they are required would increase architectural surface area and acceptance risk without being necessary to prove the Phase 1 vertical slice.
5. The Provider Layer must remain extensible so a future streaming capability can be designed as an explicit protocol/runtime change.

This is a deliberate scope decision, not a statement that streaming is undesirable.

## 10. DeepSeek Decisions Explicitly Deferred

The following are not decided by this document:

- DeepSeek model name
- official SDK vs OpenAI-compatible SDK vs direct HTTP
- request timeout duration
- retry policy
- retryable error classification
- provider error taxonomy
- provider error -> protocol error mapping
- user-facing provider error wording
- cancellation behavior across the real provider transport
- provider-specific generation parameters

These decisions must be made before implementing the corresponding DeepSeek behavior.

## 11. Error Boundary

The architecture must contain two separate failure boundaries:

```text
Vendor / Transport failure
        |
        v
Internal Provider failure
        |
        v
Agent / Application handling
        |
        v
Desktop Protocol error
```

A vendor exception must not leak directly into Core or the Desktop protocol.

The exact Provider Error Contract and Desktop protocol mapping remain deferred until their design task.

## 12. Configuration Boundary

Configuration is read through the existing settings system.

Expected responsibility:

```text
Settings
   |
   v
Composition Root
   |
   +-- chooses / configures provider
   |
   +-- injects provider into Agent
```

The Agent must not read `DCA_DEEPSEEK_API_KEY` or branch on provider names.

Secrets must remain represented and handled as secrets and must not be written to logs.

## 13. Dependency Management

The canonical Python dependency source is `pyproject.toml`.

Development installation:

```powershell
pip install -e ".[dev]"
```

`src/agent_core/requirements.txt` is an early duplicate dependency file and is not authoritative.

Phase 1 must not introduce a new dependency into only the legacy requirements file.

Cleanup of the legacy file should be performed as an explicit repository-maintenance task rather than silently mixed into unrelated provider behavior.

## 14. Test Strategy

### Provider Contract / Models

Deterministic tests should verify:

- valid provider-neutral request construction
- valid response construction
- contract-compatible fake provider behavior
- type and validation behavior chosen by the implementation

### Agent + Fake Provider

Tests should verify:

- chat input becomes an LLM request
- the Agent awaits the provider
- provider output becomes the expected protocol response
- provider-specific objects are not required by Agent tests

### WebSocket + Agent + Fake Provider

Targeted integration tests should verify the existing communication path still works when the Agent uses an injected fake provider.

### Concrete DeepSeek Adapter

Its tests should be designed after SDK / HTTP and error policies are decided.

Ordinary automated tests must not require a real API key or external network access.

### Manual End-to-End Acceptance

The project owner performs the final real path:

```text
WPF
-> Python
-> DeepSeek
-> Python
-> WPF
```

The full pytest suite remains a final acceptance action performed by the project owner unless explicitly delegated.

## 15. Development Sequence

Phase 1 follows the project workflow:

```text
Requirement Analysis
        ↓
Architecture / ADR
        ↓
Task Breakdown
        ↓
Implementation
        ↓
Targeted Tests
        ↓
Quality Checks
        ↓
Documentation Update
        ↓
Git Review
        ↓
Commit
```

Recommended Phase 1 implementation sequence:

### Task 1 - Provider Contract Foundation

- add provider package
- add provider-neutral models
- add async provider contract
- add deterministic fake provider for tests
- add targeted tests

### Task 2 - Agent Integration

- inject provider into Agent
- make the relevant Agent path async
- update WebSocketServer call site
- update tests with fake provider
- preserve existing protocol semantics

### Task 3 - DeepSeek Adapter Design

Formally decide:

- model
- integration mechanism
- timeout
- retry
- cancellation behavior
- provider error taxonomy
- provider error mapping requirements
- logging constraints

### Task 4 - DeepSeek Adapter Implementation

- implement adapter
- wire configuration in composition root
- add targeted adapter tests
- add configuration validation as required

### Task 5 - Failure Contract Integration

- implement accepted provider error model
- map failures into the accepted Desktop protocol error contract
- test failure paths

### Task 6 - Real MVP Acceptance

- configure real credentials locally
- start Python Agent Core
- start WPF Desktop
- verify real LLM response
- inspect logs for secret leakage
- perform project-owner acceptance

### Task 7 - Phase Documentation and Checkpoint

- update architecture / development docs where the implementation changed facts
- update `PROJECT_STATE.md`
- create Phase 1 checkpoint
- review Git history
- project owner runs full acceptance suite

## 16. Acceptance Criteria for the Provider Layer Foundation

The Provider Layer foundation is ready for Agent integration when all of the following are true:

- a provider-neutral asynchronous contract exists
- request and response models contain no DeepSeek-specific types
- a deterministic fake provider can satisfy the contract
- targeted Provider Layer tests pass
- Ruff checks pass for affected Python files
- mypy checks pass for affected/new public interfaces to the extent required by the current project baseline
- no real API credentials are needed
- no DeepSeek-specific implementation has been introduced prematurely
- the design remains consistent with ADR 0004

## 17. Open Decision Gates

Before the concrete DeepSeek adapter is implemented, the project must explicitly resolve:

1. DeepSeek model
2. transport / client mechanism
3. timeout policy
4. retry policy
5. cancellation semantics
6. Provider Error Contract
7. Provider Error -> Desktop Protocol Error mapping

Streaming is not an open Phase 1 gate: Phase 1 baseline is non-streaming.
