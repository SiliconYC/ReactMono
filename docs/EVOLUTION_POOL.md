# 定向进化候选池

> **本文件是所有候选方向的索引，不是任务清单或待执行承诺。** AI 负责自主维护本文件及 `proposals/` 下的提案。仅在通过评审后，才创建相应的 GitHub Issue。
>
> 目标路线图：[ROADMAP.md](ROADMAP.md)｜评审协议：[AUTONOMOUS_EVOLUTION.md](AUTONOMOUS_EVOLUTION.md)｜决策与实验：[EVOLUTION_LOG.md](EVOLUTION_LOG.md)

## 层级与职责

- **L0 永久目标**：交付真正好玩的简体中文游戏，并验证 AI 定向进化（产品边界由 [PROJECT_CHARTER.md](PROJECT_CHARTER.md) 锁定）。
- **L1 阶段目标**：P0–P5，由 [ROADMAP.md](ROADMAP.md) 维护。
- **L2 能力领域**：玩法、图形、经济、存档、部署、进化机制等，用提案主题归类。
- **L3 可交付功能**：经过评审后创建 Issue。
- **L4 原子实施任务**：必要时拆为子 Issue 或 PR 内任务。

同一领域可能跨多个阶段，勿机械把这些层级全部建成父子 Issue。

## 候选清单

| 编号 | 方向 | 阶段 | 状态 | 进入 Issue 的条件 |
| --- | --- | --- | --- | --- |
| [P001](proposals/P001-roadmap.md) | 六阶段目标与退出标准 | P0–P5 | 待评估 | 有明确缺失的当前阶段可验收工作 |
| [P002](proposals/P002-first-playable.md) | 第一局能玩到底的玩法边界 | P1 | 待评估 | 确立人数、地图、经济与验收的最小切片 |
| [P003](proposals/P003-local-pwa.md) | Pages / PWA / 本地存档 | P2（兼顾 P1） | 实现待评估 | 在既定纯本地约束下拆出可独立验证的切片 |
| [P004](proposals/P004-evolution-governance.md) | AI 发现、筛选、实施与独立验收 | 全阶段 | 治理原则已批准；效果待验证 | 可检验的工作流缺口或实验任务 |
| [P005](proposals/P005-classic-mechanics.md) | 经典玩法保留与再设计 | P1–P4 | 待评估 | 有明确价值和测试方法的当前阶段玩法切片 |

**状态词表**：待评估、研究中、延期、已否决、已晋升（注明 Issue）、已归档。已经确定的产品硬约束不是“待决定”；提案状态只指尚未解决的实施选择。每次改变状态须记录证据/原因和日期，防止越审越乱。

## 新方向怎样加入

1. 先核对 [ROADMAP.md](ROADMAP.md)、本池、现有 Issue 和近期 [EVOLUTION_LOG.md](EVOLUTION_LOG.md)，避免重复。
2. 小的观察可先在相关现有提案增加“观察/候选”，只有具有独立研究价值时才另建 `proposals/Pxxx-主题.md`，并给出下一稳定编号。
3. 每份提案至少写明：观察或证据、玩家/工程价值、影响阶段、可能方案、争议、验证办法、晋升条件、状态与关联 Issue/PR。
4. 筛选只产生四种结论：**晋升 Issue / 继续研究 / 延期 / 否决**。进入队列不得超过协议规定的容量，严重且确定的 Bug 可绕过候选研究阶段直接建 Issue，但要注明来源。
5. 实施完成或失败后回写原提案与 [EVOLUTION_LOG.md](EVOLUTION_LOG.md)。已证明为长期事实的决策，再同步产品宪章、路线图或 AGENTS。

## 当前执行入口

- [Issue #1：首轮自主规划](https://github.com/SiliconYC/ReactMono/issues/1) 是 P0→P1 的规划入口，不是“执行全部提案”的总任务。
- 当前**未因这五篇提案创建开发 Issue**；它们仅代表研究方向。
- 本池及 GitHub Issues/PR 均可由现有维护工具直接修改，无需使用 GitHub Discussions。
