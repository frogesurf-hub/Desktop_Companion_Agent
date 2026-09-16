# 开发协作与理解契约：开发轨道 × 理解轨道

> 项目：Desktop Companion Agent（桌面智能助手）
> 适用阶段：Phase 4 — Memory System 起，后续 Phase 默认继续沿用，除非项目 owner 明确修改。
> 目的：在不明显拖慢正式软件工程开发的前提下，让项目 owner 持续理解项目结构、设计理由、数据流与开发流程，避免协作退化为“复制代码 → pytest → diff → mypy → git”的机械执行。

---

## 1. 核心原则

从 Phase 4 开始，项目开发同时运行两条轨道：

```text
Development Track
开发轨道
    └─ 负责设计、实现、测试、审查、提交、验收

Understanding Track
理解轨道
    └─ 负责系统定位、概念解释、代码理解、设计推理、复盘
```

两条轨道并行推进。

理解轨道不能无意义拖慢开发轨道；开发轨道也不能以“开发效率”为理由完全跳过必要解释。

目标不是要求项目 owner 在每个 Task 前完全掌握相关软件工程理论，而是逐步达到：

```text
看到架构图
→ 知道数据大致怎么流动

看到一个类 / 文件
→ 知道它属于哪个模块、负责什么

看到一个 diff
→ 知道为什么修改这些文件

看到一个 ADR
→ 知道它正在解决什么设计问题

看到测试失败
→ 能大致定位是哪一层出了问题

面对一个设计选择
→ 能提出自己的方案，并理解规范方案为什么这样设计
```

---


## 1.1 理解轨道的内容预算

理解轨道默认采用“短、准、与当前 Task 直接相关”的原则。

对于普通 Task：

```text
Task 开始前的理解说明
→ 应控制在几分钟内可以读完的规模

Task 完成后的学习重点
→ 最多 1～3 个关键点

理论扩展
→ 只有项目 owner 主动要求，
  或确实影响当前实现时再深入
```

这里不是严格计时要求，而是限制解释规模。

禁止为了“遵守理解轨道”而把一个普通 Task 扩展成完整的软件工程课程。

例如：

```text
当前 Task 只需要理解 Repository
```

则默认只解释：

```text
Repository 是什么
它为什么在本项目中出现
不用它会带来什么问题
它在当前数据流中的位置
```

不默认展开完整 DDD、Clean Architecture 或数据库理论。

---

# 2. 每个 Task 开始前的固定说明

每个正式 Task 开始前，Assistant 必须先用简洁语言说明以下四件事：

## 2.1 这个 Task 是干什么的

说明：

- 当前 Task 要解决的问题；
- 最终要新增、改变或保证什么能力；
- 不展开不必要的实现细节。

示例：

```text
Task 4B 的目标：
给 Memory 增加持久化能力，使程序关闭并重新启动以后，
已经确认需要保存的记忆仍然存在。
```

## 2.2 它在整个系统里的位置

必须告诉项目 owner：

- 这个 Task 属于哪个模块；
- 上游是谁；
- 下游是谁；
- 它与 Character / Memory / Event / Agent / Provider 等已有模块是什么关系。

不能只给孤立类名。

## 2.3 数据从哪里来 → 到哪里去

每个 Task 至少给一条最小数据流。

例如：

```text
User Input
用户输入
    ↓
Memory Extraction
记忆提取
    ↓
Memory Repository
记忆存储
    ↓
Later Request
后续请求
    ↓
Memory Retrieval
记忆检索
    ↓
Prompt Context
提示词上下文
```

项目 owner 应优先理解“数据怎么走”，再理解具体类名。

## 2.4 做完后系统比之前多了什么能力

必须明确 Task 的增量。

例如：

```text
Task 前：
Memory 只能存在于当前进程中。

Task 后：
被确认保存的 Memory 可以跨程序重启存在。
```

禁止只说“新增了 Repository / Adapter / Service”等实现名词，而不说明能力变化。

---

# 3. Task 开始时的“先思考，再给规范方案”机制

如果当前 Task 适合让项目 owner 参与设计判断，Assistant 应在正式给出方案前，先提出一个范围有限的问题。

例如：

```text
[理解思考]

如果我们要让 Memory 可以更换 SQLite / JSON / 其他存储方式，
你觉得 Agent 应该直接调用 SQLite，还是中间再隔一层？
为什么？
```

项目 owner 可以回答：

```text
自己的方案
不确定
不会
直接给规范方案
```

其中：

```text
“不确定”
“不知道”
“不会”
“直接给规范方案”
```

