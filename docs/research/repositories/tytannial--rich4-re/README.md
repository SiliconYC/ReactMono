# tytannial/rich4-re：原版机制重建与 SDL3 测试审计

> Issue [#96](https://github.com/SiliconYC/ReactMono/issues/96)｜审计基线 [`b7b76570f445](https://github.com/tytannial/rich4-re/tree/b7b76570f445ad07c0788314062b8500e77259e7)｜证据等级：B=固定版本源码核查，C=作者陈述，D=待验证；**没有将上游作者的“测试通过”计为 A 级独立复现**。代码锚点详见 [source-index.md](source-index.md)，逐项证据见 [evidence.json](evidence.json)。

## 1. 研究身份与复现基线

- 研究对象：[tytannial/rich4-re](https://github.com/tytannial/rich4-re)，GitHub 默认分支 `main`，固定 SHA `b7b76570f445ad07c0788314062b8500e77259e7`，提交时间 **2026-10-05 12:41:36 UTC**（最后公开提交）；研究检查日 **2026-10-19 UTC**。GitHub `fork=false`，当前无公开 Release；不等于没有代码继承。
- 形式：C++17 / CMake / SDL3 / FreeType；入口 `src/main.cpp` → `Application::init` / `gameInit` / `enterGameLoop`。版权声明为 [MIT LICENSE](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/LICENSE)，第三方库及原版素材**不在 MIT 的授权承诺范围内**。[B01,B02,C01]
- 上游 [README](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/README.md) 将目标描述为 1999 年 i386 PE 原版兼容性重建；本 Issue 把原作识别为 1998 年《大富翁4》。这是**年份/版本口径差异**，不能仅凭此推断实现面向资料片；具体版本需要游戏发行史和资源校验另证。[C01,D01]
- 环境：研究者可用 Linux x86_64、CMake 3.31.6、Ninja 1.12.1、GCC 14.2；未安装 SDL3 / FreeType 开发包，`git ls-remote https://github.com/tytannial/rich4-re.git HEAD` 失败（`Could not resolve host: github.com`）；通过已授权 GitHub 文件接口逐文件审计固定 SHA。既无可用外网 Git 克隆/FetchContent，也无合法原版 MKF、可用 SDL3 及字体，**未编译、未运行上游 L0/L1、未实际游玩、未生成截图**。[D02]
- 核验方法：读取上游完整 Git tree（非截断，423 条 tree entry），静态检查 `src` / `include` / `tests` / `tools`、CMake 与 CI 配置；按 SHA 核对案例内容，不把代码“存在”提升为体验验证。[B02,B12]

## 2. 产品目标与原作关系

本项目是围绕旧 `rich4.exe` 反汇编地址重建规则与绘制的**原版导向兼容实现（`original_relation=faithful` 指意图而非证明完全忠实）**。它并非 ReactMono 所追求的全原创风格化 3D 游戏；上游倾向重用合法自备的 `Data.mkf` / `Panel.mkf` 等商业素材，原版地址/偏移贯穿注释和逆向文档。不能将它的画面重现视作可直接合法发行的自有美术资源。[B03,C01]

血缘调查：GitHub 元数据标记 `fork=false`；上游树是 `src/app/game` 等 C++ 文件及反汇编档案，而 [mytbk/rich4](https://github.com/mytbk/rich4) 的已核查树主要为 `asm/rich4*.asm`、`asm/rich4*.c`，后者 [GPL-3.0](https://github.com/mytbk/rich4/blob/master/COPYING)。搜索本上游默认分支未找到 `mytbk` 文字引用。**这只支持“不是平台 fork、工程组织不同”，不支持“已证明独立创作、零复制、MIT 一定无冲突”**：两者共享原版逆向对象；是否有函数/表格逐字迁移、共同第三方代码或历史私有来源，仍需逐函数与版权链鉴定。[B14,D03]

## 3. 代码架构与数据流

| 环节 | 可追溯实现 | 实际性质 |
| --- | --- | --- |
| 程序初始化 | `src/main.cpp` 解析 `--game --headless --seed --quickstart --script`；`application.cpp` 启动 SDL；`game_init.cpp` 装载 MKF [B02,B03] | 强依赖本地资源及 SDL 窗口，非浏览器独立部署 |
| 规则模型 | `include/game/game_state.h`，`src/app/game/turn_system.cpp` 处理格子、行动、神明/结算；`economy.cpp` 处理转账及破产 [B04,B05] | 规则是 C++ 状态机，仍耦合 `Application` / 弹窗 / 声音及阻塞演出 |
| 股票/银行 | `stock_system.cpp`、`bank_dialog.cpp`、`bank_stay_dialog.cpp`、`month_settle_dialog.cpp`、`dividend_dialog.cpp` [B06] | 交易、市场波动、账本与 UI 共存，不宜直接搬到纯函数内核 |
| 卡牌/道具/AI | `card_effects.cpp` / `item_effects.cpp`；`src/app/ai/ai_card.cpp` / `ai_item.cpp`；回合 AI 入口 [B07] | 有实质目标选择分支，不等于已独立测出策略强度 |
| 资源到画面 | `src/resource/{mkf,lzhuf,spr,smp}.cpp` → `src/render/{fli,iso_blit,surface,ui_image}.cpp` → `map_render.cpp` / SDL [B03,B08] | 原版位图/精灵/动画的像素级复现，不是 Three.js 几何资产管线 |
| 存档 | `src/app/game/save_data.cpp` 序列化 `SAVE*.DAT` 与回合快照 [B09] | 面向旧二进制结构；没有网页 JSON/PWA 存档契约 |
| 验证 | `tests/unit/*.cpp` / `tests/scenarios/*.txt`、`tools/run_tests.py`、`docs/testing.md` [B10–B13] | L0 含纯函数检查；L1 无头脚本仍依赖原版资源；Trace 与规则断言应分开 |

运行时数据路径：`gameInit` 打开 `Data.mkf` / `Speaking.mkf` / `Panel.mkf` / `Effect.mkf`；新局 `loadMap` 进一步读 `map.mkf`，`MkfArchive::read` 解压条目；逻辑在 `GameState` 中推进，再由原版映射关系和 `Surface` / `FliDecoder` 绘制。`--headless` 会设 SDL dummy 驱动与虚拟时钟，**不代表它在缺 MKF 的情况下也能完成开局**。[B03,B08,B11]

## 4. 功能与规则／视觉／交互／验证矩阵

“证实”仅指**B 级确认存在具体代码路径**；“部分”说明有实现但端到端效果/细节不足；“未知”表示未取得可独立判断的证据。C 级自述列在另栏，不折算成功率。

| 系统 | 静态证据与状态 | 验证强度 / 未覆盖 |
| --- | --- | --- |
| 新局、地图、投骰、过天、NPC/AI 回合 | **部分**：`new_game.cpp`、`turn_system.cpp`、`game_loop.cpp` [B04] | `00_smoke` 有状态断言；复杂回合/全局胜负没有本次实跑 [B11,C01] |
| 住宅地产、同路段联合租金、连锁/同盟 | **证实代码存在**：`estateRouteRent`、`landingEvent`、`transferMoney` [B04,B05] | `test_rent.cpp` 有独立数学期望；`20_rent_route` 检查现金减少，但非原版数据比对；`72_chain_rent` 检查 trace 金额 [B10,B12] |
| 商业地产、设施、旅馆、企业点 | **部分**：`landingEvent` 对 `corp/specPt` 分支及对应对话框 [B04] | `60_corp_gas` / `84_specpt_fee` 存在；未确认真实原版可视体验 [B12] |
| 银行、贷款、月息、分红、股市 | **部分**：`transferMoney`、`stockTick`、`buyStock` / `sellStock`、UI [B05,B06] | `226_stock_trade` 等待交易日志但只断言 `errors==0`；`268/270` 等待 AI 日志且只断言 errors，不能代替持仓/余额精确不变量 [B12] |
| 30 卡 / 13 道具 | **部分**：效果分派与 AI 目标函数有实质实现 [B07] | 场景覆盖种类多、部分有状态断言；没有本次执行记录或与原版逐项差分 [B12,C01] |
| 神明、新闻、命运、事件、迷你游戏 | **部分**：`turn_system.cpp` 特殊格分派、`fate_event.cpp`、`card_effects.cpp` [B04,B07] | `50_god_free_rent` 查现金不变；**`68_news_fate` 只有 wait trace，没有 `assert`**，无法证明事件业务结果 [B12] |
| 二进制存读档、自动存档、快照 | **部分**：`saveGameToSlot` / `parseSaveBody` [B09] | `246_save_load` 强校验改写现金后恢复；`test_save` 无素材就 `SKIP`，L0 绿灯并不证明与旧档兼容 [B10,B12] |
| 原版渲染/音效/动画、宽屏 | **部分**：`FliDecoder` / `Surface` / `SDL_RenderTexture`、文本/布局 [B08] | 未实跑、无本项目截图；开场/结局 **AVI TODO** [B13]；商业级观感**未知** |
| 现代浏览器、Pages/PWA、移动触摸 | **未知/目标不相符**：`SDL_CreateWindow` 本地原生应用 [B03] | 代码和构建配置不是 React 浏览器端；不宣称“移动不可实现”，只是未见可交付端侧证据 |

## 5. 深挖源码的五项定位发现

**发现 1：联合租金的“路段”按名称而非拓扑邻接。** `estateRouteRent` 扫全体地产，对住宅使用 `owner + name + type=0` 联合累加 `fees[level]`，连锁店改为全图同地主数量乘 2000，再乘 `moneyMul`；测试构造三块相同路名 400+800+200=1400 与跨街连锁 4000。这里的可借鉴对象是**可配置的纯计算契约**，不是地图邻接算法。[B04,B10]

**发现 2：收租为多收款人流程，不是“现金一减一加”。** `landingEvent` 先检查地主收租资格，处理神明、同盟比例、免付/嫁祸/死神代付；`transferMoney(flags=0)` 默认现金优先扣、收款入银行，并有破产与月度流水。若 ReactMono 简化为固定“支付给一名所有者”，将与此类原版情境不同；但本次并未证明其每条分支与原版完全一致。[B04,B05]

**发现 3：市场和存档数据结构有可测试边界。** `stockTick` 遍历 12 支股票、交易停牌/新闻动量、保留 144 期历史；`saveGameToSlot` 按顺序写四角色、地图表、股票记录、快照，再由 `parseSaveBody` 对称读。最有价值的是**字段顺序、状态生命周期与定长数组作为差分用例依据**；旧 `SAVE*.DAT` 的“逐字节兼容”只属作者说明，本轮无合法旧档重测。[B06,B09,C01]

**发现 4：伪无头测试不等于资产无关。** `--seed`、`dbg::raw` 单次注入、`setVirtualClock`、SDL dummy 驱动和脚本式状态/Trace 断言有实质代码；但 `gameInit` / `loadMap` 仍在开局读取原版 MKF。99 份 L1 场景文件是完整的**测试清单**，不是 99 次独立 PASS。官方 CI 仅两平台编译及 `ctest -R unit`，未在无素材环境运行 L1。[B03,B10,B11,B12]

**发现 5：测试数量掩盖断言类型差异。** `246_save_load` 修改资金再读取以断言恢复，能检验业务状态；`112_stock_smoke` 核对对话框/点击 trace 和通用 errors；`268_ai_stock_buy` 只是等待日志并断言错误计数为零；`304_music_resume` 全是音频请求 trace；`68_news_fate` 完全没有 `assert`。此外 `test_save` / `test_mkf` 缺资源直接 `SKIP` 退出而不计失败；原仓库宣称绿色矩阵的含义必须拆开读。[B10,B12]

## 6. 对 ReactMono 的具体借鉴（含否定意见）

| 优先级 | 可复现契约/借鉴 | 价值与成本 | 适配与明确不采纳 |
| --- | --- | --- | --- |
| P0 | 从 `estateRouteRent` 提炼“相同路名地块联合租金 / 连锁店 / 同盟分账 / 免付”的**输入-事件-资金不变量**；为不同种子生成 fixtures | 高价值、中成本 [B04,B05] | ReactMono 现有 `src/core/game.ts` / `maps.ts` 为纯 TS 规则及环形地图，**当前没有按原版名称联算**；先提可选规则提案，不暗改当前原创经济 |
| P0 | 对照“现金优先 + 存款补足 + 收款入银行 + 破产时实际支付量”的资金流守恒表；引入精确状态前后校验 | 高价值、低至中成本 [B05] | ReactMono `src/core/bank.ts` 现为每完成一轮计息，与上游“月初结息”**机制不同**；不用直接照搬上游利率/节奏 |
| P1 | 借鉴脚本 `seed` / 一次性 `rng` 插桩 / `assert state` / `assert no trace`，把业务断言与界面 Trace 分开，落到现有 Node / Chromium 测试 [B10–B12] | 高价值、中成本 | 保留 ReactMono 已有固定种子和测试框架；不要为了“99 场景”移植专用 DSL |
| P1 | 用源代码定位的“功能核验表”：每项包含规则状态、视觉请求、实际玩家画面三个不同证据门槛 [B12,B13] | 中价值、低成本 | 上游只验 trace 的场景不能当画面合格证；ReactMono 原创 3D 继续保留真实浏览器验收 |
| **不采纳** | 移植 SDL/FLC/MKF 渲染、原版素材、`SAVE*.DAT` 二进制格式或直接翻译 C++/GPL 代码 [B03,B08,B09,B14] | 成本高、许可/架构风险高 | 与 React + Three.js + Pages/PWA + 本地 JSON 存档方向冲突；**仅整理行为事实，独立编写 TS 测试** |

ReactMono 的当前源码证据：`src/core/cards.ts` 仅列 `reward/stride/remote/roadblock/rent_free` 五种卡，与上游“30 卡”不是等价覆盖；`src/core/stocks.ts` 使用五个原创报价，`src/core/bank.ts` 的结息节奏和上游不同；`src/core/maps.ts` 是 24/20 格环形拓扑。这些是**差异，不自动定性为缺陷**：原版忠实模式须由产品 Issue 单独批准。[B15]

## 7. 缺口、风险与证据矛盾

1. 作者 README 和上游 AGENTS 宣称“30 卡、13 道具、99 帮助项全实现”“完整存档兼容”“99 L1 场景”，源码确实存在大量路径，但**本次无 A 级编译、跨平台、完整对局或原版逐帧比较**。[C01,B07,B12]
2. `src/app/game/new_game.cpp` 的 `playIntro` 留有 “intro AVI playback skipped”，`src/app/game/victory.cpp` 的全图结局分支写有 “AVI playback TODO A5”。这是可定位的实际未实现项，故不得声称**完整音画复刻**。[B13]
3. L0 无资源自动 SKIP：`test_save.cpp`、`test_mkf.cpp` 缺私有数据便跳过，CI“绿”只证明真正执行过的单测；完整资源/存档回归不能靠该绿灯作证。[B10,B11]
4. 没有本次实际音频、手感、移动性能、分辨率观感或真人整局证据；SDL 本地窗口不是原生浏览器游戏。[B03,D02]
5. MIT 声明**不覆盖原版商业素材**；与 GPL `mytbk/rich4` 的关系尚未证实为代码级派生或完全独立，引用反汇编结论、复述游戏规则、复制受保护源代码必须区别处理。[B14,D03]
6. README 的“1999 原版”与本仓库任务的“1998 原作”口径未对齐；不要将扩展版、后期发行版及原版行为无证据合并。[D01]

## 8. 五维评分（0–5，非作者打分）

| 指标 | 评分 | 证据 / 置信等级 |
| --- | --- | --- |
| 原版规则覆盖 `rules` | **4.0** | B04–B07/B09：模块广、细节能定位，但无原版差分证明；**B，中** |
| 代码可维护性 `maintainability` | **3.5** | B02/B08/B11：源文件按职责拆分，CMake、基础测试齐；大型 `turn_system.cpp` 4452 行且 Application 耦合；**B，中** |
| 独立可复现性 `reproducibility` | **2.0** | B03/B10/B11/D02：可见构建/测试代码，但当前无合法素材、依赖与可联网编译环境；**B + 限制，中** |
| 画面与交互完成度 `presentation` | **null** | B08/B13：存在渲染代码也存在 AVI TODO，**无实测截图及完整玩家操作**；**不足以评分** |
| ReactMono 实用价值 `reactmono_value` | **4.0** | B04/B05/B10/B12/B15：经济/状态测试契约很强，复制美术/架构不合适；**B，中** |

分数是本次审计的证据性判断，不是原版忠实程度百分比，不计算总分。

## 9. 结论与下一步

**结论：`read_only_reference`（只读行为与测试契约参考），不进行源码或素材移植。** 优先独立设计“同路段联合租金/同盟结算”的 TS 差分用例，再建立银行和股票的日期边界、自动存档恢复与演出 Trace / 真画面分层用例。原版行为应从多份逆向证据交叉验证，不能以单个 C++ 项目当“真值机”。[B04,B05,B09,B12,B15]

未解决：上游有无可公开分发的不含商业素材的样例 fixtures；`SAVE*.DAT` 不同发行版本的字节等价程度；与 `mytbk/rich4` 的逐函数/表格来源；游戏中 “99 帮助项”哪些已受端到端**状态**断言检验；L1 真实资产条件下的无头画面/音频及多平台表现。后续应在独立 Issue 中做多源原版规则核验及 ReactMono 可选规则测试，不借 #96 修改游戏逻辑。

本 Issue 验收及受阻环境、具体路径、重试命令详见 [source-index.md](source-index.md)；以上“代码证实”均不表示上游运行成功。
