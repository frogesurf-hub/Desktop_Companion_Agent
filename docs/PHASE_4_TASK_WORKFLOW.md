# Desktop Companion Agent

# Phase 4 Task Workflow & Recovery Context

Status: Active\
Phase: 4 Memory System

------------------------------------------------------------------------

# 1. Current Phase Status

## Completed Tasks

### Task 0 --- Memory Architecture ADR / Design

目标： - 定义 Memory System 长期架构 - 明确 Memory 生命周期 - 明确
Memory Domain - 明确 Revision / Source of Truth

状态：Completed

------------------------------------------------------------------------

### Task 1 --- Memory Domain Models

目标： 建立 Memory 基础领域模型。

包含： - Memory - MemoryRevision - MemoryDomain - MemorySource

状态：Completed

------------------------------------------------------------------------

### Task 2 --- Persistence Contract + Implementation

目标： 建立 Memory 持久化层。

包含： - Repository Contract - SQLite Repository - Database Migration

状态：Completed

------------------------------------------------------------------------

### Task 3 --- Memory Governance Core

目标： 提供 Memory 管理能力。

包含： - list - inspect - edit - delete - history

状态：Completed

------------------------------------------------------------------------

### Task 4 --- Retention + Conflict Semantics

目标： 定义 Memory 生命周期管理。

包含： - retention policy - conflict detection - conflict resolution
semantics

状态：Completed

------------------------------------------------------------------------

### Task 5 --- Retrieval + PreparedMemoryContext

目标： 建立 Memory Retrieval Pipeline。

数据流：

Repository\
↓\
RetrievalService\
↓\
PreparedMemoryContext\
↓\
Agent Context

包含： - RetrievalPolicy - RetrievalLimits - MemoryRetrievalService -
PreparedMemoryContext

状态：Completed

------------------------------------------------------------------------

# 2. Development Rules

## Rule 1 --- Task 定位优先

每个 Task 开始前必须明确：

-   Task 目标
-   所处架构位置
-   输入
-   输出
-   数据流
-   完成后的能力

禁止直接进入代码实现。

------------------------------------------------------------------------

## Rule 2 --- 基于现有代码开发

必须先查看：

-   repository
-   models
-   contracts
-   tests
-   architecture docs

禁止假设不存在的模块。

禁止重新设计已经冻结的架构。

------------------------------------------------------------------------

## Rule 3 --- Decision Layer 与 Implementation Layer 分离

设计阶段：

确定： - 是否需要 - 为什么需要 - 数据如何流动

实现阶段：

确定： - class - function - file

------------------------------------------------------------------------

## Rule 4 --- 标准开发流程

每个 Task：

1.  Design discussion
2.  Implementation
3.  Targeted pytest
4.  Ruff
5.  Mypy
6.  git diff --check
7.  Working diff review
8.  Commit

------------------------------------------------------------------------

## Rule 5 --- Breakpoint 机制

出现以下情况：

-   上下文过长
-   架构理解偏差
-   当前代码状态不明确

停止开发。

恢复流程：

Task\
↓\
Breakpoint\
↓\
问题解释\
↓\
回到正确位置

------------------------------------------------------------------------

# 3. Phase 4 Remaining Tasks

# Task 6 --- Agent + Composer Integration

目标：

让 Memory 正式进入 Agent Runtime。

当前状态：

Memory：

Repository\
↓\
Retrieval\
↓\
PreparedMemoryContext

但是 Agent 尚未消费 Memory。

需要完成：

User Input

↓

Agent Runtime

↓

Memory Retrieval

↓

PreparedMemoryContext

↓

Context Composer

↓

LLM Prompt

核心问题：

-   谁负责获取 Memory？
-   谁负责组合 Context？
-   Memory 如何注入 Prompt？
-   如何防止 Memory 污染 Agent？

原则：

Memory 提供上下文，不直接控制 Agent 行为。

------------------------------------------------------------------------

# Task 7 --- Automatic Learning Pipeline

目标：

研究 Agent 如何产生新的 Memory。

流程：

Conversation

↓

Candidate Memory

↓

Validation

↓

Store

需要定义：

-   什么内容值得保存
-   什么内容应该丢弃
-   如何避免垃圾 Memory

------------------------------------------------------------------------

# Task 8 --- Memory Failure Isolation

目标：

Memory 异常不能影响 Agent 主流程。

例如：

Database failure

↓

Memory unavailable

↓

Agent continues

需要：

-   fallback
-   isolation boundary
-   error contract

------------------------------------------------------------------------

# Task 9 --- WebSocket Memory Management Protocol

目标：

让桌面端能够管理 Memory。

包括：

-   query
-   update
-   delete
-   inspect

------------------------------------------------------------------------

# Task 10 --- Simple WPF Memory UI

目标：

提供基础 Memory 管理界面。

包含：

-   Memory list
-   Detail view
-   Delete
-   Edit

------------------------------------------------------------------------

# Task 11 --- Runtime Acceptance

验证完整链路：

WPF

↓

Agent

↓

Memory

↓

Provider

↓

Response

检查：

-   正常流程
-   Memory 注入
-   Failure handling

------------------------------------------------------------------------

# Task 12 --- Phase 4 Documentation

整理：

-   Architecture
-   ADR
-   Task summary
-   Lessons learned

更新：

-   PROJECT_STATE.md
-   ROADMAP.md

------------------------------------------------------------------------

# 4. Architecture Boundary

当前架构：

Desktop Client

↓

WebSocket

↓

Agent Core

↓

Memory System

↓

Provider Layer

↓

LLM

Memory 负责：

-   保存事实
-   提供上下文
-   辅助 Agent

Memory 不负责：

-   决策
-   控制 Agent 行为
-   修改自身规则

------------------------------------------------------------------------

# 5. Next Starting Point

下一任务：

Task 6

开始前必须确认：

1.  当前 Agent Core 结构
2.  Composer 当前实现
3.  Context 生成流程
4.  Memory 注入位置

然后进入设计。

禁止直接修改代码。
