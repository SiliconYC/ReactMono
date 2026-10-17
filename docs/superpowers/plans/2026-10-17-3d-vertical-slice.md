# 低多边形 3D 垂直切片 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不替换现有正式入口的前提下，交付一个本地可运行、由现有规则核心驱动的 16 格低多边形 3D 对局切片，玩家可以投骰、逐格移动、买地并结束回合。

**Architecture:** 新增独立的 Vite + React 18 + React Three Fiber 8 演示入口，复用 `src/core` 作为唯一骰子、位置、资金和产权权威；纯函数适配层把规则结果转换为路径与演出快照，3D 场景只消费这些结果。演示构建输出到独立目录，不改变旧 UI、存档 schema、PWA 缓存和现有发行预算门槛。

**Tech Stack:** TypeScript、React 18、Three.js、React Three Fiber 8、Vite、Node 内置测试、Chrome 浏览器验收

**Spec:** `docs/art-renewal/README.md`（重点：`01-art-direction.md`、`03-frontend-architecture.md`、`04-animation.md`、`06-delivery-and-acceptance.md`）

## Global Constraints

- 目标和开发分支均从 `dev` 派生；不修改 `main`，不发布正式服务。
- 纯静态、本地可运行；无账号、无后端、无运行时 CDN。
- 所有玩家可见文本使用简体中文。
- 骰子点数、位置、现金和产权仅由现有 `src/core` 决定；3D 动画不得重算规则。
- 首轮保持存档 schema 不变，演示页不接管现有 PWA 与 IndexedDB。
- 现有正式入口及其构建、测试和 2 MB 预算不被演示产物替换或放宽。
- 视觉目标是完成度较高的原创低多边形微缩街区，不复制 Crossy Road 或《大富翁4》的受保护素材。

## Review Focus

- 连续点击投骰时只能提交一次规则命令，角色不能重复走路或越过终点。
- 角色跨越环线起点时，逐格路径必须按 route 正向连接，而不是倒走最短路径。
- 动画中途切到“减少动态效果”时，世界位置与 HUD 必须同步到权威终态。
- WebGL 初始化失败时，页面要给出中文可理解提示，不能永久停在加载状态。
- 1280×800 与 390×844 视口下，投骰/购买/结束回合主操作都可见且触控目标不小于 44px。

---

### Task 1: 规则驱动的演示会话与路线规划

**Files:**
- Create: `src/demo3d/session.ts`
- Create: `src/demo3d/route.ts`
- Create: `tests/demo3d-session.test.mjs`
- Modify: `package.json`
- Modify: `package-lock.json`

**Interfaces:**
- Consumes: `createGame(seed, config)`, `applyAction(state, action)`, `INTERNAL_TEST_MAP` from `src/core/game.ts`
- Produces: `createDemoGame(seed: number): GameState`, `dispatchDemoAction(state: GameState, action: GameAction): DemoCommandResult`, `routeSteps(route: readonly number[], from: number, steps: number): readonly number[]`

- [ ] **Step 1: Write failing rules-adapter tests**

Add tests proving a fixed seed starts a two-player 16-tile session, a roll returns the literal die value from `die_rolled`, and `routeSteps` includes every forward tile across route wrap-around without duplicating the origin.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `npm run build && node --test tests/demo3d-session.test.mjs`

Expected: FAIL because `dist/demo3d/session.js` and `dist/demo3d/route.js` do not exist.

- [ ] **Step 3: Implement the minimal adapter and route functions**

The adapter creates an isolated 16-tile configuration with two local human players, submits each action exactly once through `applyAction`, and returns `before`, `after`, `events`, `dieValue`, and the literal traversed tile IDs for accepted rolls.

- [ ] **Step 4: Run focused and full Node suites**

Run: `npm run build && node --test tests/demo3d-session.test.mjs`

Expected: PASS.

Run: `npm test`

Expected: all existing and new Node tests pass with 0 failures.

- [ ] **Step 5: Commit Task 1**

```bash
git add package.json package-lock.json src/demo3d/session.ts src/demo3d/route.ts tests/demo3d-session.test.mjs
git commit -m "feat: add rule-driven 3d demo session"
```

### Task 2: 微缩街区场景、角色与骰子演出

