# 主程序界面重做 Implementation Plan

> 执行方式：superpowers:executing-plans，本会话实施，结束后独立代码审查。所有者已授权无需阶段审批。

**Goal:** 修复 #92 的视觉与操作退化，交付真实可玩的界面。
**Architecture:** App 保留会话、规则和存储命令；视图拆出基础组件与面板，主程序只加载一份新样式；世界通过安全区参数适配 HUD。
**Tech Stack:** 现有 React 18 / TypeScript / R3F，不升级依赖。
**Spec:** `docs/main-game-ui-redesign/rebuild-2026-10-19.md` 及原完整方案。

## Global Constraints

- 纯静态、本机存档、简体中文，集成目标 dev，禁止 main 或正式部署。
- 不改规则和存档结构；旧档继续使用原规则旗标。
- 演出只展示事件，输入与 AI 等待完成；全场景统一阴影策略保持。

## Review Focus

- 打开面板时已有 AI 计时器必须取消，关闭后恢复。
- 连续真人交接与读档不得显示旧骰子或执行旧回调。
- 旧档非到访规则的升级仍可达。
- 窄屏、短屏与长名字不会挤出主操作。
- 动画结束/快进/后台恢复不会重播随机或跳过结果。

### Task 1: 页面、HUD 与统一模态

Files: src/ui/app.tsx, src/ui/game-ui.tsx, site/game-ui.css, site/index.html, tests/browser_ui_rebuild_e2e.py。
Interfaces: 沿用 App.dispatch / 存储命令；Modal(title,onClose,children)、SeatAvatar(seat)、TownIllustration(harbor?)；UI 新增 overlay 单一枚举。

- [x] RED：运行 `python3 tests/browser_ui_rebuild_e2e.py`，预期标题触摸目标/直接可见席位失败。
- [x] 实现独立页面、固定行动条、原生 dialog、真实面板、直接建设；用 overlay 停止 AI 并隔离世界输入。
- [x] GREEN：定向浏览器全部指定视口通过；检查菜单、旧档建设、真人交接及 AI 面板暂停。
- [x] 执行 npm test，处理仅绑定旧 DOM/CSS 的静态断言并保持等价行为测试；提交任务分支。

### Task 2: 世界与演出可靠性

Files: src/demo3d/world/WorldCanvas.tsx, camera-layout.ts, Dice.tsx, Mascot.tsx, tests/camera-layout.test.mjs, tests/browser_ui_rebuild_e2e.py。
Interfaces: 可选 viewportInsets={top,right,bottom,left}，demo 默认值为零；cameraFrame(viewport,insets,bounds) 返回正交相机构图尺寸/偏移。

- [x] RED：写安全区测试（有效区域/大小/偏移）；浏览器检查 1～6 点和交易不改变骰子 nonce。
- [x] 实现安全区相机、只在投骰演员上显示新骰点、结果展示时统一输入门。
- [x] GREEN：纯计算测试与真实画面/中间帧通过；npm test、demo:build、两图完整局、离线存档验证通过。
- [x] 独立审查、修复重要发现；更新档案与截图，提交并合并 dev。
