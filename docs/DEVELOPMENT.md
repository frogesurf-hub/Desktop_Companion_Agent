# Development Guide

## 1. Environment Setup

### Python Version

Required:

- Python 3.11

Recommended:

- Python 3.11.x
- Use a project-local virtual environment

### Create Virtual Environment

From the repository root:

```powershell
py -3.11 -m venv .venv
```

### Activate Virtual Environment

PowerShell:

```powershell
.\.venv\Scripts\activate
```

After activation, the prompt should contain:

```text
(.venv)
```

### Verify Python Version

```powershell
python --version
```

Expected:

```text
Python 3.11.x
```

### Install Project and Development Dependencies

The canonical development installation is:

```powershell
pip install -e ".[dev]"
```

This installs:

- runtime dependencies declared in `pyproject.toml`
- development dependencies from the `dev` extra (`pytest`, `ruff`, `mypy`)
- the current project in editable mode

`src/agent_core/requirements.txt` still exists at the Phase 0 checkpoint, but it duplicates dependency information and is a cleanup candidate. Do not add new dependencies to only one of the two files without deciding the canonical dependency policy.

---

## 2. Project Structure

Phase 0 high-level structure:

```text
Desktop_Companion_Agent
├── docs
│   ├── adr
│   ├── COMMUNICATION_PROTOCOL.md
│   ├── DEVELOPMENT.md
│   └── PHASE_0_CHECKPOINT.md
├── src
│   ├── agent_core
│   │   ├── communication
│   │   ├── config
│   │   ├── core
│   │   ├── observability
│   │   ├── tests
│   │   └── main.py
│   └── Desktop
│       └── DesktopCompanion.Desktop
├── tools
│   └── DesktopCompanion.ConnectionProbe
├── .editorconfig
├── .env.example
├── .gitignore
├── pyproject.toml
├── PROJECT_STATE.md
├── ARCHITECTURE.md
├── DESIGN.md
├── MVP_DESIGN.md
├── PROJECT.md
├── README.md
├── ROADMAP.md
├── TECH_STACK.md
└── THIRD_PARTY.md
```

Responsibilities:

- `src/agent_core/`: Python Agent Core runtime and tests.
- `src/Desktop/`: C# WPF desktop application.
- `tools/DesktopCompanion.ConnectionProbe/`: transport/protocol diagnostic client.
- `docs/`: technical documentation, checkpoint history, and ADRs.
- `pyproject.toml`: Python project metadata, dependencies, pytest, Ruff, and mypy configuration.
- `PROJECT_STATE.md`: primary context-recovery / current-state document.
- root Markdown files: project-level architecture, design, roadmap, technology, and third-party policies.

Known Phase 0 cleanup: the C# protocol source folder is physically named `Potocol/` even though the namespace is `DesktopCompanion.Desktop.Protocol`; rename the folder to `Protocol/` in a dedicated cleanup commit.

---

## 3. Development Workflow

Every development task should follow this sequence:

```text
Requirement Analysis
        ↓
Design
        ↓
Task Breakdown
        ↓
Implementation
        ↓
Targeted Tests
        ↓
Code Quality Checks
        ↓
Documentation Update
        ↓
Git Commit
```

Do not skip directly from an idea to implementation when the change affects architecture, interfaces, permissions, data models, or persistent state.

---

## 4. Testing

### Run Python Tests

From the repository root:

```powershell
pytest
```

Expected behavior:

- pytest automatically reads `pyproject.toml`
- tests are discovered under `src/agent_core/tests`
- no manual `PYTHONPATH` configuration is required

### Testing Principle

For normal development:

- run tests directly related to the current change
- add or update tests for changed behavior
- do not rely only on manual testing

For AI-assisted development:

- Codex / Claude / GPT should run targeted tests related to their modifications
- they should not run the full test suite unless explicitly requested
- the complete test suite is reserved for final acceptance by the project owner

---

## 5. Python Code Quality

### Ruff Check

