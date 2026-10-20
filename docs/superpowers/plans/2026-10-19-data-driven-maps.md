# 数据驱动压力地图实施计划

> 使用 executing-plans 在本会话顺序实施；仓库自主实施授权覆盖设计、实现、验证和合并 dev，无阶段审批。

**Goal:** 提交背景艺术方案，实际加载 60/120/360 格 JSON 地图。
**Architecture:** JSON 目录 → 纯加载/校验 → 规则与存档注册 → 通用 UI。背景代码不动。
**Tech Stack:** 现有 TypeScript/React/Vite/Node，不增加依赖。
**Spec:** `docs/proposals/P007-scalable-world-maps.md`

## Global Constraints

- 仅静态 PWA，简体中文，集成 dev，不发布正式服务。
- 旧地图/旧存档兼容，不修改背景渲染。

## Review Focus

- 新目录添加地图是否需要 TS 分支；以任意额外 JSON 条目验证加载器。
- 坏数据、重复坐标、越界引用、未知字段与断路必须明确拒绝。
- 长地图的完整循环/首尾移动和存读档不能截断。
- 原有两图经济与几何必须逐字段兼容。
- UI 真实选图后地图身份、移动与保存结果一致。

### Task 1: JSON 数据与通用加载

Files: `src/data/levels.json`, `src/core/level-data.ts`, `src/core/maps.ts`, `src/core/config.ts`, `scripts/validate-maps.mjs`, `tests/data-driven-maps.test.mjs`。

Interfaces: `LEVELS`, `PLAYABLE_LEVELS`, `loadLevelCatalog(unknown)`, `levelConfig(id)`；保持既有默认导出。

- [x] 写三图格数、邻接、循环、目录拒绝与任意新条目测试；执行确认因缺少三图而失败。
- [x] 迁移全部现有数据，添加三图；通用结构校验与冻结，接入规则注册/配置；提供 CLI。
- [x] 全量 npm test，三图固定种子模拟、存档往返和伪造拒绝通过后提交。

### Task 2: 通用地图选择与独立验收

Files: `src/ui/app.tsx`, `tests/browser_stress_maps_e2e.py`, 现有浏览器测试辅助，项目说明与进化日志。

Consumes: Task 1 的 `PLAYABLE_LEVELS`, `levelConfig(id)`；不写死 ID。

- [x] 先写浏览器三图选择/开局/掷骰/存读档测试；确认现有 UI 不存在对应选项。
- [x] 选图、重开、HUD 名称从目录读取，SVG 按真实坐标绘制缩略图；迁移原有两图数量断言为包含原两图。
- [x] npm test、demo:build、真实 Chromium 三图与旧图回归、4173/4174 HTTP 与交互。
- [x] 独立审查和差异复查；记录结果和未实施背景风险，提交后合并本地 dev。

验收结果与独立审查修复记录见 `docs/maps/ACCEPTANCE.md`。实现时补齐通用轮廓生成器、独立交换文件、设施配置与原 demo 的全量数据迁移，均在原授权范围内。
