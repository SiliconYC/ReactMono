# Issue #2｜工程构建与首次静态发布验证

当前版本是 React + TypeScript 的**工程与规则契约验证**，不是可玩游戏；不可把测试页面冒充完整大富翁。

## 运行命令

- `npm install`：获取 TypeScript 开发依赖。
- `npm test`：TypeScript 构建 + Node 原生测试。
- `npm run build`：生成静态发布文件到 `dist/`。
- `npm run dev`：构建并启动本地验证页面（默认端口 4173）。

## 当前真实能力

- 已实现：24 格初始配置、2 人（真人/电脑）、1500 初始资金、版本化状态、可复现的伪随机骰子接口、合法开始游戏命令、不合法动作拒绝。
- **未实现**：走格、实际投骰命令、买地、收租、破产、电脑玩家自动策略、存读档、离线 PWA。分别留给 #3–#6 及 P2。
- 测试页面只允许创建初始对局状态，不能玩完整一局。

## 架构

`src/core/game.ts` 是不依赖 React、DOM 或 Node 专属 API 的纯数据规则核心；`src/ui/app.tsx` 是简体中文测试界面。`site/` 放静态页面与 CSS，`scripts/build.mjs` 组装可发布的 `dist/`。

**明确技术债**：当前测试沙盒无法访问 npm 注册表，因此本轮使用已安装的 TypeScript 编译器和 Node 原生测试；网页通过 CDN 加载 React 18 UMD。P1 只验证在线 Pages 运行，**不具备 PWA 离线能力**。P2 前应改为本地打包 React、添加依赖锁文件，完善 Service Worker 离线缓存和 IndexedDB 存档，不得把依赖 CDN 的页面宣传成断网可玩。

部署方式：源码及 PR 目标为 `dev`；仅编译产物发布到 `gh-pages`，Pages 静态发布不使用 `main`。若仓库尚未配置 Pages 发布源，需进行首次设置；推送 `gh-pages` 并不自动证明网站已上线。

## 本轮验证记录

- `npm test`：6/6 规则测试通过（首次执行环境：Node 22.16、TypeScript 5.8.3）。
- `npm run build`：成功产生 `dist/`，含 HTML、CSS、规则与 React UI JS。
- 浏览器烟测：在沙盒的 Chromium 中注入离线可用的 React 16 UMD 兼容库进行替代验证（由于沙盒对外/本地 HTTP 访问受限），页面显示中文状态且点击“创建测试对局”后切换为“测试对局已创建”，无页面脚本异常。此项**不等于**线上 React 18 CDN 或 GitHub Pages 的真实远端访问验收。
