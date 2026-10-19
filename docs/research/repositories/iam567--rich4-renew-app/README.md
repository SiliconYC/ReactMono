# iam567/rich4-renew-app 深度研究：TypeScript 引擎、规则与手机封装

> Issue [#98](https://github.com/SiliconYC/ReactMono/issues/98) · 范围：**仅研究，不修改 ReactMono 游戏代码** · 结论：**只读技术参考**。本文中「源码实现」只表示固定 SHA 下存在可追溯代码；不等于真实运行、原版忠实度或商品级观感。

## 1. 研究身份与复现基线

| 项目 | 结果 |
| --- | --- |
| 研究对象 | [`iam567/rich4-renew-app`](https://github.com/iam567/rich4-renew-app)；[Issue #98](https://github.com/SiliconYC/ReactMono/issues/98) |
| 默认分支 / 锁定提交 | `main` / [`1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79`](https://github.com/iam567/rich4-renew-app/commit/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79)（完整 40 位） |
| 提交时间 / 检查时间 | 2026-10-18 17:34:57 UTC / 2026-10-19 01:22 UTC（GitHub API + 文件逐份读取） |
| GitHub fork 标志 | `false`（这只表示 GitHub 没把它标成 fork，不排除技术/规则来自其他仓库） |
| 源码版本 / 最新已查公开安装包 | `game/package.json` = `0.2.2`、`CHANGELOG` 记录 0.2.2；截至检查时 [Releases](https://github.com/iam567/rich4-renew-app/releases) 最近安装包 `v0.2.1`；查询 `v0.2.2` 发行标签返回 404 |
| 许可 | [`LICENSE`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/LICENSE) 为 GNU GPL v3 正文；README 和 package 指定 `GPL-3.0-or-later`，GitHub 元数据识别为 `GPL-3.0`；素材另有授权边界 |
| 执行环境与成绩 | 使用 GitHub 连接读取**固定提交的源码/测试/发行元数据**。本地 Linux 沙盒 `git ls-remote` 失败：`Could not resolve host: github.com`；未能独立克隆、安装依赖、执行 npm/Vitest、开浏览器或装手机 App，**A 级实测为 0，截图为 0** |

上游仓库根目录为 `game/`（TS 游戏）、`docs/rules/`（研究者规则文档）、`editor/`（仅留少量编辑器路径）等；完整递归 Git 树 382 个条目（`truncated=false`）。已读取 `game.ts`、`world.ts`、地产与经济模块、地图解析、存档、UI、移动打包脚本及多种 Vitest 断言。原始规则文档本身属于**作者的研究陈述**，不能因为写了反汇编函数名就自动升为第三方验证。

上游提供的复现路径是 `cd game && npm ci && npm test && npm run build && npm run dev`；**这里是复现计划，不是运行日志**。此前需要先提供 `game/public/assets`。相关完整定位见 [source-index.md](source-index.md)，逐事实证据见 [evidence.json](evidence.json)。

## 2. 产品定位及与 1998 年《大富翁4》的关系

它是一个**原作规则导向的现代二次重制 + 自创玩法**，并非原程序移植、也不是可视为《大富翁4》原作权利的自由软件版本。上游 README 自称根据原版反汇编恢复规则，代码中有大量 `fcn_...` 和 `rich4_*.asm` 注记；可确定的是源码保留了这些作者声称的对应关系，**本轮没有独立拿原版执行轨迹验证一一等价**。

必须分开三层：

- **原作机制的代码级覆盖**：八个旧地图的数据入口、传统单地图回合、地产升级、银行/股票、原作 30 卡与 13 工具、神明/NPC、电脑托管、存档，均有源码路径。这说明功能不是仅在 README 声称，但不证明复刻精度。
- **明确的重制改动**：`REMAKE_CARD_POOL` / `REMAKE_SUPPLY` 改变卡池（原表总 100 张，重制版基础牌总 102 张）；`REMAKE_FREE_BUILD` 改变免费加盖；`blackmarket.ts` 注释明确以黑市替代原版交易板；播种方式也改为可重复日随机数。源码的「原作规则」和实际默认开启的改版规则不可混用。
- **纯新内容**：自制东京/大阪/札幌/九州/冲绳地图、跨五城的 **12 人大富豪模式**、第六张「大富翁城」决战、歌舞伎町独立场景及老虎机/游戏厅等。参见 `world.ts`、`finale.ts`、`kabukicho.ts`；不能算入 1998 原版的规则覆盖率。

上游历史文档、标记及素材可能帮助定位原作证据，但**血缘不能只靠作者的一段来源说明**。仓库不是 GitHub fork；`THIRD_PARTY.md` 提到 `mytbk/rich4` 的反汇编和原样 Git 子模块，实际当前完整文件树里没有 `.gitmodules` / `upstream/rich4`。需要历史提交或上游具体引用 SHA 才能核对真实继承关系，当前不据此判定侵权或违规。

## 3. 代码架构与实际数据流

```text
game/index.html
  → ui/main.ts: setup / begin / start / resume
    → ui/assets.ts: 从 assets/maps/*.json + 图片加载地图
    → core/board.ts: parseBoard(十六进制原始记录 → Board 图)
    → core/game.ts: Game.run() / playerTurn() 生成 Flow<Step/Ask>
      → Stocks / Cards / Tools / Objects / Events / Places / BlackMarket / Forks
    → ui/main.ts: 等待玩家回答、消费 Step / 播动画
    → ui/board-view.ts: HTML Canvas 2D + DOM/HUD
    → ui/saves.ts: IndexedDB 槽位 ↔ core/save.ts 状态序列化
特殊模式：core/world.ts（五个 Game + 全国玩家与交通）→ finale.ts
特殊地区：MAP_RULES → kabukicho.ts（地图自己的事件）
```

**主要优点是规则与显示解耦，而非 React 复用性。** `Game.run` 与 `playerTurn` 以 generator 生成事件/提问，UI 在 `ui/main.ts` 的异步循环中等待回答、用 `BoardView` 播放掷骰、购买、收租等动画。无头测试可以用程序自动回答 `Ask`。`Game` 构造器实际实例化并初始化股票、卡牌、道具、事件、地点等子系统；`world.ts` 为五座城市各建一份 `Game`，共享全国 12 人及卡池，未显示城市照样跑规则（源码和测试定义分别见 S09/S18）。

**地图仍有原版格式约束。** `board.ts` 用 `DataView` 解原始二进制字段、`TextDecoder('big5')` 转名字，节点引用规则以 2001/4001/6001 分组；地图 `width` 可超过传统 2304。扩展地图依赖外置素材中的 `maps/remake/index.json` 与地图 JSON，**并不是仓库里附带可直接装载的地图包**。本轮读到 `kyushu.test.ts` 对 3456 宽、213 节点的断言定义，不能冒称测试已通过。

**端侧组合**是 Vite 7 + TypeScript 5.9 + Vitest 3.2 + Canvas 2D/DOM + Capacitor 7（iOS/Android 原生外壳）；`vite.config.ts` 使用 `base: './'`，为离线包/相对路径服务。没有 React、Three.js 或现成可移植到 ReactMono 的三维美术管线。手机横/竖屏经 Capacitor screen-orientation 插件处理，语言用简繁切换模块；IndexedDB 的七个槽位中普通 AUTO = 0、大富豪 AUTO = 6，刚好回应其 0.2.2 更新日志关于覆盖自动存档的问题，但**未实测修复有效**。

**打包链**：`npm run build` = `tsc --noEmit && vite build`；`npm test` = `vitest run`；`npm run package` 调用 `package.mjs`，同步 Capacitor，再通过 `gradlew assembleDebug` 制 APK 或 Xcode 生成**未签名** IPA。需大体积私有素材和 Android SDK/JDK 21、或 macOS Xcode。IPA 未签名不表示普通 iPhone 可直接安装。

## 4. 功能完成度矩阵（只限本轮证据）

「证实」= B 级固定 SHA 的代码存在且能追溯，不等于 A 级实际玩通；「部分」= 有核心实现但关键环节缺验证。「未知」= 未得足够证据而非确认没有。

| 领域 | 判断 | 固定源码证据与边界 |
| --- | --- | --- |
| 新局、回合、骰子和胜负 | **证实（源码）** | `Game.constructor/run/playerTurn`；真实连续整局未独立运行（E01–02） |
| 旧地图读取、路径和建图 | **部分** | `parseBoard` 实际解析字节；地图 JSON 外置，未测试视觉放置（E07/E12） |
| 地产买入、建造、街区收租 | **证实（源码）** | `landOnLot/calcToll`；默认含改版建造规则（E03） |
| ATM、银行贷款、银行控制及融资 | **证实（源码）** | `atm/bankCounter/financeReserve/financeRecall` + bank.test 数值断言（E03/E15） |
| 股票、公司、价格、停牌/交易 | **证实（源码）** | `Stocks` 状态与交易方法；地图相关测试有资产缺失跳过开关（E04/E16） |
| 卡片和道具 | **证实（源码）** | 30 基础卡/13 基础道具和处理器，包含额外卡/工具（E05/E06） |
| 神明、特殊对象、NPC 和新闻 | **部分** | `Objects/Events/Places` 槽表与逻辑；命运动画/原作偏移未独立复核（E06/E07） |
| 电脑对手/托管 | **部分** | `playerTurn`/模块 `aiUse`/跨城 `aiTravel`；策略好坏、真人对局未知（E02/E08） |
| 普通存档 | **证实（源码）** | `saveGame/loadGame` + `save.test` 逐状态继续的断言定义（E10/E15） |
| 大富豪存档 | **部分** | `saveWorld/loadWorld`、独立 AUTO 槽；0.2.2 修复没有 A 级回归（E10/E13/E20） |
| 自制地图/歌舞伎町 | **部分** | `mapList` + `KabukichoRules`；实际地图与贴图不在 Git（E09/E12） |
| 五城 12 人「大富豪模式」 | **部分** | `World` 城市分身/旅行/跨城结算和 `world.test`，未实测 12 人终局（E08/E15） |
| 原版音画与现代 UI | **未知（质量）** | Canvas 2D、精灵加载和音频代码存在，**无独立截图、帧率、视口及审美验收**（E11/E12） |
| Android/iOS 端侧可用 | **作者发行声称 + 包装源码** | Release 有 APK/IPA，未签名 IPA，未实机装载；源码较发行包领先（E14/E20/E21/E23） |
| 原作 1998 年行为准确性 | **未知（忠实度）** | 注记及作者规则文件不是原版两端对照的 A 级证据（E17–19） |

不能把上述十余个「有实现」相加为「玩法完成率 X%」；研究没有完整的逐玩法已测分母、游戏内截图或真人样本。

## 5. 五项有源码锚点的深入发现

**① 可无头驱动的规则-视图事件合同，具有真实技术价值。** [`Game.run/loop`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L617-L653) 与 [`playerTurn`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L804-L877) 通过 `yield` 传递游戏事件及玩家问题，UI [`main.ts`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/ui/main.ts#L913-L1068) 异步翻译为动画。这允许 `world.test.ts` 比较有/无被观看城市时的运行状态；比把动画耦合在掷骰逻辑中更利于测试。**不意味着可直接复用它的 TS 源码**。（E01/E02/E08/E11）

**② 银行/股市是真规则，不是空 UI；但保留原作适配不确定性。** [`game.ts` 金融与收租](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L1320-L1470) 有行长融资和经营权变化；[`Stocks`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/stocks.ts#L137-L403) 有交易日/股票持仓与停牌；[`bank.test.ts`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/bank.test.ts#L53-L211) 写到特殊融资是否算债务、资金不足时经营者补足、经营权转移强制清偿，具针对性。**这些只是源码 + 断言定义，本轮未运行，更不是原版自动等价**。（E03/E04/E15）

**③ 「原版规则」与默认二创参数在同一引擎共存。** [`cards.ts`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/cards.ts#L37-L120) 基础卡 30、重制补牌合计 102，另增跨城牌；[`game.ts`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L227-L248) 公开默认重制开关；[`blackmarket.ts`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/blackmarket.ts#L1-L50) 则明示独立替换交易板。这是**实际偏离来源**，不应把作者写有原版反编译注释误当整套运行配置等同原作。（E01/E05/E17）

**④ 扩展世界不是换地图按钮。** [`World.constructor/sharePool`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/world.ts#L277-L340) 将地图规则引擎和共享 12 名玩家连接，跨城共享卡池，[`World.run/arrive`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/world.ts#L1085-L1162) 负责跨城回合和路途跳转；[`saveWorld/loadWorld`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/save.ts#L108-L235) 记录五座城不同经济状态。创新力度明显，但复杂性高，**不应以来源项目 0.2.0「完整可玩」更新日志代替 ReactMono 的容量/完成率验收**。（E08/E10/E20）

**⑤ 较丰富的测试代码存在「资源条件性跳过」风险。** [`stocks.test.ts`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/stocks.test.ts#L1-L114) 明确以 `existsSync(editor/site/assets/map-2.json)` 设置 `haveMaps`，再 `describe.skipIf(!haveMaps)`；[`kyushu.test.ts`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/kyushu.test.ts#L202-L229) 定义了 200 天 4 AI 回归。原始资产放在独立 [`assets` Release](https://github.com/iam567/rich4-renew-app/releases/tag/assets)，并不是仓库文件。因而「具备回归测试」可证，「在没有地图资源时也全部跑过」不可证。验收应同时报告 `passed/skipped` 数和地图数据前提。（E12/E15/E16/E21）

## 6. 对 ReactMono 的五项建议（按价值与实施负担排序）

| 取舍 | 对 ReactMono 可做的**独立实现** | 价值 / 难度 / 兼容性 | 验收要求 |
| --- | --- | --- | --- |
| **优先学习** | 统一规则命令→事件/提问→显示的接口，使一段无头录像能用同一数据驱动 Three.js 动画与快进模拟 | 高 / 中 / 高：现有规则引擎已分离 React，不需换技术栈 | 同一随机种子在无头和有图界面产生一致终态；存档前后事件一致 |
| **优先学习** | 将种子、经济状态、模块版本和旧档迁移做确定性回归；新增跨发布旧档样本，而非只测读写同版本 | 高 / 中 / 高：与现有 IndexedDB/PWA 兼容 | 既有版本存档真实迁移；在 2–4 人/多地图上继续完整对局 |
| **选择性学习** | 地图拓扑检查和数据驱动多地图：邻接、单向性、设施/公司引用、孤岛与路口压力模拟；不要沿用旧 255 节点或 Big5 原始格式 | 高 / 中 / 高：ReactMono 已有 JSON 地图/大型压力地图 | 24/20/16/60/120/360 格覆盖检查和无头压力测试，真实 Three.js 图面独立验收 |
| **谨慎参考** | 将「地区限定规则/独立扩展模式」设计为明确可开关模块，原版对照基线与原创规则完全分组 | 中 / 高 / 中：隔离后不破坏主程序规则 | 各模式单独验收，默认原版参考规则不受实验扩展污染 |
| **借鉴反例** | CI 必须披露跳过测试和素材依赖，设置最少**无素材**公共测试样本及有素材的单独验收；避免只看 exit 0 | 高 / 低 / 高：立刻可纳入研究/游戏验收纪律 | 记录实际执行测试量与跳过量；关键功能测试不得静默 skip |

**排除直接采用：** 其 Canvas 2D 精灵渲染、Capacitor 原生安装包依赖和巨量原版/重绘素材，不适合 ReactMono 已确定的 **React + Three.js 原创 3D + 静态 Pages + PWA** 方向。它的 `GPL-3.0-or-later` 代码也不能直接复制进本项目并假设许可问题消失。上面的「学习」只指原理、自行编码与自有测试样本，必要时进行法律审查。

## 7. 缺口、风险与说法核对

1. **不可复现的主要原因是素材与执行环境**：源代码不含 `game/public/assets`，`editor/site/assets` 是外部资源路径（固定树里该路径为符号链接），作者另发 [`rich4-assets.tar`](https://github.com/iam567/rich4-renew-app/releases/tag/assets)，约 **1,696,005,120 字节**。游戏加载 `assets/maps/maps.json` 和地图图片，缺失会报错；没拉取大包，不能生成任何真实游戏画面。当前沙盒的 GitHub DNS 不可达且无已安装上游依赖，连无素材 Vitest 也没有执行。**本轮没有任何独立运行/安装/截图声称。**
2. **发布与源码错位**：源代码和 `CHANGELOG` 是 0.2.2（包括大富豪存档修复），GitHub 当次最近发行安装包 `v0.2.1`，其中 Android `rich4-0.2.1.apk` **1,643,367,575 字节**，iOS `rich4-0.2.1-unsigned.ipa` **1,628,419,621 字节**；有安装包不等于装机运行结果。Android 打包脚本的 debug-signed 情况有代码对应，iOS 未签名需要另行签名。
3. **源码/素材许可边界**：[`README`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/README.md) 与 [`THIRD_PARTY`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/THIRD_PARTY.md) 自称资源源自《大富翁4》本地游戏和高清重绘，**明确不在代码 GPL 范围**；只有下载权限/个人使用说明，不能推定允许作为 ReactMono 的公共、美术商业资源。GPL 也对代码复制、衍生和传播有义务，须逐文件审核。别把「开源仓库」误解成「原版内容可自由用」。
4. **来源文件的疑点**：`THIRD_PARTY.md` 声称保留 `upstream/rich4` Git 子模块及其指针，但固定 SHA 的完整 Git 文件树中没有该目录或 `.gitmodules`。也许这是从另一个私有/历史工作树迁移后留下的说明；**现有证据只能认定文档与文件树不一致**，还不能定性实际代码引用深度或侵权。
5. **测评难题未消除**：拥有许多美术/UI文件、93 画面等更新日志自述，不代表桌面/手机上布局稳定、无卡顿或达到商业级审美。尚缺真实手指触控、屏幕安全区、iOS 后台音频、Android 安装、12 人跨城终局、长局存档、原版规则黄金样本的 A 级验证。上游自述与源码存在并不矛盾，但证据强度不同。

## 8. 五维评分（0–5，不造总分）

| 维度 | 分数 | 证据 / 置信度与解释 |
| --- | ---: | --- |
| 原版规则覆盖 | **3/5** | **B，中低**：银行/股市/30 卡/13 工具和回合有实代码（E01/E03–E06），但抽离原作基准、默认重制开关、未做原版对照；表示实现广度，不等于规则忠实度 60% |
| 代码可维护性 | **3/5** | **B，中**：核心模块与 Vitest 测例有分层（E01/E10/E15），但 `game.ts`、`world.ts`、UI 和独立大地图规则文件篇幅很大，状态模块仍紧密耦合，资产路径依赖较重 |
| 独立可复现性 | **1/5** | **B+C，中**：提供 npm/Capacitor 脚本及 release（E12/E14/E21），但必要素材外置 1.7 GB、一些测试会 skip，当前没有研究者运行证明；此分数评估复现门槛，并非断言构建失败 |
| 画面与交互完成度 | **`null`** | **资料不足**：Canvas/触控方向/发行包存在仅为 B/C，缺 A 级截图、帧率、实际手感与玩家独立评价（E11/E12/E20/E23）；禁止从宣传图臆测评分 |
| 对 ReactMono 的实用价值 | **4/5** | **B，中**：事件合同、可重复随机、多城状态组织、地图拓扑和测试跳过陷阱对现有方向有明确启发（E02/E07/E08/E10/E16），但应独立实现、不可移植原版美术/GPL 代码 |

评分不是实测完成度百分比，也不汇总总分；更多证据到来时应独立修订。

## 9. 结论、后续研究与交付验证

**推荐：`read_only_reference`。** 上游**不是空壳**：规则、五城游戏、测试断言与手机封装都有真实源码；在我们的权限/素材约束下却**不能证明已达到手机商品级可玩，也不能宣称与 1998 原作完全一致**。ReactMono 应借鉴**模块边界、确定性、地图校验和跨模式存档测试设计**，继续维持现有 React/Three.js/PWA 原创实现，不改动当前游戏代码，不分发上游 GPL 源码或原版资产。

**待办问题（建议先归入综合研究 #104，不自动扩张本 Issue）：** （1）找可合法分享且不含商业资源的规则黄金样本；（2）追溯 `THIRD_PARTY` 记载的 mytbk 子模块具体历史 SHA；（3）取得 0.2.2 的真实设备和完整终局测试记录；（4）报告有/无资产时 Vitest passed/skipped；（5）核查大富豪 12 人整局的移动端内存与读档。在没有独立 A 级证据前，这些均保持开放。

**研究产物验收边界**：本报告九章、[源码索引](source-index.md)（固定提交、函数与行号、可重跑命令）、[机器证据](evidence.json)（A/B/C/D、功能、数值/空评分和风险）彼此对应。固定文件路径已通过 GitHub 的仓库树/逐文件读取核查；JSON 创建前已解析并检查所有证据 ID 引用。未运行上游 Vitest、浏览器或真机，所以这里不列出虚构的通过数量。最终是否正式合并以 PR 验收及 `dev` 合并记录为准。
