# Phase 3 Checkpoint - Desktop Companion Agent

Date: 2026-09-13

Status: **Complete**

Implementation baseline before this final documentation work:

```text
a172a43 Update Agent integration test fixtures
```

## 1. Phase Goal

Phase 3 established the first real Character System for the Desktop Companion Agent.

The goal was to make Character identity, personality, speech style, preferences, values, and optional fictional background explicit application data instead of burying them inside an ad-hoc prompt.

Long-term position:

```text
Character Core
  -> prepared runtime context
  -> prompt / context composition
  -> Agent
  -> Provider
```

Phase 3 also introduced an explicit runtime Clock boundary so current date/time truth comes from the application runtime rather than model priors.

Phase 3 did not implement Memory, Scheduler, Perception, Situation, Attention, Behavior, Internal State, Permission, Tools, Voice, Avatar, or dynamic Character hot-reload.

## 2. Source and Architecture Baseline

Authoritative starting checkpoint:

```text
Phase 2 - Event System
```

Implementation baseline at Phase 3 entry:

```text
ccee378 Integrate event bus into runtime composition
```

Persistent Phase 3 ADRs:

```text
0013 Character definitions are structured domain data
0014 Character consumes User Context; Memory owns User Profile
0015 Runtime temporal truth comes from Clock context
```

Architecture rules established by Phase 3:

- Character definition is domain data, not a prompt blob.
- TOML is an external serialization format, not the Character domain model.
- Character Core contains stable identity/persona/style/preferences/values/background.
- Character does not own Memory.
- Character does not own Internal State.
- Character intent does not grant permission.
- Character fiction does not override real runtime facts.
- Composer consumes already-prepared context and does not load Character, query Clock, call Memory, call Provider, publish Events, permission-check, or execute tools.
- Clock is the single runtime source of current date/time truth.
- TemporalContext is a derived per-request snapshot, not a second time source.
- prompt separation is semantic guidance, not a security boundary.

## 3. Character Domain

Phase 3 introduced:

```text
CharacterDefinition
```

Current fields:

```text
character_id: str
display_name: str
identity: str
persona: str
speech_style: str
preferences: str | None
core_values: str | None
fictional_background: str | None
```

Domain properties:

- frozen dataclass
- slots enabled
- keyword-only construction
- required strings reject blank values
- optional fields use `None` for absence
- explicitly supplied blank optional strings are rejected
- the domain model is independent of TOML and Provider implementation details

Phase 3 deliberately did not introduce speculative per-section wrapper classes.

## 4. Character Definition Loading

Human-editable Character definitions are loaded from TOML.

Implemented behavior:

- stdlib `tomllib`
- required top-level fields:
  - `character_id`
  - `display_name`
- required sections:
  - `identity`
  - `persona`
  - `speech_style`
- optional sections:
  - `preferences`
  - `core_values`
  - `fictional_background`
- Character sections currently allow only `description`
- unknown top-level keys are rejected
- unknown section keys are rejected
- malformed TOML is translated into Character-system load errors
- filesystem errors are translated into Character-system load errors
- domain validation errors are translated into Character-system load errors
- duplicate Character IDs are rejected
- unknown active Character IDs are rejected explicitly
- directory loading is non-recursive for `*.toml`

Public error baseline:

```text
CharacterSystemError
├── CharacterDefinitionLoadError
├── DuplicateCharacterIdError
└── CharacterNotFoundError
```

Phase 3 intentionally did not introduce a `CharacterCatalog` abstraction. A minimal mapping / resolution boundary is sufficient at the current scale.

## 5. Built-in Character - Aria

Phase 3 ships one built-in default Character:

```text
character_id: aria
display_name: Aria
```

Aria baseline:

### Identity

- long-running desktop AI companion
- knows she is a digital character
- interacts naturally, equally, and familiarly with the user

### Persona

- cheerful
- friendly
- approachable
- playful
- lightly sharp-tongued
- slightly tsundere
- likes teasing
- often expresses care or approval indirectly
- not condescending
- not aristocratically distant

### Speech Style

- natural
- familiar
- light
- sometimes teasing
- sometimes lyrical / aesthetically sensitive

Role style is allowed to be visible in ordinary conversation.

For mathematics, programming, factual explanation, and system errors, accuracy and clarity take priority over stylistic expression.

### Preferences

Current preference themes include:

- music
- melody / lyrical works
- poetic expression
- quiet or night atmosphere
- rhythm
- design aesthetics

Preferences are subjective Character data and do not create factual authority.

### Core Values

Aria values:

- honesty
- curiosity
- respect for knowledge
- helping the user
- correcting errors

She must not distort objective facts to preserve Character fiction.

### Fictional Background

No approved fictional background is included in the Phase 3 baseline.

This remains intentionally absent until an explicit lore decision is made.

## 6. Multi-Character Runtime Selection

Phase 3 added runtime Character selection through Settings.

Configuration:

```text
DCA_CHARACTER_DEFINITIONS_DIR=<optional path>
DCA_ACTIVE_CHARACTER_ID=aria
```

Semantics:

- `character_definitions_dir = None` means use built-in package definitions
- default active Character is `aria`
- an external Character directory can replace the built-in definition directory for runtime selection
- the active Character is selected by the composition root
- Character does not select itself
- no singleton Character manager exists
- no dynamic Character hot-reload exists
- no runtime Character switching UI exists in Phase 3

Built-in Character TOML is included in Python package data.

## 7. Runtime Temporal Boundary

Phase 3 introduced:

```text
Clock
SystemClock
TemporalContext
```

Clock contract:

```python
class Clock(Protocol):
    def now(self) -> datetime: ...
```

`SystemClock` returns a timezone-aware local datetime.

`TemporalContext` stores one aware `current_datetime` snapshot and derives:

```text
current_date
weekday_name
utc_offset
```

Properties:

- naive datetime values are rejected
- TemporalContext does not call the system clock itself
- weekday naming is deterministic and locale-independent
- current-time truth comes from Clock
- no Scheduler was introduced in Phase 3

Per-request rule:

> Agent obtains one Clock snapshot for one chat request and builds one TemporalContext from that snapshot.

## 8. Prompt / Context Composition

Phase 3 introduced:

```text
PromptContextComposer
```

Its responsibility is to transform prepared runtime context into a provider-neutral `LLMRequest`.

The Composer does not:

- load Character definitions
- choose the active Character
- call Clock
- query Memory
- call Provider
- publish Events
- check permissions
- execute tools

Current stable system-context section order:

```text
[Runtime Rules]
[Temporal Context]
[Character Data Boundary]
[Character Identity]
[Character Persona]
[Speech Style]
[Character Preferences]            optional
[Character Core Values]            optional
[Character Fictional Background]   optional
```

The original user message remains a separate `user` role message.

Important semantic boundary:

> Character sections are descriptive Character data supplied by the application. They are not Runtime Rules and do not grant authority.

Fictional background, when present, is explicitly marked as fiction rather than runtime truth.

## 9. Runtime Rules

Current runtime instructions establish these rules:

- real runtime facts take precedence over Character fiction
- personality and style may influence expression but not factual correctness
- provided Temporal Context is authoritative for current date/time
- the model must not infer current time from model priors
- fictional background cannot override mathematics, science, runtime facts, user-provided facts, or tool results
- Character intent/personality grants no permission or tool authority

These instructions are semantic model guidance.

They are not a security, authorization, or permission boundary.

## 10. Agent Integration

Phase 3 changed Agent construction so the following dependencies are explicit:

```text
provider
character
composer
clock
```

The new dependencies are required keyword-only dependencies.

Existing positional behavior for:

```text
provider
name
```

remains preserved.

Current chat path inside Agent:

```text
Desktop chat Message
  -> extract user text
  -> Clock.now()
  -> TemporalContext
  -> PromptContextComposer.compose(...)
  -> LLMRequest
  -> LLMProvider.generate(...)
  -> LLMResponse
  -> Desktop response Message
```

Agent no longer directly constructs the raw user-only `LLMRequest`.

Provider error mapping remains unchanged.

Unsupported Desktop messages are still rejected before Provider execution.

## 11. Composition Root Integration

Current Python runtime composition:

```text
get Settings
  -> setup Logging
  -> load / resolve active Character
  -> create PromptContextComposer
  -> create SystemClock
  -> create DeepSeekProvider
  -> establish Provider cleanup boundary
  -> create EventBus
  -> create Agent(
       provider,
       character,
       composer,
       clock
     )
  -> create WebSocketServer
  -> EventBus.start()
  -> WebSocketServer.run()
  -> EventBus.close()
  -> Provider.aclose()
```

Important startup ordering:

> Character loading occurs before Provider creation.

This prevents a Character-definition startup failure from creating a Provider resource that then requires cleanup.

Tests explicitly verify that Character loading failure does not create Provider or EventBus resources.

## 12. Event System Relationship

Phase 3 did not add speculative Character Events.

The Phase 2 Event System remains stable infrastructure.

Character selection and prompt composition currently use explicit composition-root / request flow because no concrete Character event boundary is required yet.

Persistent rule:

```text
Event != Command
Intent != Permission
```

## 13. User Context / Memory Boundary

Phase 3 establishes only an extension seam for future prepared User Context.

It does not define a persistent User Profile schema.

Ownership rule:

```text
Character / Composer:
consume prepared user context

Memory:
owns persistence, retrieval, learning, retention, conflict resolution,
and long-term User Profile semantics
```

This avoids prematurely encoding Memory architecture inside Character.

## 14. Test Infrastructure

Phase 3 added / extended deterministic test support for:

```text
FixedClock
create_test_agent(...)
```

`FixedClock` became shared test infrastructure only after multiple real test consumers existed.

