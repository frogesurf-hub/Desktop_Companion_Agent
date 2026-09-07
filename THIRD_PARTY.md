# Third Party References

This file is a reference register, not a dependency manifest.

Its purpose is to preserve what the project learned from external work and to prevent future developers or development AIs from rediscovering or copying code without understanding licensing and architectural fit.

## 1. OpenMeido

Repository:

```text
https://github.com/OpenMeido/OpenMeido
```

Phase 0 recorded license:

```text
GPL-3.0
```

Primary value to this project:

- desktop-companion product shape
- Live2D integration patterns
- Persona / character configuration ideas
- memory architecture lessons
- TTS integration ideas
- provider abstraction
- proactive observation / interaction patterns

Phase 0 decision:

- useful as an architecture / prototype reference
- do not casually copy code into a differently licensed public project
- if a distributed derivative directly incorporates GPL code, GPL obligations must be reviewed before distribution

Important memory lesson preserved from early research:

- temporary work state should not automatically become long-term facts
- work context, personal facts, and durable memory need explicit separation

---

## 2. Project AIRI

Repository:

```text
https://github.com/moeru-ai/airi
```

Phase 0 recorded license:

```text
MIT
```

Primary value:

- digital-life / AI Companion framing
- Live2D / VRM embodiment
- voice interaction
- plugin / extension thinking
- multi-platform companion runtime ideas

Phase 0 decision:

Use AIRI primarily to study digital-life and embodiment architecture. Do not copy its entire product architecture into this project because Desktop Companion Agent has a different core emphasis: desktop situation understanding, attention, and permission-controlled capabilities.

---

## 3. screenpipe

Repository:

```text
https://github.com/screenpipe/screenpipe
```

Primary value:

- desktop context acquisition
- Activity Timeline
- accessibility-first observation
- event-driven sensing
- local context processing

Architecture lesson:

```text
Event / accessibility / native context
  -> timeline / structured context
  -> screenshot only when needed
  -> AI interpretation when valuable
```

Do not build the perception system as continuous screenshot streaming.

Phase 0 license policy:

- treat screenpipe source as license-sensitive / restricted until the exact version and intended use are verified
- architecture can be studied
- do not copy source into a future public/distributed repository without a fresh license review

---

## 4. Microsoft UFO

Repository:

```text
https://github.com/microsoft/UFO
```

Phase 0 recorded license:

```text
MIT
```

Primary value:

- Windows UI Automation
- Windows-native application interaction
- application-agent concepts
- desktop environment understanding

Long-term capability priority informed by this reference:

```text
API / explicit tool
  -> OS-native interface
  -> UI Automation
  -> vision + mouse fallback
```

The project should not default to visual clicking when a structured Windows interface exists.

---

## 5. Agent-S

Repository:

```text
https://github.com/simular-ai/Agent-S
```

Phase 0 recorded license:

```text
Apache-2.0
```

Primary value:

- computer-use agent architecture
- GUI interaction
- action execution
- visual fallback strategies

Phase 0 decision:

Agent-S is a future fallback reference for tasks where native APIs / UI Automation cannot provide enough information. Vision-based computer use should remain lower priority than structured interfaces.

---

## 6. Open-LLM-VTuber

Repository:

```text
https://github.com/Open-LLM-VTuber/Open-LLM-VTuber
```

Primary value:

- Live2D
- voice pipeline
- offline companion patterns
- character customization

Status:

Secondary future reference for Avatar + Voice. Verify the exact license/version before copying or integrating code.

---

## 7. SillyTavern

Repository:

```text
https://github.com/SillyTavern/SillyTavern
```

Phase 0 recorded license:

```text
AGPL-3.0
```

Primary value:

- Character Card / Persona representation
- lore / contextual character data
- long-context interaction patterns
- user-defined character configuration

Decision:

Reference character-system ideas only; it is not the core architecture for this desktop companion runtime.

---

## 8. Mem0

Repository:

```text
https://github.com/mem0ai/mem0
```

Phase 0 recorded license:

```text
Apache-2.0
```

Primary value:

- durable memory concepts
- memory retrieval
- user information storage
- memory update strategies

Decision:

Use as one memory-system reference when Phase 4 begins. The project's memory domains and truth/fiction separation remain project-owned decisions.

---

## 9. LangGraph

Repository:

```text
https://github.com/langchain-ai/langgraph
```

Phase 0 recorded license:

```text
MIT
```

Primary value:

- workflow / state-machine patterns
- multi-step Agent execution
- state transition modeling

Decision:

Reference workflow ideas. Do not hard-bind the Agent Core to LangGraph unless a future subsystem demonstrates that the dependency is justified.

---

# Reference Philosophy

Desktop Companion Agent follows these rules:

1. **Reference, do not blindly fork.** External projects solve adjacent problems; this project owns its core companion architecture.
2. **Architecture lesson != code license.** An idea can be learned without copying implementation.
3. **License before code reuse.** Before adapting or copying code, record the exact repository, version/commit, license, and intended distribution model.
4. **Prefer explicit classification.** Every external use should be identified as one of:
   - architectural inspiration
   - adapted implementation
   - copied component
   - external runtime/service integration
5. **Core systems stay replaceable.** LLM, TTS, vision, memory, avatar, tools, and app adapters should remain behind stable interfaces where practical.
6. **Project-specific differentiators remain custom.** Situation Engine, Attention Engine, Permission architecture, memory-domain boundaries, and companion behavior should not become accidental copies of another product.
7. **Re-check licenses before distribution.** This file records Phase 0 understanding and policy; it is not a substitute for a fresh license check before publishing or distributing third-party-derived code.