都不得阻塞当前 Task。

当项目 owner 不确定时，Assistant 应按照成熟软件工程实践继续，并说明为什么采用该方案。

项目 owner 先回答自己的想法后，Assistant 随后需要：

1. 判断其中合理的部分；
2. 指出遗漏的约束；
3. 给出当前项目下更规范的设计；
4. 解释为什么这样设计；
5. 明确“这是通用原则”还是“只是当前项目的选择”。

不要为了教学故意设置刁钻问题。

问题应围绕当前 Task 真正存在的设计选择。

如果 Task 很机械、没有值得讨论的设计点，可以跳过提问，不强行互动。

## 3.1 区分“理解思考”和“Owner Decision”

Assistant 必须明确区分两类问题。

### [理解思考]

用于帮助项目 owner 理解设计。

例如：

```text
[理解思考]

你觉得 Agent 为什么不应该直接依赖 SQLite？
```

特点：

```text
回答正确或错误
→ 都不会自动改变项目正式架构

目的
→ 学习与理解
```

项目 owner 的猜测不能被自动记录为项目决策。

### [Owner Decision]

用于真正改变产品语义、需求或架构方向。

例如：

```text
[Owner Decision]

用户删除 Memory 后，
是否允许应用继续保留原始历史内容？
```

特点：

```text
回答
→ 会成为正式设计输入
→ 可能进入 ADR / Design / Requirements
```

Assistant 在提问前必须显式标记：

```text
[理解思考]
```

或：

```text
[Owner Decision]
```

避免项目 owner 无法判断“这是教学问题，还是我正在正式拍板”。

如果项目 owner 明确表示某个问题不会判断，可以直接说：

```text
不知道
不会
按成熟软件工程方案处理
```

Assistant 随后按照现有架构契约和成熟工程实践推进，并解释选择理由。

---

# 4. 新术语规则

任何重要的新软件工程术语第一次进入项目时，Assistant 需要回答四个问题：

```text
1. 它是什么？
2. 为什么当前项目需要它？
3. 如果不用它，会出现什么问题？
4. 当前需要掌握到什么程度？
```

例如：

```text
Repository

是什么：
统一的数据存取边界。

为什么需要：
Memory 逻辑不应该依赖具体 SQLite 实现。

不用会怎样：
业务逻辑与数据库耦合，
后续更换存储方式时需要大范围修改。

掌握等级：
A — Phase 4 必须理解。
```

后续再次出现时不需要反复长篇解释。

统一使用以下掌握等级：

```text
A. 必须理解
需要能够解释：
“它为什么存在、解决什么问题、位于哪一层。”

B. 应该认识
看到术语时知道大致用途，
不要求能够独立设计。

C. 暂时不用深入
只需要知道项目里哪里使用，
内部原理可以后置。
```

如果术语只是库内部细节、项目 owner 暂时不需要掌握，应明确标记：

```text
掌握等级：
C — 目前只需要知道用途，不要求记忆内部原理。
```

---

# 5. 架构图必须双语

后续提供给项目 owner 阅读的架构图，默认采用：

```text
English Technical Name
中文作用说明
```

例如：

```text
MemoryRepository
记忆仓库 / 定义记忆如何存取
        ↓
RetrievalService
记忆检索服务 / 决定当前请求需要哪些记忆
        ↓
PromptContextComposer
上下文组装器 / 把准备好的信息组成模型上下文
        ↓
Agent
智能体运行入口
```

要求：

- 保留真实英文类名 / 模块名，方便对应代码；
- 同时提供中文作用；
- 第一次出现缩写时解释；
- 不连续堆叠大量未解释的英文名词。

---

# 6. 每个 Task 的短代码定位

每个 Task 完成主要实现后，Assistant 必须进行一次简短的“代码定位”。

格式建议：

```text
这次主要涉及 4 个文件：

models.py
→ 定义“记忆长什么样”

repository.py
→ 定义“记忆怎么被存取”

sqlite_repository.py
→ SQLite 的具体存储实现

test_memory_repository.py
→ 验证存取契约是否成立
```

代码定位重点解释：

- 文件为什么存在；
- 文件在系统哪一层；
- 与其他文件是什么关系。

不要求项目 owner 逐行阅读整个 diff。

---

# 7. 重要 `.py` 文件附简短设计思路

当一个 Task 新增重要 `.py` 文件，或对重要 `.py` 文件进行结构性修改时，Assistant 应附上简短设计说明。

不是每个辅助文件都强制教学。

例如简单的：

