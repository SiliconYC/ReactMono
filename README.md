# ReactMono · 大富翁仓库

一个以经典《大富翁4》为主要参考的浏览器回合制经营游戏，同时也是**AI 自主定向进化软件开发**的长期实验。

> **当前阶段：P1 工程验证版。** Issue #2 的 React+TypeScript 工程与初始规则契约已实现；还不能真正投骰、走格或完成对局，没有后台持续运行的自主 Agent。GitHub Pages 上仅发布工程测试页。

## 两个长期目标

1. **必须把游戏做出来。** 从可以完成整局的最小版本出发，逐步建设地图、角色、地产、经济、卡片、道具、股市、电脑对手、动画、音效等系统，最终形成完整、稳定、有趣、可持续改进的作品。
2. **尽可能验证 AI 定向进化。** 让 AI 在明确目标与验收约束下，自主审查项目、发现缺口、提出及创建 Issue、实现功能、测试、提交、审查、合并、总结，再发起下一轮改进；留下可以核验的过程记录。

第二个目标不能以牺牲第一个目标为代价。Issue 数量、提交次数、代码行数和代理运行时间均不代表游戏质量。

## 分支约定（必须遵守）

- **`dev` 是仓库的默认开发、集成和合并目标分支。**
- 除非仓库所有者明确要求，**禁止默认向 `main` 开发、提交、推送或合并。**
- 较大的功能可从 `dev` 创建短期分支，经独立验收后合并回 `dev`；小型文档调整可按任务要求直接提交 `dev`。
- 所有操作都应显式指定分支，不依赖工具可能变化的默认值。

## 产品方向

优先实现“**从新建游戏开始，能够正常玩到分出胜负**”的闭环，而不是一开始堆砌大量菜单和演示动画。

- 基础游戏：地图与格子、回合/骰子/移动、购买与收租、资金与资产、破产及胜利条件。
- 核心扩展：地产升级、特殊地块、卡片与道具、股票、随机事件、电脑玩家和可选规则。
- 体验质量：可理解的界面、稳定动画、合理游戏节奏、音效、可访问性及跨设备适配。
- 数据与存档：新建游戏、多存档位、读档、自动保存及手动导入/导出存档。
- **产品硬约束**：只部署纯静态 GitHub Pages，可用 PWA 离线运行；不做账户登录、不做云存档或跨设备自动同步，不依赖游戏后端。
- **界面硬约束**：从第一版起，游戏内所有用户可见内容均为**简体中文**；早期不做英文版和多语言系统。
- 逐渐完善玩法和美术；与原作有关的受版权保护素材须确认授权或使用原创替代。

具体优先级由实际缺陷、玩家价值和自主规划决定；不得把上述清单当作无需讨论的固定开发顺序。

## 建议的技术边界（尚未落地）

- React + TypeScript：界面；PixiJS：地图与角色渲染（可在初始技术验证后调整）。
- 独立于 React 的确定性游戏逻辑层：规则、状态、事件及可重复的模拟。
- 自动化测试：单元/规则、端到端、批量模拟对局与界面回归。
- 确定使用 GitHub Pages 静态部署及 PWA 离线运行；IndexedDB 本地存档，支持文件备份，不建设用户系统或跨设备自动同步。

技术选型不是最终决定，变更需说明理由和验收证据。

## 阶段路线图

P0 目标与治理 → P1 第一局能玩到底 → P2 可靠的准本地游戏（含 Pages/PWA/存档）→ P3 丰富核心玩法 → P4 高完成度正式版 → P5 长期自主进化。**自主进化实验贯穿所有阶段，并非 P5 才开始。** 每阶段都有明确退出验收，详见 [路线图](docs/ROADMAP.md)。

## 第一轮实际执行任务

[Issue #1](https://github.com/SiliconYC/ReactMono/issues/1) 负责从提案池筛选 P1 任务，其规划产物是：

1. [#2 工程骨架与状态契约](https://github.com/SiliconYC/ReactMono/issues/2) → [#3 地图和回合](https://github.com/SiliconYC/ReactMono/issues/3) → [#4 地产经济和胜负](https://github.com/SiliconYC/ReactMono/issues/4)。
2. [#5 基础电脑与 100 种固定种子模拟](https://github.com/SiliconYC/ReactMono/issues/5) 依赖 #3/#4。
3. [#6 简体中文 UI 和真实浏览器完整对局](https://github.com/SiliconYC/ReactMono/issues/6) 可在 #2 完成后着手显示层，正式集成需 #3/#4/#5。

不要把“已经创建 Issue”冒充“已经开发或验收完成”。P1 详细边界参见 [P002 研究与晋升结果](docs/proposals/P002-first-playable.md)。

## 工程测试地址

- [GitHub Pages 工程验证版](https://siliconyc.github.io/ReactMono/)（不是完整可玩游戏）。
- [Pages 自动部署成功记录](https://github.com/SiliconYC/ReactMono/actions/runs/38749060304)：由独立 `gh-pages` 分支发布，源码仍以 `dev` 为唯一默认开发/集成目标。
- [Issue #2 的测试、构建与局限](docs/ISSUE2_IMPLEMENTATION.md)：P1 阶段暂用 React CDN，**尚不支持断网运行**；P2 必须打包本地依赖才能实现 PWA。

## 协作入口

- [六阶段路线图](docs/ROADMAP.md)
- [定向进化候选池（讨论与研究入口）](docs/EVOLUTION_POOL.md)
- [首批五份独立提案](docs/proposals/)
- [决策与实验记录](docs/EVOLUTION_LOG.md)
- [项目目标与验收边界](docs/PROJECT_CHARTER.md)
- [AI 自主定向进化流程](docs/AUTONOMOUS_EVOLUTION.md)
- [GitHub Pages 与存档架构评估](docs/DEPLOYMENT_ASSESSMENT.md)
- [AI Agent 必读约定](AGENTS.md)
- [Issues（只用于经筛选的可执行任务）](https://github.com/SiliconYC/ReactMono/issues)

**协作机制**：探索性意见与长期改进假设统一落在 Git 管理的 Markdown 提案中；由 AI 自行维护、去重和评审，不依赖 GitHub Discussions。严重且明确的缺陷允许直接开 Issue。

**初始化不等于自主代理已经在后台运行。** 持续的自动调度和执行环境必须在后续阶段单独部署、验证和启用。
