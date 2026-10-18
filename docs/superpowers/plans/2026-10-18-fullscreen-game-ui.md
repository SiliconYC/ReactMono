# 主程序全屏游戏 UI 实施计划

**Spec:** [全屏游戏界面设计](../specs/2026-10-18-fullscreen-game-ui-design.md)

**目标分支：** `dev`。当前工作分支从最新 `dev` 派生；完成后合并回 `dev` 并同步远端。

## 任务

1. **全屏世界基底**
   - `site/style.css`, `site/board-art.css`, `site/board-3d.css`
   - 固定 `html/body/#root/.app-shell` 到 `100dvh`，移除页面容器宽度/页边距/背景画布，地图场景覆盖全屏；隐藏宣传标题和页脚。
   - 桌面、窄屏分别给顶部栏、底边玩家快捷条、右侧当前行动卡留安全区；只有 HUD 自身滚动。
   - 验收：浏览器截图中 canvas 覆盖视口，不发生 document scroll。

2. **开局/高级设置分层**
   - `src/ui/app.tsx`, `site/board-3d.css`
   - setup 屏显示游戏标题、地图、人数和开始按钮；把种子、玩家详情、轮数、设施及速度放入原生折叠的高级设置。
   - 资产面板、存档、玩家列表、事件与帮助默认收起，不删除任何交互。
   - 验收：原有 2–4 人、地图选择、命名、真人/电脑策略和种子配置仍能操作。

3. **对局 HUD 与结算覆盖层**
   - `src/ui/app.tsx`, `src/demo3d/world/WorldCanvas.tsx`, `site/board-3d.css`
   - 全屏棋盘下呈现当前玩家与本回合关键行动；金融和存档等次要操作通过 HUD details 面板访问。
   - 结算结果居中覆盖场景；窄屏按钮 ≥44px 并按单列排列。
   - 静止时采用全图视角，移动时跟随角色，保持 20/24 格可见。
   - 验收：setup、playing、finished 三种状态在桌面和窄屏上无文档滚动，所有主要按钮可见/可触达。

4. **记录与交付**
   - `docs/EVOLUTION_LOG.md`, `docs/EVOLUTION_POOL.md`, 本计划
   - 写入真实浏览器/构建结果与未测项目；保留 #73 未完成状态。
   - 运行生产构建并在 4174 做桌面/窄屏 UI 实际检查；确认 4173 继续 HTTP 200。
   - 提交任务分支，PR base `dev`，合并并快进本地 `dev`、推送远端。