Run:

```powershell
ruff check .
```

Purpose:

- detect unused imports
- detect common Python mistakes
- enforce basic style consistency
- catch maintainability issues early

### Ruff Format

Run:

```powershell
ruff format .
```

Purpose:

- automatically normalize Python formatting

Before formatting a large change, review the affected files first.

### Type Check

Run:

```powershell
mypy src
```

Purpose:

- detect invalid type assumptions
- improve interface clarity
- reduce runtime errors in a growing codebase

Type checking may be introduced gradually. Existing modules do not need to become fully strict immediately, but new public interfaces should prefer explicit type annotations.

---

## 6. C# / WPF Development

The desktop layer lives under:

```text
src/Desktop/
```

Primary responsibilities:

- desktop window lifecycle
- Windows integration
- user interaction
- display and avatar hosting
- communication with Agent Core
- permission prompts
- local OS-facing capabilities

The WPF layer must not contain Agent reasoning, memory logic, LLM provider logic, or other Python-core responsibilities.

### Build and Run

Open the Visual Studio solution under `src/Desktop/`.

Use:

```text
F5
```

for debugging.

Before committing Desktop changes:

- confirm the project builds
- run relevant C# tests when they exist
- verify the changed UI flow manually when necessary

---

## 7. Module Boundaries

The project follows separation of responsibilities.

Examples:

```text
Desktop UI
    ↓
Communication Layer
    ↓
Agent Core
```

Not:

```text
MainWindow.xaml.cs
    ↓
Direct DeepSeek API Call
```

Another example:

```text
Behavior Engine
    ↓
Semantic Avatar Action
    ↓
Avatar Adapter
```

Not:

```text
Emotion Module
    ↓
Direct Live2D Parameter Mutation
```

Core modules should communicate through explicit interfaces, messages, events, providers, or adapters.

---

## 8. Communication Contract

C# Desktop and Python Agent Core communicate according to:

```text
docs/COMMUNICATION_PROTOCOL.md
```

Do not invent new message shapes directly inside implementation code.

If a new message type is required:

1. update the protocol design
2. define the message model
3. implement both sender and receiver
4. add tests
5. update documentation

---

## 9. Security and Permission Rules

Core rule:

```text
Intent != Permission
```

Agent initiative never grants additional authority.

Operations involving sensitive capabilities must pass through the permission system, including future access to:

- network services
- files
- screenshots
- microphone
- shell execution
- UI Automation
- Computer Use
- external messaging
- destructive changes

Personality, mood, relationship state, or autonomous behavior must never bypass permission checks.

---

## 10. Local and Online Separation

The project must remain capable of graceful degradation.

Target runtime modes:

```text
Offline
Local AI
Hybrid
Cloud
```

Cloud services are enhancements, not the foundation required for the companion to exist.

When an external provider is unavailable:

- detect the failure
- expose service status
- notify the user appropriately
- fall back when configured
- retain local companion behavior where possible

---

## 11. Configuration and Secrets

Never commit secrets.

Examples that must not be committed:

```text
.env
API keys
access tokens
private credentials
```

Use:

```text
.env.example
```

for documented environment-variable names without real values.

Provider configuration should remain replaceable and must not be hard-coded into business logic.

---

## 12. Git Workflow

### Check Current State

```powershell
git status
```

Git commands should normally be run from the repository root.

### Stage Changes

```powershell
git add .
```

For focused changes, prefer staging specific files when practical.

### Review Before Commit

Before committing:

1. check `git status`
2. run targeted tests
3. run relevant quality checks
4. confirm no secrets or generated files are staged
5. update affected documentation

### Commit

Example:

```powershell
git commit -m "Implement agent message model"
```

Commit messages should describe the completed change, not the activity used to make it.

Prefer:

```text
Implement WebSocket message handling
```

over:

```text
Worked on WebSocket stuff
```

---

## 13. Commit Scope

Commits should be small enough to understand and revert.

Good examples:

```text
Define communication protocol
Implement agent core foundation
Add agent core unit tests
Configure Python project structure
```

Avoid mixing unrelated changes such as:

```text
Add memory system + redesign UI + update dependencies + fix unrelated bug
```

in one commit.

---

## 14. Documentation Rules

Project-level decisions belong in root documentation:

- `PROJECT.md`
- `ARCHITECTURE.md`
- `DESIGN.md`
- `ROADMAP.md`
- `TECH_STACK.md`
- `MVP_DESIGN.md`
- `THIRD_PARTY.md`

Detailed subsystem documentation belongs in:

```text
docs/
```

Examples:

- communication protocol
- memory design
- permission model
- event system
- plugin API

When implementation changes a documented contract, update the documentation in the same development stage.

---

## 15. Third-Party Code and References

Before copying or adapting external code:

1. identify the source repository
2. check its license
3. record the source in `THIRD_PARTY.md`
4. distinguish between:
   - architectural inspiration
   - adapted implementation
   - copied component
   - external runtime integration

Do not copy source code from a project merely because it is publicly visible.

---

## 16. AI-Assisted Development

AI tools are development assistants, not project owners.

When using Codex, Claude, GPT, or similar tools:

- provide project background documents
- state the exact modification scope
- identify architectural constraints
- require relevant targeted tests
- require local Git commits when appropriate
- do not ask them to redesign unrelated modules
- do not ask them to run the complete test suite by default

The project owner performs final integration review and full acceptance testing.

---

## 17. Error Handling and Logging

Avoid relying on raw `print()` statements for long-term application behavior.

Future application modules should use structured logging with appropriate levels:

```text
DEBUG
INFO
WARNING
ERROR
CRITICAL
```

Errors should preserve enough context for diagnosis without leaking secrets or sensitive user data.

External-service failures must be distinguishable from internal application failures.

---

## 18. Maintainability Principles

The project prioritizes:

- explicit module boundaries
- replaceable providers
- testable business logic
- documented contracts
- local-first operation
- permission-first actions
- backward-compatible evolution where practical
- clear migration paths for persistent data
- minimal hidden global state

Do not simplify architecture merely to reduce short-term implementation difficulty when doing so would create long-term coupling.

---

## 19. Definition of Done

A development task is complete when all relevant items are satisfied:

- implementation is finished
- relevant tests pass
- code-quality checks pass or known exceptions are documented
- architectural boundaries remain valid
- permissions remain correct
- documentation is updated when necessary
- no secrets or generated artifacts are committed
- Git commit accurately represents the change

---

## 20. Current Development Baseline

Phase 0 baseline (2026-09-08):

- Windows 11 primary environment
- C# WPF desktop layer
- .NET 8 Windows project target
- Python 3.11 Agent Core
- `pyproject.toml` as the Python project/build configuration
- pytest discovery under `src/agent_core/tests`
- Ruff and mypy integrated into normal development checks
- `pydantic-settings` runtime configuration with `.env` support
- console + rotating-file Python logging
- local WebSocket implemented for Desktop <-> Agent Core communication
- JSON message envelope implemented in both Python and C#
- protocol error isolation implemented for malformed input
- C# `IAgentConnection` transport abstraction implemented
- C# independent receive loop implemented for future proactive messages
- ConnectionProbe available for transport diagnostics
- WPF ViewModel + Application Service layering implemented
- real WPF <-> Python echo-Agent round trip verified
- SQLite remains planned as the first persistent database
- DeepSeek remains planned as the first cloud LLM provider
- provider abstraction is required before DeepSeek integration
- local-model support remains planned
- Git is the source of development history

Important distinction:

- Phase 0 cross-language runtime foundation is complete.
- The original AI MVP is not complete until a real LLM provider path is connected.

Context-recovery documents:

- `PROJECT_STATE.md`
- `docs/PHASE_0_CHECKPOINT.md`

This document should continue evolving with each major runtime phase.
