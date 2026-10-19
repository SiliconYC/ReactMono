# lhr0909/richman4-remastered：原生移植、可玩性与界面保真深度研究

> ReactMono [Issue #97](https://github.com/SiliconYC/ReactMono/issues/97)｜研究时间：2026-10-19（UTC）｜证据定义与机器索引见 [source-index.md](source-index.md)、[evidence.json](evidence.json)。本报告只评估外部开源实现，不转入外部代码和原版商业素材，**不构成独立试玩、原版忠实度认证或商业分发许可**。

## 一、研究身份与复现基线

| 项目 | 事实与证据 |
| --- | --- |
| 外部项目 | [lhr0909/richman4-remastered](https://github.com/lhr0909/richman4-remastered)；默认 `main`；GitHub 标注非 Fork，但技术血缘来自 mytbk/rich4 [E01、E17] |
| 固定版本 | **`3f4209a7dfb5b2f20799bf54e6c03c5faa11c557`**，提交时间 **2026-10-06 02:20:39 UTC**；研究时核查 HEAD 即该 SHA，不能以仓库页面“最近更新”冒充新提交 [E01] |
| 产品/环境 | C++20、SDL3、FreeType、FluidSynth、原生 macOS ARM64；Android ARM64 APK 与 iOS 模拟器/设备工程；不是 React/Web/PWA [E02、E13、E14] |
| 授权 | 根目录 `LICENSE` 为 GNU GPL 第 3 版文本；源码 SPDX 与法律声明采用 **GPL-3.0-or-later**，版权素材及原版文字另受限制 [E17、E18] |
| 执行状态 | **只做固定 SHA 的远端源码、构建配置、测试定义与文档独立核查（B）；未克隆编译、未执行上游测试或真机安装（A=无）**。当前执行环境缺少自有原版 MKF/EXE、构建所需 Mac SDK/设备和可访问上游的本地源码环境；公开仓库中也没有可重放的私有验收原始数据 [E20] |

原版要求原始 v3.11 光盘素材；Steam 版资产未逐一比对。上游的 `game-assets/` 只有导入指引，**没有可直接运行的正版媒体文件**，Android/iOS 打包会将使用者自己的资源打入安装包，不能公开再分发。见 [game-assets/README.md:1–56](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/game-assets/README.md#L1-L56)、[NOTICE.md:8–46](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/NOTICE.md#L8-L46)。[E18]

## 二、产品目标、原版与二创边界

项目明确旨在把 **1998 年《大富翁4》** 的规则、原始 640×480 画面、人物、音画、操作时序重建成不依赖 Win32/Wine 的本机应用（原始程序/素材需使用者自己提供）。它是**忠实原版意图的跨平台原生重写**，不是《大富翁4》资料片，也不是新的 3D 棋盘游戏。宣称的“重制”依赖原版 MKF、MIDI、WAV、FLC 和转录文字来实现原貌；**独立忠实程度未证实**。上游的“约 15.8 万行汇编转 3.2 万行 C++”为作者统计而非功能百分比，不能作为视觉/游戏完成度分数。[E02、E03、E17]

ReactMono 则是纯静态 Pages/PWA、React/TypeScript 规则核心 + Three.js 原创现代街区视效和简体中文界面。两者产品形态不同：前者的价值是原作行为与素材索引线索；后者**不能以复制原版 640×480 图像代替商业级 Q 萌 3D 表现**。[E21]

## 三、代码架构、边界与数据流

- **规则层**：`src/game.cpp` 的 `GameSession::Impl` 管理 `World`、`Random`、阶段、`GameDecision`、事件/特效、电脑轮次；`src/cards.cpp`、`src/tools.cpp`、`src/stocks.cpp`、`src/stocks_ai.cpp`、`src/minigames.cpp` 处理独立子系统。[E04、E05、E08、E09]
- **原格式世界/存档**：`src/save.cpp::SaveFile::decode` 对 0x26 格式标识、1–4 位玩家及地图范围进行结构核验；`src/world.cpp::World::from_save` 映射状态；`validate_playable_world` 作语义入口验证。`tools/native_game.cpp` 存 `.DAT` 与随机状态 `.rng`，两次独立写入，不是单个事务。[E10]
- **呈现与输入**：`tools/native_game.cpp` 是 SDL 宿主；`tools/screens/main_screen.cpp` 对原版图标栏、四类信息、可转小地图/全图、日历与 GO/骰子提供**真实代码路径**；`tools/screens/items.cpp`、`tools/screens/stocks.cpp` 映射各类 UI；`src/board_renderer.cpp` 渲染原始精灵/建筑；`src/flc.cpp` 处理过场格式。逻辑事件排入 `presentation_`，前一个动画/讯息未结束时暂停下一阶段展示，避免骰子和人物表现穿插。[E06、E07、E11]
- **平台包装**：macOS 原生程序依赖系统库；Android 通过 Gradle/NDK/SDL Activity，首启解包私有 MKF；iOS CMake+Xcode 将资源放进 app bundle，两个移动平台将存档放到应用私有目录。脚本拉取第三方库并核对 SHA-256（见第三方声明）。[E13、E14]

### 六条端到端调用链（B：源码结构，**没有本次实际执行**）

| 链 | 从输入到核心再到结果 | 重要验证边界 |
| --- | --- | --- |
| 新局、地图与原生绘图 [E04] | `new_game` → `World::from_map_resource` → `validate_playable_world` → `GameSession`/`board::Renderer` → `observe` 事件 → `draw_board`；[tools/native_game.cpp:913–1014](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L913-L1014) | 世界载入入口存在；不证明八图素材均可用 |
| 掷骰、步行与队列 [E05] | SDL GO/键盘 → `roll_dice` → `GameSession::tick` → `start_step/complete_step/land` → `drain_events/drain_effects` → `pump_presentation` → 主屏人物/特效；[src/game.cpp:4052–4117](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L4052-L4117) | 顺序控制可审；“手感与原版一致”仍未验证 |
| 卡片、道具及目标 [E08] | `Screens::draw_inventory` 触控网格 → `GameSession::use_card/use_tool` → `legal_card_targets/apply_card` 或 `tools::use` → 规则事件 → 气泡/特效；[src/game.cpp:3749–3818](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3749-L3818) | 可核对合法性和目标校验；不证明 26 卡和 13 道具均由真人触发 |
| 股市、交易及电脑 [E09] | `StockMarket` 买卖点击 → `stock_actions`/`trade` → `GameSession::buy_stock/sell_stock` → `stocks::buy_stock/sell_stock`；AI `begin_ai_turn` 调 `stocks_ai::buy/sell`；[tools/native_game.cpp:1751–1775](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1751-L1775) | 按源码证实行情限制、交易和 AI 存在；经济原版对照为上游报告 |
| 存档、读档 [E10] | `save/write_save` → `GameSession::export_save` → `World::export_save` → DAT+RNG；`load` → `SaveFile::decode` → `World::from_save` → 世界校验 → 安装会话；[tools/native_game.cpp:1015–1053](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1015-L1053) | 只在阶段允许时存档；DAT 与 RNG 未跨文件原子提交 |
| 三种互动小游戏 [E11] | 地块 6–8 → `DecisionKind::mini_game` → `MiniGames::begin/draw_decision/input` → 企鹅/气球/天降 → `submit_mini_game` 回写点券、共享随机数消耗；[src/game.cpp:3342–3359](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3342-L3359) | 仅开启动画且人类操作时互动；无人回放用自动奖励，不能拿来验真人体验 |

## 四、规则、视觉、交互与验证覆盖矩阵

下表 **“源码可证”仅表示存在可追溯实现 B**；“作者声称 C”不等同独立 A；“部分”包含明确缺口或尚无真实体验证据。

| 功能 | 覆盖判定与定位 | 证据 |
| --- | --- | --- |
| 开局、八图、人物行动与地产结算 | **源码可证、体验未知**；存在世界初始化、回合/动画步进、土地经营与结算；八图 30 天为作者验收脚本目标，不是本次八图跑通 | E04 E05 E15 |
| 原版主界面、工具栏、地图转向与小地图 | **源码可证、像素保真未验**；`MainScreen::draw_toolbar/draw_info_panel/draw_minimap/draw_go` 已实装。10/5 “缺小地图”是历史信息 | E06 E16 |
| 人物动作、FLC/过场、音频与语音 | **部分**；FLC、效果序列、WAV/MIDI 混音和语音接口存在；**原版 23 个 AVI 是占位视频**，真实听感与逐帧比对未独立核查 | E07 E12 E16 |
| 卡片、13 种道具、商店、神明、特殊事件 | **源码可证、覆盖声称**；26 个主动卡、13 道具经代码分发；20/20 全覆盖仅上游 10/6 自述 | E08 E15 E16 |
| 银行、股票、股息、贷款、交易、拍卖与彩票 | **源码可证、部分偏差**；银行/股市和买卖流存在；界面细节与原版数值对照不等于完整游戏等价 | E09 E16 |
| 三个小游戏 | **源码可证但操作体验未验**；有人类触控与自动化快捷模式，自动模式不等于真人完成三个游戏 | E11 |
| 存档、五手动槽与自动档 | **源码可证、跨文件一致性有风险**；解码/语义校验、六槽 UI、自动档可见；`can_save` 限制托管中途存档 | E10 E16 |
| 电脑 AI/托管 | **源码可证、长期策略未知**；股票/卡/道具 AI 真实调用；10/6 托管状态与 `set_ai_settings` 对上，10/5 “无法托管”过时 | E09 E16 |
| Android APK、触控、后台存档 | **工程链可证；真机完成仅作者声称**：OnePlus 8 安装和音效由作者报告，未有本轮可复用设备日志 | E13 E15 |
| iOS 模拟器、XCUITest、真机 | **工程与测试脚本可证；模拟器成功仅作者声称；真机明确未测**；XCUITest 仅菜单→新局→棋盘→GO 并非全局验收 | E14 E15 |
| 自由设定胜负、投降、完整原版 AVI、Steam 素材相容 | **已知未完成/未知**，来自 10/6 状态和配置；无凭据断定其他未知功能不存在 | E16 E18 |
| 原版全面对照、现代商业级 3D 画面 | **未独立验证/不属于其目标**；原版用传统 640×480 商业素材；和 ReactMono 现代化新美术不能按截图等价推论 | E19 E21 |

**关键时序**：10 月 5 日曾“43/43 CTest、19 个子例各通过但总矩阵因卡 17 缺失而失败，20 个案例只跑了 5 个就中止”，这些都由 [docs/migrations/031-native-acceptance.md:137–160](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/docs/migrations/031-native-acceptance.md#L137-L160) 与旧文档明确记载 [E15]。**10 月 6 日** `docs/STATUS.md` 顶部宣称 `d00cb9a` 时刻 **47/47 CTest + 20/20 验收及 Android 真机运行**，并明确要求旧“暂停记录”当历史阅读。两个时间点的结论不能简单二选一；**新结果也没有在公开 Git 仓库附上原始运行报告供第三方检验**。[E15 E16 E20]

## 五、五项深入源码发现与可审查性

1. **演出顺序由事件/特效单队列驱动，不只是加动画。** `observe` 按 `after_events` 交错入队，`pump_presentation` 每次等上一段演出完成，`present` 消费声音/人物消息；同一核心 `tick` 可生成多个逻辑事件，因此队列是避免 “AI 下回合骰子越过上一回合演出” 的必要解耦。[tools/native_game.cpp:1062–1149](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1062-L1149)。[E07]
2. **动作规则与交互选择共用明确的合法性入口。** 卡片检查玩家背包、可用市场/目标和回调，再统一处理分支；工具限制 1–13 号、库存及目标/落点；这比只在 UI 中隐藏按钮更稳，但还未证明所有边缘行为与原 EXE 相同。[src/cards.cpp:250–287](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/cards.cpp#L250-L287)、[src/game.cpp:3752–3818](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3752-L3818)。[E08]
3. **“原版存档兼容”与运行时无损恢复是两个不同命题。** `SaveFile::decode` 检查布局，`World::from_save` 恢复对象，`validate_playable_world` 校验可用世界，`write_save` 才是持久化；原生随机数另外写 `.rng`。崩溃发生在两文件写入之间可能恢复不一致；上游源码没有显示跨文件事务。[src/save.cpp:86–106](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/save.cpp#L86-L106)、[tools/native_game.cpp:1015–1053](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1015-L1053)。[E10]
4. **小游戏区分“同一个规则事件”的真人模式与无头模式。** `kind=6..8` 对人类玩家按设置进入模态游戏；关闭动画或电脑玩家直接使用随机点券结果；真人游戏另按真实交互消耗随机数并返写。用无头自动对局“测过小游戏”会漏掉触控、画面、节奏。[src/game.cpp:3342–3359](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3342-L3359)、[tools/screens/minigames.cpp:139–190](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/screens/minigames.cpp#L139-L190)。[E11]
5. **移动端“能编出工程”不等于无需原游戏的公开可玩安装包。** 安卓打包检验本机 `Data.mkf` 并抽取 `rich4.exe` 图标，iOS 将游戏资产直接入包；脚本确有签名、资源、自检和真机命令，但真机测试结果缺少公开运行产物，且版权声明限制传播。[scripts/build_android.sh:62–80](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/scripts/build_android.sh#L62-L80)、[scripts/build_ios.sh:84–108](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/scripts/build_ios.sh#L84-L108)。[E13 E14 E18]

## 六、ReactMono 的借鉴与拒绝项（按效益与成本）

| 优先级 | 借鉴或拒绝 | 价值 / 工作量 / 兼容性 | 核对路线及反面边界 |
| --- | --- | --- | --- |
| P0 | **按规则事件封装“气泡→音效→动画→下一回合”的演出队列** | 高 / 中 / 很适合规则与 React 表现分离 | 在 ReactMono 的 `src/core/game.ts`、`src/ui/game-ui.tsx` 和 `src/demo3d/` 之间对真实事件加序号、可跳过等待与重载恢复测试；**不能直接粘贴 GPL 的 C++** [E07 E21] |
| P0 | **采用按功能和输入来源拆开的严苛验收矩阵** | 高 / 中 / 适合纯无头规则 + 浏览器 | 保留“自然开局”与“人为合成卡/道具/终局”分组，要求**真实使用**而非背包出现即覆盖，明确总门槛失败；结合 Chromium / Android 浏览器 UI 实操，不继承上游 20/20 结果 [E15 E20] |
| P1 | **规则合法性与跨系统存档校验前置** | 中高 / 中 / 适合 TypeScript 事件引擎 | 审阅 ReactMono `src/core/cards.ts`、`src/core/stocks.ts`、`src/core/save.ts` 的边界，编写畸形存档和分支中断用例。**不要照抄“双文件 DAT+.rng”**，应尽量把 RNG 与游戏状态放到同一版本化存档事务 [E08 E10 E21] |
| P1 | **建立“原作行为→本地规则差异→玩家价值”逐项证据表** | 中 / 低中 / 研究兼容 | 按股息、建造、神明、小游戏等读取原版装置/逆向证明，但只有版本、功能与真人复现充分时再决定是否调整 ReactMono；“作者已复刻”不能直接变为产品需求 [E03 E09 E11] |
| 拒绝 | **照搬原版 640×480、原作受保护素材/声音、GPL 源码和手机侧载架构** | 对现有现代化 3D 美术是负价值 / 高版权风险 / 不兼容 | ReactMono 继续原创 Q 萌 3D、静态 Pages/PWA、简体中文交互；上游大量原版文字、MKF 依赖和非网页原生 SDK 均不是可直接复用资产 [E17 E18 E19 E21] |

以上为**候选工程建议，不是已发现 ReactMono 缺陷或已实施功能**；若未来拟立 Issue，必须先在对应现存模块/页面进行独立缺口复核，避免重复建设。

## 七、差距、风险、证据冲突与许可证

**文档时间冲突**：`docs/STATUS.md` 10/6 开篇修订了 10/5 的暂停列表，并写明旧记录仍保留；同时 `docs/audit/panel-jump-help.md`、`audio-map.md` 等仍有“缺小地图、小游戏、救护车”等当期 B gap，现行 [tools/screens/main_screen.cpp:275–301](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/screens/main_screen.cpp#L275-L301)、[tools/screens/minigames.cpp:139–190](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/screens/minigames.cpp#L139-L190) 已有相应代码。审核应将审计视为 **当时的问题清单**，逐条标记“源码已补/仍缺/未验证实际效果”，不能照抄成现行缺陷，也不能因为代码存在就断言问题已视觉验收 [E06 E11 E12 E16]。

**作者统计不等于第三方通过**：`47/47` 并非固定编译环境里的必然用例数——CTest 的原版资源和金标项受输入条件控制；`20/20` runner 既检查自然地图也检查合成存档，还带 `original_full_game_equivalence_verified:false`。即使公开补齐整套新报告，也只证明脚本范围，不等于原版连续完整对局、真实购买者体验及现代设计验收。旧 10/5 失败和 10/6 声称成功都应原样保留。[E15 E20]

**产品真实缺口**：10/6 自列胜利/时间/投降选项未启用、23 AVI 占位、圣诞节二图赠卡差异、托管中存档限制、魔法屋对象选择差异、部分文字只写日志、iOS 实机未测、Steam 资源未比对。没有本次 Mac 原生全局截图、合法对照素材或玩家逐页实测，**视觉完成度与人机手感无法给可靠的定量结论**。[E16]

**法律与血缘**：GitHub metadata 显示 `fork=false`，**不是**源码独立原创的证明；README、`THIRD_PARTY_NOTICES.md` 认定规则/画面资料直接承袭 `mytbk/rich4` 的逆向成果（参照锁定版本 `ec7d70e...`），原作程序和 UI 资料具有自身权利。此移植引擎源文件为 GPL-3.0-or-later，其文本抄录等被明确排除在 GPL 游戏源码许可外；衍生复制若进入 ReactMono 必须另做许可证兼容性/合规审查。只有概念、事实性算法比较及独立重新设计适合当前研究，不应拷贝上游源码、原版脚本、图像/音频；普通个人“拥有正版”**不代表拥有转分发授权**。[E17 E18]

## 八、五维有证据评分（0–5；无充分证据为 null）

评分是**固定版本的保守静态审计适用度，不是游戏产品综合分，也不是原作保真比例**。

| 维度 | 分数 | 证据 / 置信度 |
| --- | --- | --- |
| 原版规则覆盖 `rules` | **3/5** | B 中：土地、股市、26 主动卡、13 道具、存档、AI 与小游戏可定位；但无本次原版同局重演，作者又列胜利条件/节庆偏差 [E04 E05 E08 E09 E11 E16] |
| 代码可维护性 `maintainability` | **3/5** | B 中：引擎、平台、界面和细分测试分层清楚，仍有巨大的 `src/game.cpp` 与 `tools/native_game.cpp` 单元、原版格式耦合与平台打包复杂度 [E04 E07 E13 E14] |
| 独立可复现性 `reproducibility` | **1/5** | B/C 高：有脚本、固定种子、严格验证入口，但需要用户私有商业游戏素材与原版金标、各平台 SDK/设备；公开成果不含原始 47/47/20/20 日志，本轮无法实跑 [E15 E18 E20] |
| 画面与交互完成度 `presentation` | **null** | C/D 低：屏幕实现和资产映射可查，但缺合法可复用的同状态截图/真人逐页对照；不以函数存在推算观感 [E06 E12 E16 E20] |
| ReactMono 实用价值 `reactmono_value` | **3/5** | B 中：可参考测试矩阵、规则隔离、演出节奏、原作行为；不能直接使用 GPL 代码和受保护素材，目标图形/端侧明显不同 [E07 E10 E15 E17 E21] |

## 九、结论与下一步

**建议：`read_only_reference`（只读研究参考，不直接移植）。** 当前可以肯定存在具体、连贯的原生游戏及 UI 实现路径，且比仅有设计稿或模拟器结构更深入；但尚**不能独立确认**其 10/6 报告的完整游戏可玩性、原版画面逐帧保真、真机体验或 47/47 和 20/20 的最新真实性。特别不能把 10/5 失败当成 10/6 仍然失败，也不能把 10/6 作者声明升级为本研究 A 级。[E04 E06 E15 E16 E20]

后续若取得**合法自有 v3.11 素材**和 Mac ARM64/Xcode/Android 设备：固定 `3f4209a7dfb5b2f20799bf54e6c03c5faa11c557`、记录素材哈希/第三方下载 SHA，再本地独立执行 CTest 与 20 场 runner；随机挑 3–5 个同存档的原版/原生 UI 状态做截图并人工审查，另做 Android 实机音频/后台档和 iOS 真机。详见 [source-index](source-index.md) 的具体命令。剩余问题：最新成功的 20 场原始 `summary.json` 是否可去商业资料后公开？47 个 CTest 的具体配置和金标来源是什么？23 个 AVI 占位能否合法替换？官方 Steam 数据和 v3.11 的格式差异？iOS 真机完整局是否可操作？GPL 与文字摘录的分发边界是否经权利人确认？这些全部保留为**待证实**，不生成空的新 Issue。[E15 E16 E17 E20]
