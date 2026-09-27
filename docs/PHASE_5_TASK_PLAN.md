# Phase 5 — Situation Engine Task Plan

Date: 2026-09-27

Status: Accepted task plan; implementation not started.

Implementation baseline: `75a7e5c3f1aad119189be6b18265dcea46966b2b`.

## 1. Planning rules

先定义情境与失败语义，再写契约、规则、事件适配和运行时装配。
每个 Task 是独立可审查增量；目标验证通过并完成 diff review 后 commit + push。
不得把多个未完成 Task 混成一次难审查的大提交。

Task 前短说明：目标、所属层、最小数据流、新增能力。
理解说明围绕当下设计理由，最多选 1–3 个重点，不以教学问答阻塞工程流程。

Owner 负责本地修改、实际验证、staged diff review、commit/push。
Assistant 负责读当前源码、设计与代码建议、检查证据及判断验收是否充分。
当前工具只读 GitHub；不声称已替 Owner 修改或提交远程仓库。

## 2. Dependency order

| Task | 目标与位置 | 主要产物 | 验收门 |
| --- | --- | --- | --- |
| 1 | 把 Phase 5 概念转成可实现的范围与设计 | Design、Architecture Review、ADR 0022/0023、Task Plan、状态／协作契约同步 | Owner 文档及 diff review、git diff --check、commit/push |
| 2 | 定义事实与情境的公共契约 | situation 领域模型、输入事实、变化通知、Reader／错误契约 | 模型不变量与无效输入定向测试、Ruff/mypy |
| 3 | 根据固定事实与时间得到确定性情境 | 两条规则、有界证据、身份／版本／生命周期 | 时间、乱序、重复、容量、成功解除等正反例测试 |
| 4 | 接入 EventBus 与显式查询 | subscriber 适配、串行状态边界、健康／通知、过期维护 | 真实 EventBus 集成、满队列、关闭、取消、日志安全 |
| 5 | 将已测组件接入实际 Core | 聊天观察适配器、main.py 装配、安全诊断日志 | 原聊天响应等价、memory 路由不受影响、实际装配及清理测试 |
| 6 | 验证整体能力与旧功能回归 | deterministic 综合验收和真实运行记录 | 完整 pytest/Ruff/mypy、Desktop build、WPF/Core 手动场景、日志复查 |
| 7 | 使当前文档与验收后的源码一致 | State/Architecture/Roadmap、Checkpoint、Learning Review | 无实现夸大、已知限制明确、diff review、commit/push |

## 3. Task 1 — Design and review

增量：从“准备做 Situation”变为“有明确输入、输出、生命周期和失败契约”。

文档顺序：

1. 收录已确认的首版方向及协作偏好。
2. 读取最新代码与既有 ADR。
3. 形成 Situation Design。
4. 做架构自审，修正发现的问题。
5. 形成 Proposed ADR。
6. 根据依赖链拆 Task。
7. 基于 Owner 已确认的范围与完整 staged diff，由 Assistant 完成技术审查，记录 ADR Accepted 日期。
8. 检查工作 diff、显式 staging、检查 staged diff、commit、push。

本 Task 仅文档变更，无新运行时测试要求，不重复已有 355 项测试充当设计验收。
本轮交付阶段不能将 Task 1 记为已提交完成。

## 4. Task 2 — Contract first

建议文件定位（在 Task 启动时对照最新仓库确定最终文件数）：

- `src/agent_core/situation/models.py`：情境、证据和生命周期。
- `src/agent_core/situation/events.py`：两个输入事实及一个变化通知。
- `src/agent_core/situation/contracts.py`：显式查询／评估能力及结果。
- `src/agent_core/situation/errors.py`：安全 capability 错误。
- 对应测试与包导出。

先让领域模型能够拒绝无时区时间、无效窗口、非法版本和超限证据。
不在这一 Task 改 main.py 或调用 Provider。

能力变化：其他组件可以在类型层面明确地交换 Situation 信息。

## 5. Task 3 — Deterministic interpretation

实现输入事实 → 有界聚合 → 规则判断 → 生命周期变化。

必测反例：

- 第 2 次失败不能提前触发；同 invocation 不重复计数。
- 第三新失败过期后，不能因最新失败尚在窗口内就继续满足阈值。
- 晚到旧失败不能推翻较新的成功；相同时间戳采用保守顺序。
- 查询时不能返回过期状态；时钟回退不能复活旧状态。
- 容量退化与正常空结果有区别；各辅助索引和缓存同样有界。

首版阈值是可注入的工程默认值，不当作现实普适规律。
能力变化：固定事实和时间可以重现相同的语义判断与过期结果。

## 6. Task 4 — Event integration and lifecycle

使用真实 EventBus 测试，不只 mock publish。
至少安排满队列、正在关闭时处理输入产生输出、兄弟订阅者失败、外部取消场景。

Reader 和订阅者共享单个 SituationRuntime；查询与更新不产生不一致快照。
通知失败只影响 delivery health，不回滚有效状态。
维护任务停止后没有孤立任务；原 EventBus 语义不变。

能力变化：内部情境可随事件变化、可被显式读取、可有界关闭。

## 7. Task 5 — Production composition

观察适配器基于现有 MessageProcessor 能力包装 chat 路径，不让 Agent 变成 EventBus owner。
观察事实不得携带原始聊天正文；临时失败 outcome 从安全协议代码映射。
对异常／取消保持原有传播；观察入队失败不能摧毁原有效响应。

main.py 启动前注册静态订阅，创建维护任务，并明确 stop/drain/cleanup 顺序。
保留 memory.* 路由和 Provider 关闭保护。

真实运行由安全日志确认事实被处理、情境建立及过期。
显式查询通过同进程集成验收验证；不增加 WebSocket 协议或 WPF 页面。

能力变化：已验证的 Situation 从测试组件进入实际 Core 装配。

## 8. Task 6 — Acceptance matrix

| 编号 | 场景 | 证据形式 |
| --- | --- | --- |
| A | WPF 发起普通聊天，建立近期交互情境并正常响应 | 真实 WPF/Core 日志与响应记录 |
| B | 受控 3 次临时失败形成情境，成功解除 | FakeProvider 或受控 processor 的真实组件集成测试 |
| C | 正常过期、无输入时维护、Reader 新鲜度 | 可控时间测试；真实维护日志 |
| D | 不同调用、重复、乱序、旧成功／失败 | 确定性规则测试 |
| E | 满队列和关闭时派生发布失败 | 真实 EventBus 生命周期测试 |
| F | 无正文／密钥／原始异常泄露 | 自动日志回归与真实日志复查 |
| G | 聊天与 Memory 既有功能 | 完整 Python 门；必要的 WPF Memory 操作回归 |
| H | 生产装配及资源回收 | main 装配测试、真实启动／关闭、Desktop build |

真实 Provider 不需要为证明失败规则而故意触发凭据错误或耗尽配额。
区分 FakeProvider 证据、真实 EventBus 集成证据与真实 WPF/Provider 验收，不能相互冒充。
测试数量以实际运行结果为准，不预设新的总数。

## 9. Task 7 — Closure

记录实际实现、验证结果、已知限制及后续 Attention 接入点。
历史 Phase 4 Checkpoint 不回写成 Phase 5 状态；Phase 4 学习复盘 Pending 标记不得凭空改完。
Owner 理解复盘可在不影响工程验收的情况下进行。

## 10. Current breakpoint

Phase 5 / Task 2 / contract design next, after confirming the Task 1 containing
commit and clean working tree. Task 1 scope and technical design were reviewed;
this plan itself does not claim Situation implementation or new test results.
