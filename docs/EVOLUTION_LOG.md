# 定向进化决策与实验记录

> 记录**真实发生的决策、实验、接受/拒绝和失败证据**。不把文档调整算成已完成自主游戏开发轮次，不伪造测试成绩。

## 治理决策

### 2026-10-15｜G001：讨论载体改为仓库内提案池

- **背景**：原规划让 GitHub Discussions 承担探索讨论，Issue 只负责成熟任务。仓库已启用 Discussions，但当前承担维护工作的 GitHub 连接缺少可靠的创建/修改 Discussion 能力。
- **人类决定**：改用仓库内 Markdown 提案池，保留与 Issue 分层的理念，不要求用户手动维护论坛。
- **实施方式**：[EVOLUTION_POOL.md](EVOLUTION_POOL.md) + `proposals/Pxxx-*.md` + 本日志；只把经过筛选的可执行事项晋升到 GitHub Issue，PR 与验证记录作为执行证据。
- **理由**：读写与历史记录可以使用现有 GitHub 文件操作完成；避免提案停留在不可维护的外部系统。
- **取舍**：放弃论坛式嵌套评论，改用文件变更记录意见与证据。仍可保留 GitHub Discussions 功能，但自主工作流不得依赖它。
- **关联**：[P004](proposals/P004-evolution-governance.md)、[Issue #1](https://github.com/SiliconYC/ReactMono/issues/1)。

### 2026-10-15｜G002：Issue #1 首次自主任务筛选与晋升

- **输入基线**：`dev`（规划前提交 `391799a84ee8eb734c1b6f70ed3355514ccc39b4`）只有 Markdown 文档、提案与 Issue #1，没有游戏代码；经过搜索不存在其他重复的开发 Issue。
- **评审对象**：P001–P005。P001 六阶段目标已成为 ROADMAP 基线；P002 的最小可玩缺口明确、可分割验证，批准晋升；P003 静态部署/PWA/完整存档延期 P2；P004 的管理规则已落地但尚未用开发证实；P005 股市、卡片和多地图等复杂内容延期。
- **实际晋升**：[#2 工程状态契约](https://github.com/SiliconYC/ReactMono/issues/2)、[#3 棋盘回合](https://github.com/SiliconYC/ReactMono/issues/3)、[#4 地产经济与胜负](https://github.com/SiliconYC/ReactMono/issues/4)、[#5 电脑玩家和 100 个种子模拟](https://github.com/SiliconYC/ReactMono/issues/5)、[#6 简体中文 UI 与浏览器整局](https://github.com/SiliconYC/ReactMono/issues/6)。
- **路径依赖**：#2→#3→#4→#5；#6 的显示层可在 #2 后启动，但集成/验收依赖 #3/#4/#5。不可无序并行改动共享规则核心。
- **决策理由**：选择一名人类玩家加一名电脑玩家，24 格封闭棋盘，2 人初始现金相同，简化租金破产和最多 60 个完整轮次。仅 P1 必需范围晋升；所有硬约束（仅简体中文、纯浏览器、`dev`）保持不变。详细规则与验收 [见 P002](proposals/P002-first-playable.md)。
- **结果**：本轮**完成文档层规划与 Issue 创建**；还没有代码提交、游戏构建、真实对局、PR/独立验收，更没有连续自主进化。不要把五条 Issue 统计为五次成功改进。
- **后续入口**：先实施 [#2](https://github.com/SiliconYC/ReactMono/issues/2)，经独立验收后开启依赖任务；每完成一轮回写本日志。

## 自主改进实验账本

**当前尚无经验证的自主游戏改进轮次。** 后续每轮至少记录：

| 轮次 | 来源提案/Issue | PR/提交 | 目标与测试证据 | 独立验收 | 回归/回滚 | 成本与人工介入 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| （尚无） | — | — | — | — | — | — | — |

每轮出现失败也要登记：失败原因、复现方法、下一步实验以及是否停止；不得只记录成功，不得用提交数量冒充玩家体验的提升。
