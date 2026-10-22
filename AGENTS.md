# Agent 约定

- 开发与合并目标为 `dev`；仓库写操作显式指定分支，未经明确授权不修改 `main`。
- 已授权任务完成必要验收后自行合入 `dev`；自主选题的准入与记录按下列演进规范执行。
- 修改规则或存档结构时检查既有对局与存档兼容性。

## 本地测试

- 主游戏：`npm run main:dev`，`http://127.0.0.1:4174/`。
- 独立 3D 演示：`npm run demo:dev`，`http://127.0.0.1:4173/`。
- 两个入口均使用 `strictPort`；冲突时先核实本仓库进程，不静默换端口或提供旧链接。交给用户继续验收时保持对应服务运行。

## 上下文索引

- 产品约束与阶段：`README.md`、`docs/PROJECT_CHARTER.md`、`docs/ROADMAP.md`。
- 自主演进规则与候选池：`docs/AUTONOMOUS_EVOLUTION.md`、`docs/EVOLUTION_POOL.md`。
- 外部研究：`docs/research/README.md`、`docs/research/RESEARCH_STANDARD.md`。
