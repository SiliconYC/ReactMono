# ReactMono · 大富翁仓库

一个以经典《大富翁4》为主要参考的浏览器回合制经营游戏，同时也是**AI 自主定向进化软件开发**的长期实验。

> **当前状态（2026-10-18）：主程序入口已换为低多边形 3D 棋盘，并连接原有多人、AI、存档和 PWA 回合系统；正式版综合验收 #73 仍开放。** 正式入口已接入停留格地产操作、街区联排、银行存取款和银行账户股票交易。主程序采用全屏 3D 游戏布局，桌面本机可以进行实际对局；完整跨视口、离线、独立及远程验收仍待完成，不宣称 P4 已完成。

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

## 当前技术架构

- React 18 + TypeScript 本地静态构建；纯规则引擎不依赖 React 或后端。
- Node 内置测试框架进行规则、100 种子模拟与存档迁移回归；Playwright/Chromium 进行真实浏览器验收。
- GitHub Pages 静态发布；PWA 缓存离线运行，IndexedDB 本地多存档与 JSON 文件备份。
- P3 #30 将规则类型、配置、随机数、地产、回合、卡片分为独立模块，但公共入口仍为 `src/core/game.ts`；模块化完成状态以合并后的验收记录为准。
- 尚未引入 PixiJS、服务器、登录或云同步。

## 阶段路线图

P0 目标与治理 → P1 第一局能玩到底 → P2 可靠的准本地游戏（含 Pages/PWA/存档）→ P3 丰富核心玩法 → P4 高完成度正式版 → P5 长期自主进化。**自主进化实验贯穿所有阶段，并非 P5 才开始。** 每阶段都有明确退出验收，详见 [路线图](docs/ROADMAP.md)。

## 第一轮实际执行任务

[Issue #1](https://github.com/SiliconYC/ReactMono/issues/1) 负责从提案池筛选 P1 任务，其规划产物是：

1. [#2 工程骨架与状态契约](https://github.com/SiliconYC/ReactMono/issues/2) → [#3 地图和回合](https://github.com/SiliconYC/ReactMono/issues/3) → [#4 地产经济和胜负](https://github.com/SiliconYC/ReactMono/issues/4)。
2. [#5 基础电脑与 100 种固定种子模拟](https://github.com/SiliconYC/ReactMono/issues/5) 依赖 #3/#4。
3. [#6 简体中文 UI 和真实浏览器完整对局](https://github.com/SiliconYC/ReactMono/issues/6) 可在 #2 完成后着手显示层，正式集成需 #3/#4/#5。

不要把“已经创建 Issue”冒充“已经开发或验收完成”。P1 详细边界参见 [P002 研究与晋升结果](docs/proposals/P002-first-playable.md)。

## 当前版本试玩与验收

- [GitHub Pages 在线游玩](https://siliconyc.github.io/ReactMono/)：P2 人机对局、存档、多种卡片/机会事件以及离线启动。
- **主程序 3D 棋盘**：执行 `npm install` 后运行 `npm run main:dev`，固定打开 [http://127.0.0.1:4174/](http://127.0.0.1:4174/)；原有 4173 demo 保持单独运行，并在界面中标记为“待删除迁移参考”。主程序保留两张地图、2–4 人与电脑对局、规则、存档及离线入口；3D 场景直接使用实际地图数据布置棋盘。地产可在到访时购买、建房和升级，同行同主地产可联排；银行支持存取款，股票交易使用银行存款。`npm test` 运行规则和构建回归，`npm run demo:build` 单独检查仍保留的迁移参考 demo。临时验收端口和生产构建分别为 4174 与 `dist/`。
- [P2 总验收 Issue #20](https://github.com/SiliconYC/ReactMono/issues/20) / [PR #29](https://github.com/SiliconYC/ReactMono/pull/29)：规则/百种子、离线、自动存档、JSON 往返及 Chromium 公网交互证据。
- [P3 16 项任务 #30–#45](https://github.com/SiliconYC/ReactMono/issues/30)：规则模块化 → 2–4 人/多地图 → 经济及股市 → 特殊格/AI → 综合验收。
- [历史 P2 执行队列](docs/P2_QUEUE.md) 与 [实际开发实验日志](docs/EVOLUTION_LOG.md)。

## 外部《大富翁 4》开源项目研究（增量补做）

项目已有大量现代 3D 游戏代码、规则测试及完整的开发治理，**不进行“空白研究仓库初始化式”的目录迁移、README/AGENTS 重写或项目结构调整**。在保留现有产品开发路径的同时，新增独立的 [`docs/research/` 外部项目研究入口](docs/research/README.md)：

- [研究证据、报告与许可标准](docs/research/RESEARCH_STANDARD.md)：记录上游精确 Commit、源码锚点，区分独立实测、源码核查、上游声称和未验证推断；不复制版权素材。
- [逐仓库研究索引](docs/research/repositories/README.md)：每个上游一个目录，交付九章报告、源代码定位与结构化证据 JSON。只有研究实际完成才建立该目录，不做空占位。
- [研究 Issue #95–#103](https://github.com/SiliconYC/ReactMono/issues/95)：九个目标分别研究原版逆向、原生/网页/Godot 重建、早期 Cocos 和现代 Three.js 视觉。Issue 各自独立开发、验收、合并 `dev`。
- [跨仓库综合综述 Issue #104](https://github.com/SiliconYC/ReactMono/issues/104)：待子研究完成后，复核源码血缘、证据冲突、许可证、原版规则与 ReactMono 差距，形成综合报告和验证矩阵。

**研究只为改善现有游戏提供可追溯依据**，不引入服务器、账号、云同步，不默认改变 React/Three.js 现代原创美术方向。研究任务创建不等于研究报告已经完成，研究完成也不等于产品功能已交付。

## 协作入口

- [主程序界面重设计：完整方案、交互网页与图像档案](docs/main-game-ui-redesign/README.md)（[直接查看图文入口](docs/main-game-ui-redesign/index.html)，含重做后的真实游戏画面与验收）
- [美术与前端重建：方向、架构、动画、资产与验收](docs/art-renewal/README.md)
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
