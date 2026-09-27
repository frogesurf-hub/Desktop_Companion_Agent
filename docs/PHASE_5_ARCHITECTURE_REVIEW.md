# Phase 5 — Architecture Review

Date: 2026-09-27 (Asia/Shanghai)

Status: Assistant source/design review and owner-supplied staged-diff review complete.
This is not an independent review, a runtime test report, or implementation acceptance.

Reviewed baseline: `75a7e5c3f1aad119189be6b18265dcea46966b2b`.
Reviewed proposal: `PHASE_5_SITUATION_ENGINE_DESIGN.md`.

## 1. Review objective

在写代码前检查：当前源码能否支持设计、责任是否越界、失败语义是否真实、
本阶段验收能否证明宣称的能力。审查发现先返回设计修正，再冻结任务顺序。

## 2. Source evidence

| 当前源码／契约 | 已确认事实 | 设计响应 |
| --- | --- | --- |
| core/agent.py | 没有业务 EventPublisher 依赖 | 在显式聊天边界增加观察适配器，保持 Agent 主路径 |
| core/message_router.py | 只路由 chat / memory.* | 只装饰 chat_processor，不改 memory 路由 |
| core/message.py | Message.id 为 str，不保证 UUID 校验 | 使用 Core 新生成 invocation UUID，不强制转换客户端 ID |
| events/models.py | RuntimeEvent 不可变，UTC 时间、UUID 元数据 | 明确两个输入事实类型和一个变化类型 |
| events/bus.py | NEW 状态静态订阅；exact-type 路由 | main.py 在 start 之前注册具体事件类型 |
| events/bus.py / ADR 0012 | 满队列立即拒绝 | 无阻塞重试；记录投递失败与健康状态 |
| events/bus.py | close 先进入 CLOSING，再排空 accepted Events | 排空中派生发布可失败，不能承诺图级排空 |
| events/bus.py | 同一 Event 的兄弟订阅者并发 | 无兄弟执行顺序依赖；本模块状态修改串行化 |
| temporal/clock.py | Clock 返回 aware datetime | 复用 Clock，测试可控时间 |
| memory/retrieval.py | PreparedMemoryContext 为分域字符串元组 | 当前两条规则不需要它，不发明假证据来源 |
| main.py | 创建并启动 EventBus，无业务订阅 | 增加实际装配及装配验收，而非只测孤立 engine |
| ADR 0019 | 情境是未来决策输入，Permission 独立 | 不实现提醒、重试、Provider 路由或行为准入 |

Source links are relative to repository baseline:

- `../src/agent_core/core/agent.py`
- `../src/agent_core/core/message_router.py`
- `../src/agent_core/core/message.py`
- `../src/agent_core/events/bus.py`
- `../src/agent_core/main.py`
- `adr/0010-events-are-facts-commands-remain-explicit-boundaries.md`
- `adr/0011-async-bounded-in-process-event-bus.md`
- `adr/0012-fail-fast-event-bus-overload-admission.md`
- `adr/0019-adaptive-runtime-behavior-decision-and-capability-boundaries.md`
- `adr/0021-explicit-runtime-routing-for-request-response-capabilities.md`

## 3. Findings resolved in the proposal

### R1 — Input capability did not exist

风险：把 Unity 示例或既有 EventBus 误当作已经存在的事实生产能力。
处理：选择两个由当前聊天运行时提供事实的场景，单独安排观察适配器。
验证归属：Task 5 生产装配与 Task 6 真实运行时验收。

### R2 — Derived event delivery could be mistaken for state success

风险：队列满或关闭期间发布失败，被 EventBus 的 subscriber 隔离日志吞成普通失败。
处理：情境状态与通知分离；显式处理非接纳，记录 notification health。
验证归属：Task 4 过载、关闭中派生发布及版本测试。

### R3 — Repetition expiry was easy to calculate incorrectly

风险：3 条失败里较早两条已过期，仍因最后一条尚未过期保留“重复失败”。
处理：按第三新失败的截止时刻计算阈值保持时间，并持续重新评估。
验证归属：Task 3 的窗口边界反例。

### R4 — Delayed facts could resurrect resolved situations

风险：旧失败晚于成功到达，引擎按接收顺序重新输出故障情境。
处理：保留成功时间下界，按发生时间判断；同一时间戳保守处理。
验证归属：Task 3 乱序及同时间戳用例。

### R5 — An empty result could hide failure

风险：规则崩溃、证据容量耗尽与正常未匹配都变成相同的空列表。
处理：查询返回 capability health；受影响状态不冒充有效。
验证归属：Task 3 容量及 Task 4 故障隔离。

### R6 — Diagnostics could pull forward a protocol/UI project

风险：为了“能检查”提前增加 WebSocket family、WPF 页和服务器推送桥。
处理：显式查询在同进程验收；真实 WPF 运行通过安全生命周期日志观察。
验证归属：Task 5 确认 Reader 与订阅者共享实例，Task 6 区分不同证据层级。

### R7 — Understanding questions could become an artificial gate

风险：项目 owner 必须先答教学题，才能继续已授权工程工作。
处理：协作契约增加简短补充，工程流程优先；真正产品语义变化才使用 Owner Decision。

## 4. Accepted limitations of this proposed scope

- 首版只能识别已列出的两类运行时情境，尚不能识别桌面工作内容或 Unity 调试。
- EventBus 瞬时投递可能丢失未被接纳的事实，情境只反映实际收到的证据。
- 不向用户主动发话，也不把情境写入 Memory 或 Prompt。
- 同进程查询不是新的跨进程协议；没有 Situation WPF 页面。
- 规则阈值是工程初始值，不是经验测量得出的普适值。
- 进程重启清空所有临时情境。

## 5. Remaining implementation gates

1. Task 2 冻结具体领域字段、错误类型与 capability 方法签名。
2. Task 3 明确所有辅助数据结构的回收，不能只有主列表 bounded。
3. Task 4 验证串行化、维护任务取消、通知失败与查询一致性。
4. Task 5 必须读届时最新 main.py 后修改装配，保留已有清理保证。
5. Task 6 提供实际运行证据，不以当前文档内的历史 355 passed 代替新结果。

## 6. Disposition

未发现必须在编码前重设计 EventBus、Memory、Provider 或 Router 的理由。
设计基线与 ADR 0022 / 0023 已记录为 Accepted。
Task 1 的 Git 检查点由包含本文的 commit 及其远程同步证明；进入 Task 2 前应核对它。
