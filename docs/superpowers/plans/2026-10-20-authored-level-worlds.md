# Authored Level Worlds Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use checkbox syntax for tracking.

**Goal:** 将关卡背景升级为显式数据，并重绘五张可玩地图。

**Architecture:** 纯数据世界格式与校验器独立于 React。规则网格不变，显式道路/地产坐标统一服务渲染、导航、预览；景物只能来自数据。旧格式规则草稿可读取，所有正式关卡采用版本2。

**Tech Stack:** TypeScript / React / Three.js / JSON / Node tests / Playwright。

**Spec:** docs/proposals/P008-authored-level-worlds.md

## Global Constraints

- 仅静态、简体中文、不新增依赖；目标 dev；不发布正式服务。
- 不改变已发布的规则格号、map.version、经济与存档结构。
- 全场景统一投影/受影；所有地面部件依共用地表高度落地。
- demo:dev 为127.0.0.1:4173，主程序为4174，验收后保持运行。

## Review Focus

- 旧档和旧规则草稿无 world：保留逻辑兼容，空背景不生成景物。
- 曲线道路：非相邻段、地产之间不得碰撞，角色/点击/预览保持一致。
- 地形洞、非法多边形及非有限数据必须在加载时拒绝。
- 远景、手机与重复切换：完整覆盖，显式景物不漂移，GPU资源不持续增长。
- 中性格设施不再自动变成树：正式场景逐个指定，所有银行可见。

### Task 1: 世界格式与完整性验证

**Files:** src/core/level-world.ts, src/core/level-data.ts, tests/authored-world.test.mjs
**Interfaces:** WorldDefinition; validateWorld(value,tileCount); worldForMap(map); visibleDecorations(world,bounds).
- [ ] 写缺失/重复/非法多边形/变异隔离及旧格式兼容测试，先观察失败。
- [ ] 实现纯数据类型与严格验证，目录版本2要求world，版本1兼容规则草稿。
- [ ] 运行构建与上述测试，提交。

### Task 2: 手工编排地图数据与坐标接管

**Files:** src/data/levels.json, src/demo3d/world/layout.ts, docs/maps/containers/, tests/demo3d-layout.test.mjs, tests/scalable-world.test.mjs
**Interfaces:** anchorsForMap优先读取world道路与地产；未注册测试地图保留旧规则坐标兼容布局。
- [ ] 写显式坐标接管、道路/地产间距、对象不变与旧规则不变测试并观察失败。
- [ ] 编排五张曲线地图和参考demo；地形面/每个景物均物化为JSON坐标，交换容器同步。
- [ ] 以真实旋转矩形及线段距离校验占用，运行测试，提交。

### Task 3: 显式景观渲染与统一导航

**Files:** src/demo3d/world/ContinuousGround.tsx, AuthoredScenery.tsx, MiniatureTown.tsx, WorldCanvas.tsx, WorldNavigation.tsx, src/ui/LevelPreview.tsx, app.tsx
**Interfaces:** 地面/景物只消费WorldDefinition；道路旋转/连接基于显式anchors；预览和迷你地图复用相同顶点。
- [ ] 删除hash植被与隐式地标，替换显式多边形、实例植被和具名设施，保留全局阴影。
- [ ] 道路/地产朝向与连接线支持任意方向；地表覆盖可见视域，水面低于陆地。
- [ ] 正式预览、迷你地图展示地形与实际路线；运行npm test与demo:build，提交。

### Task 4: 真实画面、游玩与独立验收

**Files:** tests/browser_authored_world_e2e.py, tests/browser_scalable_world_e2e.py, docs/maps/AUTHORED_WORLD_ACCEPTANCE.md, EVOLUTION_POOL.md, EVOLUTION_LOG.md
- [ ] 更新原浏览器投影坐标契约，验证桌面/手机五图、导航、买地、旧档与重复切换资源。
- [ ] 查看截图，修复拥挤、遮挡、单调或穿插问题；记录真实证据。
- [ ] 完成独立代码审查、必要修复，运行完整测试与构建，确认4173/4174交互。
- [ ] 原子提交、集成本地dev，推送任务分支并创建指向dev的PR；说明未正式发布。
