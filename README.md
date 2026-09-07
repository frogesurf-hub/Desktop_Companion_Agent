# Desktop Companion Agent

Desktop Companion Agent 是一个长期 Windows 桌面 AI 伴侣项目。

目标不是制作普通的问答聊天框，而是构建一个可以长期运行、理解桌面情境、拥有角色与记忆、能够主动决定是否互动，并在权限边界内帮助用户完成工作的桌面 Companion Runtime。

## Current Status

Phase 0: **Complete**

Current verified vertical slice:

```text
WPF UI
  -> ViewModel
  -> AgentClientService
  -> C# WebSocket client
  -> Python WebSocket server
  -> Agent Core
  -> response
  -> WPF UI
```

Current Agent behavior is still a stub:

```text
You: 你好
Agent: 收到你的消息: 你好
```

A real LLM provider is not connected yet.

See:

- `PROJECT_STATE.md`
- `docs/PHASE_0_CHECKPOINT.md`
- `ROADMAP.md`

## Architecture Direction

Long-term flow:

```text
Perception
  -> Events
  -> Situation Engine
  -> Attention Engine
  -> Behavior Engine
  -> Voice / Avatar / Tools
```

Core principles:

- proactive companion, not turn-based chatbot
- `Intent != Permission`
- local-first, cloud-enhanced
- real memory and fictional flavor remain separated
- stable interfaces / adapters between replaceable providers
- event-driven sensing instead of continuous screenshot streaming

## Technology Baseline

Desktop:

```text
C# WPF
.NET 8 Windows target
```

Agent Core:

```text
Python 3.11
```

Communication:

```text
Local WebSocket
JSON protocol
```

Current Python tooling:

- pytest
- Ruff
- mypy
- pydantic-settings
- websockets

## Repository Structure

```text
src/
├── agent_core/
│   ├── communication/
│   ├── config/
│   ├── core/
│   ├── observability/
│   ├── tests/
│   └── main.py
│
└── Desktop/
    └── DesktopCompanion.Desktop/

tools/
└── DesktopCompanion.ConnectionProbe/

docs/
├── COMMUNICATION_PROTOCOL.md
├── DEVELOPMENT.md
└── PHASE_0_CHECKPOINT.md
```

## Run the Phase 0 Runtime

### 1. Activate Python environment

From repository root on Windows PowerShell:

```powershell
.\.venv\Scripts\activate
```

For a fresh environment, install the project and development dependencies:

```powershell
pip install -e ".[dev]"
```

### 2. Start Agent Core

```powershell
python -m agent_core.main
```

Expected endpoint:

```text
ws://127.0.0.1:8765
```

The server remains running until stopped with `Ctrl + C`.

### 3. Start WPF Desktop

Run the `DesktopCompanion.Desktop` project from Visual Studio, or build from the project/solution environment.

In the current MVP UI:

1. click `Connect`
2. confirm status becomes `Connected`
3. type a message
4. click `Send`

### 4. Optional transport diagnostic

With Agent Core already running:

```powershell
dotnet run --project tools/DesktopCompanion.ConnectionProbe/DesktopCompanion.ConnectionProbe.csproj
```

The probe isolates C# / protocol / WebSocket behavior from WPF UI behavior.

## Development Rules

Normal change flow:

```text
Requirement
-> Design
-> Task Breakdown
-> Implementation
-> Targeted Tests
-> Quality Checks
-> Documentation Update
-> Git Review
-> Commit
```

Development AIs should run targeted tests for their changes, not the complete pytest suite by default. Full acceptance is reserved for the project owner.

## Current Non-Goals

Phase 0 does not yet implement:

- real LLM responses
- memory
- perception
- Situation Engine
- Attention Engine
- tools
- permission UI
- avatar
- voice
- local models

See `ROADMAP.md` for planned phases.
