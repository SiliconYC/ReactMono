# Issue #100 · 固定上游源码索引

- 仓库：`oama1111/rich4-remake-public`；默认分支 `main`；固定提交：`42ad97ad31f07541a9af35415e36be4da4147484`。
- 核对：2026-10-19T01:20:13Z（UTC）。本索引均锚定该 SHA，避免 `main` 继续变更；行号基于此提交源码。
- **证据等级**：B = 本次逐文件源码查阅；C = 上游文档自述；**不存在 A 级游戏运行结果**。阅读公开 API 树（1051 个条目、未截断）和以下指定源码；不能据此声称逐文件审计全部 1051 项。
- 源码索引不是上游源码副本；涉及原版商用素材的路径不复制。

| 路径与永久链接 | 行号 / 符号 | 具体证据与限制 | 级别 |
| --- | --- | --- | --- |
| [`packages/core/src/state/actions.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/core/src/state/actions.ts) | 1–35、53–60、84–108 · `Action / reseed / rollDice / buyLand / buyStock` | 所有输入转成带类型动作；宿主显式注入种子；操作接口独立于 UI | B |
| [`packages/core/src/state/reduce.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/core/src/state/reduce.ts) | 1–10、383–405、1602 起、6996 起 · `MapTopology / reduce / reduceAll` | 不可变状态归约；地理静态数据与动态产权分开；重放完整动作 | B |
| [`packages/core/src/state/replay.test.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/core/src/state/replay.test.ts) | 28–112 · `record / 1000 次同种子重复 / reduceAll` | 测试定义覆盖确定性、录制与分段重放；未独立执行 | B |
| [`packages/core/src/rng/policy.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/core/src/rng/policy.ts) | 16–26、43–61、73–99 · `SINGLE_PLAYER_POLICY / MULTIPLAYER_POLICY` | 单机按时机重播种但不持久化随机状态，联机仅开局播种且保存随机状态；两种语义不同 | B |
| [`packages/core/src/net/acting-seat.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/core/src/net/acting-seat.ts) | 21–41 · `actingSeat` | 被动卡持有者或拍卖当前出价者可以不是回合主人 | B |
| [`packages/core/src/net/sequencer.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/core/src/net/sequencer.ts) | 1–15、65–151 · `Sequencer.submit / submitSystem / since` | 批准前校验、再发连续序号；源文件自认不抵御恶意客户端；不能断章理解为服务器永不运行规则 | B |
| [`packages/server/src/room.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/server/src/room.ts) | 120–146、217–286 · `Room / Sequencer / reduce mirror` | 实际服务端持有状态镜像，用 reduce 校验非法动作，并保存按序指纹；修正 sequencer 顶部简化注释 | B |
| [`packages/client/src/net-client.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/client/src/net-client.ts) | 190–202、459–480 · `NetClient.submit / defaultWsUrl` | 客户端只发送意图，等服务器广播；WebSocket /ws 和同源反向代理依赖运行中服务器 | B |
| [`packages/server/src/hub.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/server/src/hub.ts) | 637–710、1619–1672、1804 起 · `RoomHub / replay / room start / submit` | 房间、座位、重连重放与 AI 接管都是需要在线服务的系统 | B |
| [`packages/client/src/host.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/client/src/host.ts) | 1–22、30–47、239–315 · `assetBase / saveStore` | 浏览器 /assets/game 与 Tauri rich4 协议分流；浏览器 localStorage 存档；不满足单靠 Pages 自备原作资产即玩的条件 | B |
| [`packages/desktop/src-tauri/src/lib.rs`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/desktop/src-tauri/src/lib.rs) | 543–574、632–672 · `run / rich4 自定义协议 / bundled_game_dir` | 大 MKF 用异步 URI 读而非 IPC；运行期寻找原版素材；镜像桌面包不带素材 | B |
| [`packages/desktop/src-tauri/tauri.conf.json`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/desktop/src-tauri/tauri.conf.json) | 27–50 · `bundle` | bundle 项中未声明 resources，和镜像说明一致 | B |
| [`packages/assets-pipeline/src/cli-extract.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/assets-pipeline/src/cli-extract.ts) | 113–181 · `extractAll` | 从本机 MKF 解出精灵、地面图、FLIC 帧等，只有存在原始归档才能产出资源 | B |
| [`packages/data/src/source-fidelity.test.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/data/src/source-fidelity.test.ts) | 1–16、29–65 · `hasSource / describe.skip / parseTable` | 在外部 rich4-re 缺失时直接跳过真值对照；源码比对测试存在不等于在镜像执行过 | B |
| [`packages/core/src/loaders/savegame.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/packages/core/src/loaders/savegame.ts) | 1–18 · `new save format / importOriginalSave` | 自有 JSON 存档与原版二进制只读导入分开，降低固化 x86 布局的耦合 | B |
| [`vitest.config.ts`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/vitest.config.ts) | 1–17 · `RICH4_WORKSPACE` | 原版可对照目录由外部环境变量提供，缺失则相关测试跳过 | B |
| [`.github/workflows/build.yml`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/.github/workflows/build.yml) | 1–13、31–53 · `check` | 镜像脚本说明 assets 缺失、跳过素材用例、绿灯不意味着保真；仅源码与工作流声明未亲自跑 | B |
| [`docs/audit/provenance-summary.md`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/docs/audit/provenance-summary.md) | 1–35、38–68 · `六区溯源审计` | 作者分级列出 exe 地址、修正、approx、follow-up；本次未获取原版 exe 独立校核这些地址 | C |
| [`docs/acceptance/net-20260919.md`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/docs/acceptance/net-20260919.md) | 1–49、62–120 · `net W-40` | 作者记录两标签页联机、断线恢复、修复拍卖座位死锁；属于上游测试报告非研究者实测 | C |
| [`docs/handoff.md`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/docs/handoff.md) | 8–40 · `镜像/测试边界` | 交接承认 code-only git filter-repo、私有真实资产和差分资料、CI 跳过 / 未真机验收 | C |
| [`README.md`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/README.md) | 1–20、53–59 · `项目自述 / 许可` | 原版标称《超时空之旅》v3.11 (2001)，GPL-3.0-or-later，归功 mytbk/rich4；并非 1998 基础版本的独立验证 | C |
| [`LICENSE`](https://github.com/oama1111/rich4-remake-public/blob/42ad97ad31f07541a9af35415e36be4da4147484/LICENSE) | 1–18 · `GNU GPL version 3` | 仓库有 GPLv3 许可证正文；版本授权取 README / package.json 的 -or-later 声明 | B |

## 可复核操作与未执行项

从完整原版素材、自行合法取得的资源和 Node 22 / pnpm 工作区出发，上游所述命令：`pnpm install --frozen-lockfile`、`pnpm check`、`pnpm dev`、`pnpm --filter @rich4/desktop build`。**这些命令均未由本研究在上游代码上实际执行**，不得把作者验收数字标为独立测试。

实际环境：Node `v22.16.0`，npm `10.9.2`，`pnpm` 未安装；`git ls-remote https://github.com/oama1111/rich4-remake-public.git HEAD` 尝试失败（`Could not resolve host: github.com`）。研究改走具有授权的 GitHub 仓库读取接口，对固定提交读取公开源文件和树；没有原作 MKF、原版 EXE、私有 `rich4-spec` 或 `rich4-re` 外部文件，所以不能进行原作差分、浏览器实际游玩、Tauri 包安装、截图、独立性能和多人真机验收。报告中的作者测试日志是 C，不是 A。

检查链路：上游目录树包括 `packages/core/`、`packages/client/`、`packages/desktop/`、`packages/data/`、`packages/server/`、`docs/acceptance/`；但没有公开 `assets/game/`、`rich4.exe` 或 `rich4-spec`。相关路径存在与否以固定提交的完整树为准，不凭本地安装状态推断完整软件不可构建；**可构建 ≠ 可独立开局或验证原作**。
