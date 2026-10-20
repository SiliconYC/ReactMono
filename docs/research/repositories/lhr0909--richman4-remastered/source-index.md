# lhr0909/richman4-remastered 固定源码索引与复核手册

**上游**：https://github.com/lhr0909/richman4-remastered  
**默认分支**：`main`；**本次锁定**：`3f4209a7dfb5b2f20799bf54e6c03c5faa11c557`  
**提交时间**：2026-10-06T02:20:39Z；**检查时间**：2026-10-19 UTC；**ReactMono 任务**：[Issue #97](https://github.com/SiliconYC/ReactMono/issues/97)  
**证据等级**：A 独立执行（本次无）；B 固定 SHA 源码/脚本核查；C 作者文档自述；D 推断。E01–E21 与 [evidence.json](evidence.json) 同号。URL 定位至**固定 SHA**，并非会移动的 `main`。

## 文件与证据锚点

| ID/级别 | 证据主题 | 上游位置（固定 SHA） | 审核含义与限制 |
| --- | --- | --- | --- |
| E01 / B | 版本与来源 | [`README.md:1-36`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/README.md#L1-L36) | GitHub commits/HEAD 定位固定提交；与仓库 GitHub fork 元数据结合判断，不把“非 fork”理解为无继承 |
| E02 / B | 构建模块 | [`CMakeLists.txt:1-106`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/CMakeLists.txt#L1-L106) | 核对 C++20 核心、SDL 依赖、分条件启用的测试列表；无用户原作资源只能按无资产方式尝试 |
| E03 / C | 作者规模说法 | [`README.md:48-71`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/README.md#L48-L71) | 15.8 万行 x86 汇编与 3.2 万行 C++ 为上游统计，与用户验收和原作一致率无数学对应 |
| E04 / B | 新局安装世界和渲染 | [`tools/native_game.cpp:913-1014`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L913-L1014) | new_game → World::from_map_resource → validate_playable_world → GameSession/Renderer；见 src/world.cpp:590–714 |
| E05 / B | 回合、骰子、AI 及步进 | [`src/game.cpp:513-756`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L513-L756) | start_turn → begin_ai_turn 或 human_ready，GameSession::roll_dice 3743–3747，tick 4052–4117 |
| E06 / B | 原版主屏具体实现 | [`tools/screens/main_screen.cpp:275-303`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/screens/main_screen.cpp#L275-L303) | draw_toolbar/info/minimap/calendar/GO/dice/full_map；另见 338–552；旧文档“缺小地图”是历史 |
| E07 / B | 演出顺序和声音 | [`tools/native_game.cpp:1062-1149`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1062-L1149) | drain_events/effects 按 after_events 合并，队列按序 present 及 audio/Effects；前一展示完毕再向后推进 |
| E08 / B | 卡片、道具及合法操作 | [`src/game.cpp:3749-3818`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3749-L3818) | use_card 交给 src/cards.cpp:250–287 的 apply_card；use_tool 交给 src/tools.cpp；UI tools/screens/items.cpp:310–355 |
| E09 / B | 股票成交到核心、AI | [`src/game.cpp:3825-3858`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3825-L3858) | UI tools/screens/stocks.cpp:143–195 → native_game.cpp:790–799/1763–1775 → stocks::buy_stock/sell_stock src/stocks.cpp:160–245；AI game.cpp:601–645 |
| E10 / B | 本机存档结构和脆弱点 | [`tools/native_game.cpp:1015-1053`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1015-L1053) | .DAT 与 .rng 分别保存；src/save.cpp:86–106 校验签名；src/world.cpp:174–200；src/world_validation.cpp:70–228；game.cpp:4167–4174 |
| E11 / B | 三类小游戏动态路径 | [`src/game.cpp:3342-3359`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3342-L3359) | 人类互动的 DecisionKind::mini_game 与无人回放奖励分支；tools/screens/minigames.cpp:139–190/270–315；GameSession::submit_mini_game 4038–4050 |
| E12 / B | 原版界面与旧审计 | [`docs/ui/main-screen.md:25-70`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/docs/ui/main-screen.md#L25-L70) | 对照 docs/ui/{finance-menus,cards-tools-shops,effects,mini-games,messages}.md 与 docs/audit/*.md；各自可能保留当时缺口，需复查当前实现 |
| E13 / B | Android 打包入口 | [`scripts/build_android.sh:62-80`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/scripts/build_android.sh#L62-L80) | 本机 MKF 与 EXE 图标前置、Gradle 装包/adb；android/app/src/main/cpp/rich4_android.cpp:101–161 首启复制素材与配置目录 |
| E14 / B | iOS 包与模拟器触控脚本 | [`ios/uitests/Rich4TouchTests.m:31-63`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/ios/uitests/Rich4TouchTests.m#L31-L63) | 触摸菜单、开新局、GO、后台恢复测试定义；脚本 scripts/build_ios.sh:84–108，准备目录 ios/rich4_ios.mm:39–77；仅脚本不证明跑过 |
| E15 / B | 20 场验收定义及严格总门槛 | [`scripts/run_native_acceptance.py:23-65`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/scripts/run_native_acceptance.py#L23-L65) | 20=八地图自然 30 天 + 四库存 + 五目标动作 + 终局 + 恢复 + 交易；有效操作覆盖而非库存含卡；详见 236–261、264–330 |
| E16 / C | 10 月 6 日作者最新声称与旧日志 | [`docs/STATUS.md:1-27`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/docs/STATUS.md#L1-L27) | 10/6 47/47、20/20、Android OnePlus 8/iOS simulator；之后 10/5 旧历史段保留失败/暂停；最新声称原始本地日志未公开 |
| E17 / B | 许可证与技术血缘 | [`THIRD_PARTY_NOTICES.md:1-33`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/THIRD_PARTY_NOTICES.md#L1-L33) | 源码 SPDX/NOTICE 采用 GPL-3.0-or-later、mytbk/rich4@ec7d70e...、依赖许可证；LICENSE 是 GPL-3 许可文本，另见 NOTICE.md |
| E18 / B | 商业资源/商标/文字分发边界 | [`NOTICE.md:1-75`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/NOTICE.md#L1-L75) | 不带原版 MKF/可执行档；但转录原版台词和名称仍为商业权利；个人使用构建含原版资源不可公开分发 |
| E19 / D | UI 主观保真程度不定 | [`docs/ui/effects.md:1-58`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/docs/ui/effects.md#L1-L58) | 有原版 FLC 功能与界面规格，但公开仓库缺同状态原版 vs 原生独立截图，不能据静态代码断言全幅保真 |
| E20 / B | 作者验收可复现条件与界限 | [`docs/migrations/031-native-acceptance.md:137-160`](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/docs/migrations/031-native-acceptance.md#L137-L160) | 10/5 原始 19 场 aggregate failed、20 场仅 5 场 interrupted；10/6 新成果没有公开的 summary.json；测试编排 tests/native_acceptance_tests.py 用 mock，并非原生端到端本轮运行 |
| E21 / B | ReactMono 产品边界（本仓库 dev） | [`../../../../README.md:1-20`](https://github.com/SiliconYC/ReactMono/blob/dev/README.md) | 本项目 dev 的 README/AGENTS/PROJECT_CHARTER、src/core、src/ui、src/demo3d；原上游不是 React 3D/PWA，遵守现有产品约束 |

## 跨模块端到端检查（只读、非运行）

1. **开局与地图**：https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L913-L1014 `Application::new_game` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/world.cpp#L590-L714 `World::from_map_resource` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/world_validation.cpp#L70-L93 `validate_playable_world` → `Application::install_session` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1456-L1515 `draw_board`。这里验证调用方传入 `decode((stage*4+map)*2+1)`，不是八图纹理的真实截图。[E04]
2. **GO→掷骰→走格→演出**：https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L505-L515 识别输入并 `roll_dice` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3743-L3747 → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L4052-L4117 状态推进 → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1132-L1149 读取事件/特效 → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1062-L1095 按序展示 → `draw_board`。[E05 E07]
3. **卡片与道具**：https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/screens/items.cpp#L310-L355 网格触摸 → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3749-L3818 `use_card/use_tool` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/cards.cpp#L196-L287 `legal_card_targets/apply_card`、`src/tools.cpp` `tools::use` → 主画面播放相关消息/效果。26 张主动卡和 13 道具全执行属于测试目标，不是本研究实测。[E08 E15]
4. **股市与 AI**：https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/screens/stocks.cpp#L143-L195 买/卖回调 → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L790-L799 `stock_actions` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1763-L1775 `trade` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3825-L3858 交易验证 → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/stocks.cpp#L160-L244 买卖结算。另 https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L601-L645 `begin_ai_turn` 自主调用 `stocks_ai`、卡片策略。[E09]
5. **存读档**：https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1040-L1053 `Save1.DAT`+分离的 `.rng` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L4167-L4174 `can_save/export_save` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/world.cpp#L378-L413 `World::export_save`；读取路径 https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/native_game.cpp#L1015-L1038 `load` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/save.cpp#L86-L106 `SaveFile::decode` → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/world.cpp#L174-L200 `World::from_save` → `validate_playable_world`。**DAT 和 RNG 非跨文件事务。**[E10]
6. **小游戏与点券**：https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L3330-L3359 `land` 分发 6–8 类地块 → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/screens/minigames.cpp#L139-L190 创建 Penguin/Balloon/Catcher → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/tools/screens/minigames.cpp#L270-L315 真实触摸分支 → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/game.cpp#L4038-L4050 结果提交并结束回合；关闭动画时只做自动点券结算。[E11]
7. **Android/iOS 平台依赖**：https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/scripts/build_android.sh#L62-L80 APK 构建/安装 → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/android/app/src/main/cpp/rich4_android.cpp#L101-L161 解资源+私有存档；https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/scripts/build_ios.sh#L84-L108 iOS 签名/构建 → https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/ios/rich4_ios.mm#L39-L77 bundle/资源/保存路径；https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/ios/uitests/Rich4TouchTests.m#L31-L63 模拟器交互脚本。**脚本存在不是实际设备通过。**[E13 E14]

## 作者声明与历史暂停核对

- 2026-10-05 历史：https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/docs/migrations/031-native-acceptance.md#L137-L160 的 **19/19 单场通过但 aggregate failed（缺卡 17）**，增加第 20 场后仅跑完前五场即 **interrupted**。https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/docs/migrations/validation.md#L84-L112 仍反映 43/43 的旧时点，不能推论后来必失败。[E20]
- 2026-10-06 最新作者口径：https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/docs/STATUS.md#L1-L28 记载 **47/47 CTest、20/20 验收、Android OnePlus 8 真机、iOS 模拟器**。这是明确的 C 级历史自述；不在公开 Git 树内提供对应新的完整 `summary.json`、`ctest.log`、`.xcresult` 等第三方可复用报告。[E16]
- 因而本研究 **没有将 47/47 或 20/20 标记为 A**；上游静态代码存在并不能代替音画原版对照及真人完整局。[E15 E16 E20]

## 独立复现指令与前置条件（本次**未执行**）

本环境不能直接从 GitHub 克隆上游并缺少版权素材、macOS SDK/移动设备；以下是上游指定的**未来执行办法，不是本次测试日志**。全部文件应保存在测试者自己的忽略目录，禁止上传原版商业素材/构建产物。

```sh
git clone https://github.com/lhr0909/richman4-remastered.git
cd richman4-remastered
git checkout --detach 3f4209a7dfb5b2f20799bf54e6c03c5faa11c557
git rev-parse HEAD
# 将自己合法持有的 v3.11 原版文件复制到 game-assets/，勿入 Git
python3 scripts/audit_assets.py
# macOS/Apple Silicon + Homebrew: brew install cmake sdl3 freetype fluid-synth
cmake -S . -B build/native -DCMAKE_BUILD_TYPE=Debug -DRICH4_SANITIZERS=ON
cmake --build build/native --parallel
ctest --test-dir build/native --output-on-failure
# 只有使用者依法持有原版游戏及需要的原版金标时，才执行完整专用验证
python3 scripts/run_native_acceptance.py \
  --binary build/native/rich4-native.app/Contents/MacOS/rich4-native \
  --fixture-binary build/native/rich4-native-fixture \
  --game game-assets --output artifacts/native-acceptance/independent-20261019
# 真机条件满足后，Android: scripts/build_android.sh <adb-serial>
# iOS: scripts/build_ios.sh --run "iPhone 16 Pro"
# iOS device 需 Xcode、Apple 签名团队及实际 iOS 装置
```

**应留存而本次不存在的 A 级材料**：完整输入清单/哈希、版本化本机工具链、CTest 全部用例详情、单次 20 场汇总 `summary.json` 与失败/运行日志、真实 UI 比较图及录像、Android APK 本机运行/音频与后台恢复日志、iOS `.xcresult` 和实机安装证明。虚拟显示 `SDL_VIDEODRIVER=dummy` / `SDL_AUDIODRIVER=dummy` 的 30 日自动回放不能单独证明人类视听体验、对局胜负流程或相机/文字保真。

## 不依赖商业素材的独立验证路线（本次未执行）

为避免误把资源缺失当成所有测试均无法运行，可先在有 C++20、CMake 与 Python 的可联网环境运行（注意这只是**未来建议命令**，本研究未运行）：

```sh
cmake -S . -B build/core-only -DRICH4_BUILD_GAME=OFF -DRICH4_BUILD_VIEWER=OFF -DBUILD_TESTING=ON
cmake --build build/core-only --parallel
ctest --test-dir build/core-only --output-on-failure
```

CMake `RICH4_BUILD_GAME=OFF` 可以绕过 SDL3/FreeType/FluidSynth 的游戏宿主依赖，但测试注册仍依 `Python3`、本地资源和 `RICH4_ORACLE_DIR` 配置变化；此路线不能检验原版画面、原生音频、Android/iOS 或 20 场完整验收。避免将测试数量与作者在另一环境的 `47/47` 直接比较。

## 法律与污染隔离

- 代码 GPL-3.0-or-later；实际 `LICENSE` 是 GNU GPLv3，`NOTICE.md` 具体界定作者/版权来源；`mytbk/rich4` 的公开逆向证据索引点为 `ec7d70e693059d1e781d9d1cc2ad7f36d360d39e`，但 GitHub 元数据 `fork:false`，应标记为“技术派生，非平台 fork”。[E17]
- `game-assets/`、原版 `rich4.exe`、MKF/MIDI/WAV/AVI、移动端含原版资源的 APK/IPA 均不允许纳入 ReactMono；上游转换的对白、上市公司名称不因源库 GPL 自动取得正版授权。[E18]
- 实操命令不应该凭空运行或发布供公众下载的版权包。查阅公开文本/函数不意味着可以复制代码到 ReactMono；应自行编写全新 TypeScript 行为和视觉。[E21]

**索引验收**：所有外部固定源码锚点采用同一个 SHA；索引与报告不提供原版游戏的二进制、纹理或伪造测试输出。原始对照文档可能滞后 10/6 最新源码，核查时先比日期再判定状态。