```text
__init__.py
导出文件
```

如果没有新的重要设计意义，可以只在代码定位中一句带过。

对于重要文件，至少说明：

```text
文件职责：
它负责什么。

为什么单独放在这里：
为什么不直接写进其他类。

核心输入：
它接收什么。

核心输出：
它产生什么。

不负责什么：
明确边界。
```

示例：

```text
memory/repository.py

职责：
定义 Memory 的存取能力。

设计思路：
业务层只依赖这个契约，不依赖 SQLite。

输入：
MemoryRecord / 查询条件。

输出：
保存结果 / 查询出的 Memory。

不负责：
不判断某条记忆是否值得保存，
不负责把 Memory 拼进 Prompt。
```

说明保持简短。

复杂设计仍以正式设计文档 / ADR 为准。

---

# 8. 每个 Task 的关键代码学习点

每个 Task 不需要项目 owner 理解全部代码。

Assistant 应挑选最多 1～3 个最值得理解的点。

例如：

```text
本 Task 最值得看的两个地方：

1. Protocol 为什么放在 domain boundary。
2. SQLite 实现为什么依赖 Protocol，而 Agent 不依赖 SQLite。
```

必要时可以让项目 owner 先猜：

```text
[理解思考]

你觉得这里为什么不用直接 new SQLiteMemoryRepository() 写进 Agent？
```

然后再解释。

目标是学习设计思路，不是进行逐行代码讲解。

---

# 9. “我不会 / 我看不懂”中断机制

项目 owner 在开发过程中可以随时引用：

- 某个术语；
- 一段代码；
- 一张架构图；
- 某个命令；
- 某个测试；
- 某个设计结论；

并直接说明：

```text
这里不懂。
```

或提出具体问题。

此时执行以下流程：

```text
当前开发位置
    ↓
建立 Breakpoint
开发断点
    ↓
暂停当前推进
    ↓
解释问题
    ↓
确认问题已经解决
    ↓
返回 Breakpoint
继续原 Task
```

Assistant 必须明确记录：

```text
断点：
Task X / Step Y / 当前等待 Z
```

问题解决后必须从该断点继续。

禁止：

- 因解释问题跳到新的开发任务；
- 忘记原 Task；
- 重新从 Task 开头重复；
- 在没有必要时重做已经完成的工作。

---

# 10. 开发命令必须说明“为什么运行”

项目 owner 仍然会执行：

```text
pytest
Ruff
mypy
git diff
git diff --check
git status
git add
git commit
```

但 Assistant 不应只给命令。

首次或关键节点应简短说明目的。

例如：

```text
pytest
→ 验证行为是否符合预期。

Ruff
→ 检查代码规范和一部分静态问题。

mypy
→ 检查类型契约是否被破坏。

git diff
→ 人工确认到底改了什么。

git diff --check
→ 检查空白符等 diff 问题。

git status
→ 确认当前工作区状态。

git commit
→ 建立一个可恢复、可追踪的工程检查点。
```

后续重复运行时可简化，不必每次重新解释。

项目 owner 应逐渐理解这些步骤在软件工程流程中的作用，而不只是机械运行。

---

# 11. 测试失败时增加“定位解释”

如果 pytest / Ruff / mypy / 手动验收失败，Assistant 除了修复问题，还要简短说明：

```text
失败发生在哪一层？
为什么会失败？
它暴露的是实现问题、契约问题、测试问题还是环境问题？
```

例如：

```text
这是 Repository Contract 层的失败。

原因：
SQLite 实现允许重复 ID，
但 domain contract 规定 ID 必须唯一。

所以这里不是测试本身有问题，
而是实现违反了已经定义的契约。
```

---

# 12. Task 完成时的小复盘

每个 Task 完成后，增加一个非常短的理解复盘。

建议格式：

```text
Task X 你现在只需要带走 3 件事：

1. Repository 是存储边界。
2. Memory 业务逻辑不依赖 SQLite。
3. 测试验证的是 Repository Contract，而不只是某个函数。
```

控制篇幅，不重复完整开发过程。

---

# 13. Phase 4 结束时的完整学习复盘

Phase 4 正式完成并通过最终验收后，除了工程 Checkpoint，还必须单独做一次“Phase 4 理解复盘”。

复盘分为以下部分。

## 13.1 Phase 4 完成了什么

用非代码语言总结：

```text
Phase 4 开始前系统不会……
Phase 4 完成后系统可以……
```

## 13.2 用过的旧知识

列出此前 Phase 已经出现、Phase 4 再次使用的知识。

