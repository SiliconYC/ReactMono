# Issue #3：棋盘、骰子、回合推进（实施与验证记录）

## 本轮新增功能

- 24 格环状棋盘展示：起点 1、地产 16、普通格 7；真人与电脑棋子位置实时反映引擎状态。
- 玩家从开局进入等待掷骰；单枚六面骰、绕圈移动、到达地块事件、暂时跳过购买、结束回合、轮次切换。
- 实现 `await_roll`、`await_decision`、`await_end_turn`、`finished` 阶段的合法命令约束；错误动作不会改变状态。
- 固定种子与纯函数回放；60 轮到达临时规则上限后测试局结束。#4 将实现真正的经济胜负。
- 电脑目前由玩家点击“代电脑掷骰”继续轮次，**不是电脑 AI**；#5 才实现自主对手。
- 新界面仅简体中文，使用自制图形和静态资源，不加入账号/后端，不更改 `main`。

## 本地验证

- `npm test`：**12/12 项通过**（原有 6 项 + 新增 6 项棋盘回合测试）。
- 覆盖：骰子点数 1–6、跨尾格绕圈、自定义地图、行动者校验、非法连续掷骰、不能跳过待决策、两名玩家交替、固定种子可复现、无界面推进到 60 轮终局、终局拒绝后续操作。
- `npm run build`：TypeScript 编译及静态文件构建成功。
- 沙盒 Chromium：由于浏览器对本地 HTTP 请求有管理员限制，通过向 `about:blank` 注入**实际构建后的游戏逻辑与 UI JS**、静态 CSS 和本地可用的 React 16 UMD，验证 24 个棋盘格呈现；点击“开始测试对局 → 真人掷骰 → 跳过购买 → 结束回合 → 代电脑掷骰 → 结束回合”，正确进入第 2 轮，双方棋子分别在 1 号与 5 号格，**无 JS 异常**。
- 以上沙盒浏览器烟测使用 React 16 UMD 替代在线 React 18 CDN，**不能冒充已通过线上 CDN 加载或真实公网端到端测试**。GitHub Pages 平台部署另行核对。

## 范围与技术债

- **尚未实现**：地产购买、租金、资产与破产结算，正式胜负/净资产判定，真正电脑玩家自动行动、存读档与 PWA 离线。
- `buy_property` 明确返回 `NOT_IMPLEMENTED`，购买按钮不会伪装为成功；当前可跳过地块进入后续回合。
- 暂依赖 React 18 在线 CDN；P2 需改为本地打包并验证断网能力。
- 浏览器规则层不依赖 React 或 DOM；测试/构建仍通过 Node 22 和预装 TypeScript 5.8.3，干净网络环境的 `npm install` 本沙盒不可验证。

## 实际提交与 GitHub Pages 验证

- 代码工作分支：`feat/issue-3-board-turns`；[PR #8](https://github.com/SiliconYC/ReactMono/pull/8) 已经通过 squash 合并回 `dev`，提交 `5d267bbe5d3d52c51aedad070bbbc6a6ced2fe42`。
- 静态编译产物经独立 [`gh-pages` 提交](https://github.com/SiliconYC/ReactMono/commit/93b9edb7c4710ed2a98c48ce24ba203142ee41ea) 发布；`index.html`、`style.css`、`core/game.js`、`ui/app.js` 四个文件的 Git blob 哈希与沙盒构建逐一吻合。
- [GitHub Pages 部署运行 #38753188805](https://github.com/SiliconYC/ReactMono/actions/runs/38753188805) 报告 `completed / success`，发布地址为 **https://siliconyc.github.io/ReactMono/**。
- 本沙盒的网页读取工具无法访问实际公网 Pages 地址，故**没有冒充已完成线上真人浏览器端到端核验**。用户可以访问上面的地址做实际体验。
- 仅由 GitHub Pages 平台运行其自动发布任务，没有新增 GitHub Hosted Runner 来编译游戏。源码依然只在 `dev` 开发，**未操作 `main`**。

