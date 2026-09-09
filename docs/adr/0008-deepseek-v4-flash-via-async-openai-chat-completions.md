# ADR 0008 - DeepSeek V4 Flash via Async OpenAI-Compatible Chat Completions

Status: Accepted

Date: Phase 1 DeepSeek adapter design

## Context

Phase 1 now has a provider-neutral asynchronous LLM contract and an Agent runtime that depends only on that contract.

A concrete DeepSeek adapter is required to complete the original real-LLM MVP.

The adapter design must choose:

- the initial model
- the client / transport mechanism
- thinking behavior
- streaming behavior
- timeout
- retry
- cancellation semantics

without leaking provider-specific details into Agent Core.

## Decision

Use:

```text
default model: deepseek-v4-flash
API: OpenAI-compatible Chat Completions
Python client: openai.AsyncOpenAI
base URL: https://api.deepseek.com
streaming: false
thinking: explicitly disabled by default
application request timeout: 60 seconds
automatic retries: 0
```

The model, timeout, and thinking flag are provider configuration.

The adapter must allow asyncio cancellation to propagate unchanged.

The adapter owns and closes its asynchronous SDK client.

## Rationale

### V4 Flash

Phase 1 is a conversational MVP without memory, tools, or autonomous planning. V4 Flash is the lower-latency / lower-cost default suitable for this first vertical slice. The model remains configurable so V4 Pro can be selected without changing Agent Core.

### Chat Completions

The Provider contract is already message-oriented, so Chat Completions is the smallest direct translation. Responses-API-specific capabilities are not required in Phase 1.

### Async OpenAI-compatible SDK

DeepSeek documents OpenAI-compatible access. `AsyncOpenAI` matches the existing asynchronous Provider contract and provides a maintained client and typed failure hierarchy while keeping SDK types inside the adapter.

### Thinking disabled

Current DeepSeek V4 behavior enables thinking by default. Phase 1 explicitly disables it to avoid silently adding reasoning latency/cost and reasoning-state complexity to a simple interactive MVP.

### 60-second request budget

The vendor / SDK defaults allow requests to remain pending far longer than is appropriate for interactive desktop chat. A configurable 60-second application deadline creates predictable behavior.

### No automatic retry

The SDK has automatic retry behavior by default. Phase 1 disables it so one Agent request corresponds to one external attempt. Retry, backoff, idempotency, duplicate-billing risk, fallback, and observability should be designed together later.

### Cancellation

Task cancellation is runtime control flow and must not be disguised as a provider failure. Protocol-level user cancellation is outside Phase 1.

## Consequences

- add the `openai` dependency to `pyproject.toml`
- extend provider-specific settings
- replace the temporary Echo provider in the composition root after the adapter is ready
- add explicit provider cleanup
- deterministic tests mock / fake the SDK boundary
- no real API key is used in ordinary automated tests
- a later retry/fallback design can use the Provider error classification
- future streaming requires a separate protocol/runtime design under ADR 0007

## Non-Decisions

This ADR does not add:

- tools
- memory
- prompt/personality policy
- user-requested cancellation protocol
- automatic provider fallback
- max token policy
- sampling policy
- Responses API