例如可能包括：

```text
Protocol
dataclass
async / await
dependency injection
composition root
EventBus
domain model
pytest
mypy
Git staged diff review
```

并说明这些旧知识在 Phase 4 中怎么被重新使用。

## 13.3 Phase 4 新知识

列出 Phase 4 首次真正进入项目的重要概念。

例如可能包括：

```text
Persistence
持久化

Repository
仓储 / 存取边界

Retrieval
检索

Retention
保留策略

Conflict Resolution
冲突处理

Memory Domain
记忆域
```

最终以真实 Phase 4 实现为准，不预先硬塞概念。

## 13.4 哪些知识项目 owner 应该掌握

分类：

```text
A. 必须理解
需要能解释它为什么存在。

B. 应该认识
看到以后知道大概作用。

C. 暂时不用深入
只需知道项目里哪里在使用。
```

防止所有术语都变成同等学习负担。

## 13.5 Phase 4 的明确开发流程

总结本 Phase 实际走过的软件工程流程，例如：

```text
恢复基线
    ↓
确认需求
    ↓
架构设计
    ↓
Architecture Review
    ↓
ADR
    ↓
Task Plan
    ↓
Contract
    ↓
Implementation
    ↓
Unit Tests
    ↓
Integration Tests
    ↓
Static Checks
    ↓
Diff Review
    ↓
Manual Acceptance
    ↓
Checkpoint
```

如果 Phase 4 实际流程发生变化，以真实过程为准。

需要解释每一步“为什么存在”。

## 13.6 Phase 4 最终系统数据流

用一张双语架构图总结 Phase 4 完成后的真实数据流。

项目 owner 应尝试自己解释一次：

```text
信息从哪里进入？
Memory 在哪里保存？
什么时候查询？
查询结果送到哪里？
Character 和 Memory 的边界在哪里？
```

Assistant 根据回答指出：

- 已理解部分；
- 理解偏差；
- 遗漏部分。

## 13.7 Phase 4 后的知识地图

最后生成：

```text
已经掌握
    ↓
正在形成理解
    ↓
Phase 5 会继续用到
```

帮助下一 Phase 衔接。

---

# 14. 开发轨道仍然保持严格工程要求

理解轨道不能降低项目工程标准。

仍然保持：

```text
Current Code
当前源码
    >
Current PROJECT_STATE / Phase Checkpoint
当前状态文档
    >
Current Architecture / Roadmap
当前架构与路线
    >
Historical Design Docs
历史设计文档
    >
Chat Memory
聊天记忆
```

继续执行：

- 先设计后实现；
- 重要架构决策写 ADR；
- 一个 Task 一个可审查增量；
- 测试先于“感觉正确”；
- pytest / Ruff / mypy 保持质量门；
- staged diff 必须人工审查；
- Git commit 作为真实工程检查点；
- 不根据聊天记忆猜当前源码；
- 不为了教学目的降低架构质量。

---

# 15. 理解轨道不能变成额外课程负担

本项目的理解方式采用：

```text
Just-in-Time Learning
即时学习
```

只解释当前 Task 真正需要理解的内容。

避免：

```text
为了理解一个 Repository
→ 先学完整 DDD
→ 再学 Clean Architecture
→ 再学数据库理论
→ 项目暂停数天
```

正确方式：

```text
当前 Task 需要 Repository
    ↓
只学 Repository 在本项目中的作用
    ↓
实现
    ↓
从真实代码中理解
    ↓
以后遇到更深问题再扩展
```

---

# 16. 项目 owner 的参与方式

项目 owner 不只是执行命令。

项目 owner 可以主动：

- 提出自己的架构猜想；
- 质疑设计；
- 要求解释术语；
- 要求比较两个方案；
- 引用不会的代码打断；
- 尝试预测下一步实现；
- 根据架构图复述数据流；
- 在 Task 前给出自己的实现思路。

错误答案不会影响正式开发。

Assistant 应区分：

```text
“你的思路可行，但不是当前项目最佳选择”

“这个思路违反了已有契约”

“这个方向正确，但漏掉了某些边界”

“这个问题目前没有唯一答案”
```

不能把项目 owner 的猜测自动当作开发决策。


当项目 owner 明确说：

```text
不知道
不会
这个点按成熟软件工程方案处理
```

Assistant 应继续推进，不要求 owner 为了学习而强行做出技术决策。

---

# 17. Assistant 的固定工作模式

从 Phase 4 开始，一个典型 Task 应尽量遵循：

