# 主程序 3D 接管实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** 将主程序默认界面替换为基于既有完整规则状态的 3D 街区界面，并保留其完整玩法、存档和离线能力。

**Architecture:** 主程序的 React UI 作为 Vite 同源 bundle 运行，嵌入 demo 的 R3F 场景并让地图坐标从 GameMap 动态生成。已有 UI 继续负责回合命令、电脑玩家、金融、卡片、玩家设置及 IndexedDB；demo 仅标待退役。

**Tech Stack:** React 18、TypeScript、Three.js、@react-three/fiber、Vite、Node test runner。

**Spec:** [主程序 3D 接管设计](../specs/2026-10-18-main-3d-takeover-design.md)

## Global Constraints

- 纯静态 GitHub Pages/PWA 准本地运行；不做账号、云同步或后端。
- 所有游戏界面和提示只使用简体中文。
- `dev` 是默认开发、集成和 PR base 分支；不修改 `main`。
- GameState 是唯一规则/存档状态；画面和动画不改变结算。
- `127.0.0.1:4173` 晴湾 demo 服务保持运行，主程序测试使用 `127.0.0.1:4174`。
- 全场景统一投影/受影；所有地图格、建筑和平台贴地。

## Review Focus

- 页面离线/Service Worker 是否遗漏 bundle/chunk：构建产物清单与 SW 缓存测试。
- classic-24 与 harbor-20 是否布局/路径一致：坐标映射单测和浏览器地块选择。
- 3–4 人同格和产权是否可辨认：角色站位与玩家颜色测试。
- WebGL 创建失败是否还能操作：简化棋盘浏览器检查。
- IndexedDB 旧档是否被新入口误改：旧 schema 夹具恢复回归。

---

### Task 1: 规则地图到世界坐标的动态映射

**Files:** `src/demo3d/world/layout.ts`、`src/demo3d/world/MiniatureTown.tsx`、`src/demo3d/world/Mascot.tsx`、`src/demo3d/world/WorldCanvas.tsx`、`tests/demo3d-layout.test.mjs`

**Interfaces:** `positionForTile(tileId:number,map:GameMap):WorldPoint`；场景内所有道路、地块、角色与动画统一使用 game.map。

- [x] 写布局测试：24/20 格每 tile 坐标存在且唯一；route 邻接点与 `cells` 一致；边界地块朝内。
- [x] 运行 `node --test tests/demo3d-layout.test.mjs`，确认旧静态布局失败。
- [x] 从 `map.cells` 推导路径节点、退界、地块朝向和世界边界；移除固定 16 格索引依赖。
- [x] 把 map 传给所有场景坐标消费者；扩展 3/4 人稳定角色站位/颜色。
- [x] 重跑布局测试及 `npm run demo:build`。

### Task 2: 主程序 React 与 3D 场景统一打包

**Files:** `src/ui/app.tsx`、`src/ui/react-shims.d.ts`、`src/ui/main.tsx`、`vite.main.config.ts`、`scripts/build.mjs`、`site/index.html`、`tests/build-pwa.test.mjs`

**Interfaces:** 页面由 `ui/main.tsx` 单一 React 18 `createRoot` 入口挂载；现有 `dist/core/*.js` Node 接口保留。

- [x] 添加构建验收，要求生产首页引用本地 bundle、同源 Three/R3F，SW 包含生成的模块，不引用 React UMD。
- [x] 运行针对性构建测试并确认当前入口失败。
- [x] 模块化 React 挂载主程序；Vite bundle UI 与 3D 模块，保留 tsc 核心输出和原静态资源生成流程。
- [x] 让 SW 的资源列表和 fingerprint 纳入 Vite 输出的所有运行 chunk。
- [x] 运行 `npm run build` 与构建验收。

### Task 3: 3D 接管主程序棋盘

**Files:** `src/ui/app.tsx`、`src/demo3d/world/*`、`src/ui/board-fallback.tsx`、`site/*.css`、`tests/main-3d-entry.test.mjs`

**Interfaces:** `WorldCanvas` 收到现有 `GameState`、选中 tileId、骰子/移动/租金/事件表现与 reduced motion；地块选择回调只设置现有 UI 选中状态。

- [x] 写入口验收，要求主程序默认棋盘为 3D Canvas，保留同页操作/设置/金融/存档 DOM 且 demo 标记只出现于独立入口。
- [x] 先运行并确认当前 2D 主程序失败。
- [x] 将 3D 世界嵌入主 UI 并接入选格、动作轨迹、事件、租金、胜负表现；主程序新局启用银行、贷款、股票、访问升级限制，保留配置/旧档规则。
- [x] 加 WebGL 创建失败时有键盘/触屏可操作的 DOM 地块网格。
- [x] 运行入口测试、核心 `npm test` 和 `npm run build`。

### Task 4: 标记 demo 退役并提供 4174 审核服务器

**Files:** `demo3d/index.html`、`vite.main.config.ts`、`package.json`、`docs/EVOLUTION_POOL.md`、`docs/proposals/P006-3d-art-renewal.md`、`docs/EVOLUTION_LOG.md`、`docs/ROADMAP.md`

- [x] 写退役标记检查：独立 demo 入口提示待删除及条件，旧源码仍存在。
- [x] 配置 `main:dev` 固定 127.0.0.1:4174/strictPort；demo 原 4173 配置不变。
- [x] 记录本轮实际能力、测试、遗留风险和删除门槛；不宣布 P4 总验收完成。
- [x] 运行 `npm test`、`npm run build`，启动两个服务并分别检查 4173/4174 HTTP 与浏览器交互。

## Commit checkpoints

在任务间使用聚焦提交；完成后推送任务分支并通过 PR 合并至本地 `dev`，再推送 `dev` 到 `origin/dev`。
