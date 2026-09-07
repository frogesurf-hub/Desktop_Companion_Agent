# Desktop Companion Agent Architecture

# 1. 总体架构

    Desktop Companion

    ├── Shell / Runtime
    ├── Character Core
    ├── Memory System
    ├── Internal State
    ├── Perception Layer
    ├── Situation Engine
    ├── Attention Engine
    ├── Behavior Engine
    ├── Permission Layer
    ├── Action Layer
    ├── Embodiment Layer
    ├── Provider Layer
    ├── Event Bus
    └── Persistence

------------------------------------------------------------------------

# 2. 数据流

    External World

    ↓

    Perception

    ↓

    Events

    ↓

    Situation Engine

    ↓

    Attention Engine

    ↓

    Behavior Engine

    ↓

    Avatar / Voice / Tools

------------------------------------------------------------------------

# 3. Character Core

负责角色长期定义。

包含：

-   Identity
-   Personality
-   Speech Style
-   Preferences
-   Core Values

原则：

角色可以有个性，但不能为了个性欺骗用户。

------------------------------------------------------------------------

# 4. Memory System

记忆必须分离：

    User Profile
    用户真实资料

    Working Context
    当前任务

    Episodic Memory
    真实经历

    Long-term Memory
    长期信息

    Relationship Memory
    关系历史

    Today Memory
    今日状态

    Fiction Memory
    临时虚构生活

禁止：

虚构记忆进入真实事实系统。

------------------------------------------------------------------------

# 5. Internal State

动态状态：

-   Mood
-   Energy
-   Curiosity
-   Social Desire
-   Relationship State
-   Daily State

区别：

    Character Core:
    她是谁

    Internal State:
    她现在怎样

------------------------------------------------------------------------

# 6. Perception Layer

负责观察：

-   当前窗口
-   当前软件
-   文件变化
-   系统状态
-   时间
-   天气
-   网络信息
-   屏幕视觉

只提供信息，不决定行为。

------------------------------------------------------------------------

# 7. Situation Engine

将低级事件转换为高级理解。

例如：

输入：

    Unity
    修改代码
    编译失败
    重新运行

输出：

    用户正在解决 Unity 问题

------------------------------------------------------------------------

# 8. Attention Engine

决定：

-   是否重要
-   是否需要提醒
-   是否重复
-   是否适合打扰

目标：

主动但不过度打扰。

------------------------------------------------------------------------

# 9. Behavior Engine

根据：

-   Personality
-   Mood
-   Relationship
-   Situation

决定：

-   说话
-   沉默
-   动作
-   表情
-   工具请求

------------------------------------------------------------------------

# 10. Permission Layer

核心原则：

    Intent != Permission

角色想做某事，不代表系统允许。

所有敏感操作经过权限层。

------------------------------------------------------------------------

# 11. Embodiment Layer

负责：

-   Live2D
-   VRM
-   3D
-   声音
-   动作
-   表情

上层输出语义：

    emotion: annoyed
    motion: look_away

底层负责实现。

------------------------------------------------------------------------

# 12. Event Bus

所有模块通过事件交流。

避免：

模块直接耦合。

------------------------------------------------------------------------

# 13. Provider / Adapter

所有外部能力可替换：

-   LLM
-   TTS
-   Vision
-   Memory
-   Avatar
-   Tools
-   App Adapter

------------------------------------------------------------------------

# 14. Local / Cloud

系统必须支持：

    Local Core

    +

    Optional Online Intelligence

云服务失败时可以降级。
