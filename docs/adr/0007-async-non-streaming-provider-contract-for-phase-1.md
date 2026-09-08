# ADR 0007 - Async Non-Streaming Provider Contract for Phase 1

Status: Accepted

Date: Phase 1 design baseline

## Context

Phase 0 established an asynchronous Python WebSocket runtime and a stub `Agent.process_message()` path.

Phase 1 must replace the echo behavior with a real provider-agnostic LLM path. The provider boundary must support cloud I/O without tying Core code to a specific vendor.

A second question is whether token streaming should be included in the initial Phase 1 provider contract.

The current Phase 1 product requirement is to complete the original real-LLM MVP. Token streaming has not been specified as a product requirement.

## Decision

The Phase 1 Provider contract will be asynchronous.

Conceptually:

```python
async def generate(request: LLMRequest) -> LLMResponse:
    ...
```

The initial Phase 1 contract will be non-streaming and will return one provider-neutral response object per request.

Streaming will require a separate explicit design decision because it affects more than the provider adapter. It changes Provider models, Agent behavior, the Desktop communication protocol, cancellation semantics, partial-failure behavior, and WPF rendering.

## Rationale

### Async

- the Agent Core runtime is already asynchronous
- cloud LLM calls are I/O-bound
- synchronous external I/O must not block the WebSocket event loop
- an async boundary gives the runtime a suitable foundation for future cancellation and timeout behavior
- synchronous vendor libraries can be adapted internally by a concrete provider without changing the Core contract

### Non-streaming Phase 1 baseline

- completing the real LLM vertical slice does not require token streaming
- the current protocol exposes complete message envelopes rather than token/chunk semantics
- streaming would broaden Phase 1 across Python, protocol, C#, and UI layers
- adding that complexity before a product requirement exists would increase implementation and acceptance risk
- future streaming support remains compatible with the provider abstraction but must be designed as an explicit capability rather than silently added to the current request/response path

## Consequences

- the relevant Agent path will become asynchronous
- `WebSocketServer` will await Agent processing
- Provider implementations must satisfy an asynchronous Core-facing contract
- deterministic fake providers can implement the same async contract for tests
- the initial DeepSeek adapter will produce a complete provider-neutral response
- no token/chunk protocol is introduced in Phase 1
- a future streaming design may add a separate streaming method or capability rather than mutating the existing semantics without review

## Explicit Non-Decisions

This ADR does not decide:

- DeepSeek model
- SDK vs direct HTTP
- timeout duration
- retry policy
- cancellation transport details
- Provider Error Contract
- Desktop protocol error mapping
- provider-specific generation parameters

Those decisions require separate design before concrete DeepSeek implementation.

## Relationship to Existing ADRs

This decision refines:

- ADR 0002 - WebSocket Desktop/Core transport
- ADR 0004 - Local-first runtime and provider abstraction

It does not supersede either ADR.
