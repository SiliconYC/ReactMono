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

### 2026-10-15｜E001：Issue #2 工程骨架实现与首轮 Pages 静态发布

- **来源**：[P002](proposals/P002-first-playable.md)、[Issue #2](https://github.com/SiliconYC/ReactMono/issues/2)。
- **实现**：[PR #7](https://github.com/SiliconYC/ReactMono/pull/7) 合并至 `dev`（`682809d05012c077130ad5b2a19fc8d19c0216c3`）。React+TypeScript UI；纯数据 `GameState`/`GameAction`/`GameEvent`、固定种子接口、24 格配置、两名玩家、合法开始游戏命令。其余游戏命令清晰标记未实现，不冒充可玩版本。
- **测试证据**：沙盒 Node 22.16 / TypeScript 5.8.3 运行 `npm test`，6/6 单元测试通过；`npm run build` 成功。Chromium 在受限沙盒内以本地 React 16 UMD 替代 CDN 验证首屏与点击“创建测试对局”后的状态切换，零 JS 页内异常；该烟测不能替代真正的公网 React 18 验收。
- **部署证据**：编译产物发布至独立 `gh-pages`（`5656e65f603c61ae01403269b0175cf39b4ebc45`），[GitHub Pages 部署 #38749060304](https://github.com/SiliconYC/ReactMono/actions/runs/38749060304) 显示所有 Job success，deploy 日志报告 `https://siliconyc.github.io/ReactMono/`，且仓库元数据 `has_pages=true`。
- **限制与不足**：因沙盒 npm 注册表连接失败，无法证明在本沙盒完成了 `npm install` 的干净依赖安装；使用系统预装 TypeScript。当前 React 从 CDN 在线加载，**尚不具备 PWA 离线能力**；在本沙盒无法通过公网 URL 进行浏览器实测。需要在后续环境验证 CDN 真正加载，P2 必须改用本地打包并锁定依赖版本。
- **验收范围**：本轮只确认了工程、单测、浏览器本地烟测及 GitHub Pages 平台发布结果；**没有**实现骰子动作、地图行走、租金、电脑策略或完整对局，不能计入“已做出游戏”。
- **下一步**：[Issue #3](https://github.com/SiliconYC/ReactMono/issues/3) 棋盘、骰子与回合规则。

### 2026-10-15｜E002：Issue #3 棋盘、骰子与回合系统

- **来源**：[P002](proposals/P002-first-playable.md)、[Issue #3](https://github.com/SiliconYC/ReactMono/issues/3)；从 #2 工程契约扩展到实际棋盘与行动规则。
- **真实新增玩家能力**：GitHub Pages 测试版显示 24 格封闭棋盘、人物标记；点击“开始测试对局”，即可掷骰、环绕走格、处理到达事件、跳过尚未支持的地产购买、结束回合，并由玩家手动为电脑代操作。这是可交互演示，不是完整游戏。
- **规则验收**：先新增 6 项失败测试再实现，连同原有测试合计 `npm test` **12/12 通过**；覆盖骰子范围、绕圈、回合合法性、真人/电脑轮换、固定种子重现、60 轮无界面终局与终局拒绝。
- **浏览器烟测**：在沙盒 Chromium 通过注入实际编译 JS 和本地 React 16 UMD 验证，24 格显示，真人/电脑各完成一回合后进入第 2 轮，玩家分别位于 1 与 5 号格，无页面脚本异常。因沙盒网络策略，**此测试不能证明线上 React 18 CDN 和 Pages 端到端交互已验收**。
- **源码与发布**：[PR #8](https://github.com/SiliconYC/ReactMono/pull/8) 已合并到 `dev`（`5d267bbe5d3d52c51aedad070bbbc6a6ced2fe42`）；[发布分支提交](https://github.com/SiliconYC/ReactMono/commit/93b9edb7c4710ed2a98c48ce24ba203142ee41ea)；[Pages 自动部署 #38753188805](https://github.com/SiliconYC/ReactMono/actions/runs/38753188805) `completed / success`，编译 JS 与站点静态资源的哈希吻合。
- **范围边界**：土地购买、收租、资金变化、破产与真正胜负未做（#4）；电脑自动策略未做（#5）；完整对局与独立端到端验收未做（#6）；PWA/存读档仍属于 P2。不得将 #3 算成完成一局游戏。
- **下一轮**：[#4 地产交易与经济胜负](https://github.com/SiliconYC/ReactMono/issues/4)，在 #3 的 `await_decision` 阶段接入购买/跳过和财务结算；任何修改应保留此次确定性与规则状态机测试。

### 2026-10-15｜E003：#5 电脑自动回合与百种固定种子模拟

- **来源**：[P002](proposals/P002-first-playable.md)、[#5](https://github.com/SiliconYC/ReactMono/issues/5)；依赖的 #4 已关闭。
- **代码**：[PR #10](https://github.com/SiliconYC/ReactMono/pull/10) squash 合并至 `dev`，提交 `88e2d315d3b925a306407953b84159b39c29c9a7`。
- **策略**：电脑仅通过合法 `applyAction` 投骰、选择买地/放弃、结束回合；默认买后保留至少 200 游戏币，阈值可配置。真人结束回合后，电脑自行行动，无须手动代操作。
- **自动测试**：TypeScript 编译成功，`npm test` **28/28 通过**。固定随机种子 0–99 共 100 局全部正常结束，最长 120 个玩家回合、276 条有效命令；41 局破产、59 局达到 60 回合上限，无拒绝动作及非法余额/产权；同种子重演一致。
- **浏览器**：Chromium 通过内联编译模块及本地 React UMD 兼容版本验证「真人买地并结束回合→电脑自动投骰、购地、结束回合→第 2 轮返回真人」，页面脚本异常为零。沙盒网络限制使得公网 Pages 的 React 18 CDN 加载**尚未获浏览器实测**。
- **Pages**：`gh-pages` 最新静态发布提交 `5bd88d6c640af59f658d81350810c71e5727defa`，[Pages 部署 #38759941787](https://github.com/SiliconYC/ReactMono/actions/runs/38759941787) 已完成且全部成功。
- **范围边界**：#6 的完整浏览器端到端质量验收、复杂电脑策略、PWA 与存读档仍未交付；本轮不宣称无人值守连续自我进化已建成。

## 自主改进实验账本

**已有独立功能的开发及自动测试记录；但尚无无人值守连续自主进化或 #6 完整真人验收的实证。** 后续每轮至少记录：

| 轮次 | 来源提案/Issue | PR/提交 | 目标与测试证据 | 独立验收 | 回归/回滚 | 成本与人工介入 | 结论 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| （尚无） | — | — | — | — | — | — | — |

每轮出现失败也要登记：失败原因、复现方法、下一步实验以及是否停止；不得只记录成功，不得用提交数量冒充玩家体验的提升。