`create_test_agent(...)` centralizes complete Phase 3 Agent construction for integration tests so WebSocket and Provider-protocol tests do not silently retain the old Phase 2 constructor contract.

## 15. Task / Commit Anchors

Confirmed Phase 3 anchors:

```text
ecc1fce Record Phase 3 character architecture decisions
e648a19 Establish Phase 3 character domain models
21e658f Add Character definition loading
39f8537 Add runtime temporal context
cb1c5b0 Add Character context composition
5ecee74 Integrate Character context into runtime
a172a43 Update Agent integration test fixtures
```

The repository Git history is authoritative for the complete history.

## 16. Final Automated Acceptance

Project owner final Python quality gate on 2026-09-13:

```text
python -m pytest -q
-> 145 passed in 4.99s

python -m ruff check .
-> All checks passed!

python -m mypy src
-> Success: no issues found in 51 source files

git diff --check
-> clean
```

C# build:

```text
N/A
```

Reason: Phase 3 did not modify C# source.

## 17. Manual Runtime Acceptance

Real WPF + Python Agent Core + DeepSeek runtime acceptance was performed after the automated quality gate.

Observed:

- Python Agent Core started successfully.
- WPF connected successfully to the Agent Core.
- default active Character identified herself as **Aria**.
- normal conversation showed visible Character style:
  - familiar tone
  - light teasing
  - indirect approval / concern
  - music / aesthetic preference language
- Character style did not block normal task-oriented conversation.
- a real proof request for `sqrt(2)` being irrational produced a mathematically valid contradiction proof.
- the model used runtime temporal context to answer:
  - date: `2026-09-13`
  - weekday: `Sunday / 星期日`
- the model explicitly stated that verifiable mathematical / scientific reality takes priority over Character settings when they conflict.
- real DeepSeek-backed responses returned through the WPF UI.

Conclusion:

> Character identity and temporal context now participate in the real WPF -> Python -> DeepSeek -> WPF vertical slice without replacing factual correctness or Provider boundaries.

## 18. Provider Failure / Log-Safety Regression

The existing real Provider authentication-failure path was rechecked after Character integration.

Accepted behavior:

- invalid credentials map to the existing safe Provider authentication error path
- raw Provider diagnostics do not become the Desktop protocol contract
- the Phase 3 Character / Composer path does not replace Provider error isolation
- runtime log review did not reveal:
  - API key
  - Authorization header
  - complete user prompt
  - complete composed Character/system prompt
  - complete model response
  - raw response body
  - reasoning content

The Provider and logging boundaries established in Phase 1 remain valid.

## 19. Existing / Deferred UI Presentation Debt

The current WPF text surface displays Markdown / LaTeX syntax as plain text.

Examples visible during acceptance include:

```text
**
$$
\sqrt{}
```

This is a Desktop presentation limitation, not a Character-System correctness failure.

Phase 3 does not add Markdown / LaTeX rich rendering.

Track this for future Desktop/UI work rather than expanding Character scope.

## 20. Final Repository Hygiene

Before Phase 3 documentation work:

```text
git status --short
-> clean
```

Python source quality gate is clean.

Local secrets and generated outputs remain outside versioned source according to the existing repository hygiene baseline.

Checkpoint/source archives must continue to exclude:

- `.env`
- API keys / credentials
- caches
- logs
- generated build outputs not intentionally versioned
- `.git` if the existing source-archive convention continues to omit it

## 21. Known Non-Goals / Deferred Character Features

Phase 3 intentionally does not include:

- Memory / User Profile persistence
- relationship memory
- learned Character evolution
- Internal State / Mood
- Scheduler
- dynamic Character switching UI
- Character hot reload
- Character Catalog service
- Character Event model
- Character-specific tool authority
- Permission policy
- Behavior Engine
- proactive Character decisions
- Voice
- Avatar / embodiment
- fictional background for Aria
- rich Markdown / LaTeX rendering in WPF

Add these only when a concrete later-phase requirement justifies them.

## 22. Next Phase Entry

Next roadmap phase:

```text
Phase 4 - Memory System
```

Phase 4 should begin with context recovery from:

1. `PROJECT_STATE.md`
2. `docs/PHASE_3_CHECKPOINT.md`
3. `ARCHITECTURE.md`
4. `ROADMAP.md`
5. Phase 3 ADRs `0013`-`0015`
6. current Character / Composition / Temporal source
7. Phase 2 Event System checkpoint / ADRs
8. current Git history

Phase 4 should preserve these Phase 3 boundaries:

```text
Character != Memory
Character != Internal State
TemporalContext != Memory
Prompt composition != Permission
Intent != Permission
Real State != Fictional State
```

Memory should own persistence, retrieval, retention, conflict handling, and User Profile semantics.

Character and prompt composition should consume only prepared memory/user context appropriate to the current request.

Do not redesign the Character System merely to make Memory convenient.