**Files:**
- Create: `demo3d/index.html`
- Create: `src/demo3d/main.tsx`
- Create: `src/demo3d/DemoApp.tsx`
- Create: `src/demo3d/world/WorldCanvas.tsx`
- Create: `src/demo3d/world/MiniatureTown.tsx`
- Create: `src/demo3d/world/Mascot.tsx`
- Create: `src/demo3d/world/Dice.tsx`
- Create: `src/demo3d/world/layout.ts`
- Create: `tests/demo3d-layout.test.mjs`
- Modify: `package.json`
- Modify: `package-lock.json`

**Interfaces:**
- Consumes: Task 1 `DemoCommandResult` and route tile IDs
- Produces: `TILE_ANCHORS`, `positionForTile(tileId: number)`, `WorldCanvas` props for authoritative players/tiles plus transient movement and die presentation

- [ ] **Step 1: Write failing layout tests**

Add tests proving all 16 tile IDs have unique X/Z anchors, consecutive route anchors remain visually adjacent (including 15→0), and every property lot sits outside the walking lane.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `npm run build && node --test tests/demo3d-layout.test.mjs`

Expected: FAIL because `dist/demo3d/world/layout.js` does not exist.

- [ ] **Step 3: Implement the 3D page and scene**

Build an orthographic, fixed-angle miniature island with a cohesive warm/cool palette, soft shadows, water/ground layers, curved road edges, 16 readable lots, modular houses, trees, lamps and a central landmark. Add two original low-poly mascots, a correctly oriented 3D die, per-tile travel interpolation, landing pulse, purchase/build reveal, limited camera follow, DPR cap, WebGL fallback, and reduced-motion completion behavior.

- [ ] **Step 4: Run focused tests and production demo build**

Run: `npm run build && node --test tests/demo3d-layout.test.mjs`

Expected: PASS.

Run: `npm run demo:build`

Expected: Vite exits 0 and creates `dist-3d-demo/index.html` with no CDN references.

- [ ] **Step 5: Commit Task 2**

```bash
git add demo3d src/demo3d package.json package-lock.json tests/demo3d-layout.test.mjs
git commit -m "feat: build low-poly 3d miniature town"
```

### Task 3: 商业化 HUD、回合操作与 Chrome 实机验收

**Files:**
- Create: `src/demo3d/demo.css`
- Create: `tests/browser_demo3d_e2e.py`
- Modify: `src/demo3d/DemoApp.tsx`
- Modify: `src/demo3d/world/WorldCanvas.tsx`
- Modify: `README.md`

**Interfaces:**
- Consumes: Task 1 session actions and Task 2 `WorldCanvas`
- Produces: 中文 HUD with `掷骰前进`, `买下此地` / `暂不购买`, `结束回合`, player cash/turn/location, event toast, camera overview/follow toggle, and stable browser selectors

- [ ] **Step 1: Write the failing browser acceptance test**

At 1280×800 and 390×844, assert the scene canvas and current-player HUD are visible; click `掷骰前进`; observe at least one intermediate actor position before the authoritative landing position; verify die result text and that no second roll command is accepted while moving; then complete any offered purchase decision and end the turn.

- [ ] **Step 2: Run the browser test and verify RED**

Run: `python3 -m unittest tests.browser_demo3d_e2e`

Expected: FAIL because the polished shell/selectors/interaction contract are incomplete.

- [ ] **Step 3: Implement the responsive shell and interaction gates**

Add a focused top status rail, bottom action dock, location/event cards, accessible 44px controls, scene-loading and WebGL error states, reduced-motion behavior, responsive mobile layout, and concise README launch instructions. Keep debug/settings panels out of the primary view.

- [ ] **Step 4: Run fresh verification**

Run: `npm test`

Expected: all Node tests pass with 0 failures.

Run: `npm run demo:build`

Expected: exit 0.

Run: `python3 -m unittest tests.browser_demo3d_e2e`

Expected: both desktop and mobile cases pass with 0 failures.

- [ ] **Step 5: Inspect in visible Chrome and commit**

Start `npm run demo:dev -- --host 127.0.0.1`, open the printed local URL in Chrome, operate at least one full human turn, and visually inspect composition, shadows, route readability, action visibility, dice face, movement continuity and purchased-property feedback.

```bash
git add README.md src/demo3d tests/browser_demo3d_e2e.py
git commit -m "feat: polish the 3d turn experience"
```