```text
① Task 定位
   讲清四件事

② Owner 思考
   适合时使用 [理解思考]
   Owner 可以回答、不确定、不会或跳过

③ Owner Decision
   只有真正影响产品 / 架构时，
   才明确使用 [Owner Decision]

④ 规范方案
   给出正式设计，并指出遗漏约束

⑤ Implementation
   正常开发

⑥ Code Location
   短代码定位

⑦ Design Notes
   重要 .py 文件简述设计思路

⑧ Key Learning Points
   只挑 1～3 个关键代码点

⑨ Verification
   pytest / Ruff / mypy / diff / manual acceptance

⑩ Task Recap
   只保留本 Task 最重要的几个知识点
```

出现理解问题时：

```text
Task
 ↓
Breakpoint
 ↓
Explain
 ↓
Resolve
 ↓
Resume Task
```

---

# 18. 最终目标

这套协作方式的目标不是让项目 owner 在开发过程中同步成为资深软件架构师。

目标是随着 Desktop Companion Agent 一起成长：

```text
Phase 0
知道项目如何建立

Phase 1
知道不同模块如何通信

Phase 2
知道为什么需要事件边界

Phase 3
知道角色数据为什么需要独立建模

Phase 4
理解状态、记忆、存储与检索边界

后续 Phase
逐步理解 Situation / Attention / Perception / Behavior / Permission 等系统
```

最终项目 owner 应能理解：

```text
这个系统为什么被拆成这些模块，
信息为什么这样流动，
每个边界解决什么问题，
新增需求应该大致落在哪一层，
一个设计选择会影响哪些部分。
```

达到这一点后，项目 owner 就已经真正参与了软件工程设计，而不只是执行生成的代码和命令。

---

# 19. 契约优先级

本文件属于 Phase 4 起的“协作与学习流程补充契约”。

它不覆盖已有的：

- 架构边界；
- 安全原则；
- ADR；
- Phase Scope；
- Source Priority；
- 测试标准；
- Git 工作流；
- 项目 owner 最终决策权。

发生冲突时：

```text
正确性 / 安全 / 已接受架构契约
    >
Phase Scope
    >
正式工程流程
    >
本理解轨道契约
    >
教学便利性
```

理解机制用于帮助项目 owner 跟上开发，不得为了“更容易解释”而牺牲正确的工程设计。

## Source Checkpoint / 源码快照约定

为了保证长期开发、跨话题开发和上下文恢复时能够获得可靠的完整代码基线，
项目在重要开发里程碑建立 Source Checkpoint。

Source Checkpoint 以当前项目完整源码 ZIP 为主体。
必要时同时保存 Git Context 文本，用于记录当前 branch、HEAD、working tree 状态和近期提交历史。

### 需要建立 Checkpoint 的情况

以下情况默认建立新的 Source Checkpoint：

1. 一个具有明显结构性变化的 Task 完成并提交后，例如：
   - 新增新的核心子系统；
   - 新增或修改 Persistence / Protocol / Provider / Character / Memory 等架构层；
   - 新增较多源码文件或跨多个模块的大规模修改；
   - 新增重要 ADR、Migration 或基础设施。

2. 即将进入新的 Project Conversation / Phase / 大型开发阶段之前。

3. 当前完整源码与上一个 Source Checkpoint 已产生较大结构差异，且后续开发需要以新结构为基础时。

4. 每个 Phase 最终验收并提交完成后。

### 不需要建立 Checkpoint 的情况

以下情况通常不单独上传 ZIP：

- 小型 bug 修复；
- 少量测试补充；
- 单文件小范围修改；
- formatting / lint / typo 修复；
- 尚未完成或尚未 commit 的中间开发状态。

除非这些修改本身成为后续开发的重要恢复基线。

### Checkpoint 内容

源码快照建议命名：

`Desktop_Companion_Agent_phaseX_taskY_checkpoint.zip`

重要结构性 Checkpoint 可额外保存：

`PHASE_X_TASKY_GIT_CONTEXT.txt`

Git Context 至少包含：

- 当前 branch；
- 当前 HEAD commit；
- working tree 状态；
- 最近的 commit history。

完整 `.git` 目录不需要放入源码 ZIP。

### 协作责任

项目 owner 负责实际打包并上传 Source Checkpoint。

AI assistant 在判断当前开发已经达到需要建立 Checkpoint 的里程碑时，
应主动提醒项目 owner 上传最新 ZIP，并明确说明是否同时需要 Git Context。

Checkpoint 不是每个 Task 的机械步骤，而是由结构变化和上下文恢复价值决定。
