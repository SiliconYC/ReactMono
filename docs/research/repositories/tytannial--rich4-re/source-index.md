# 源码索引、固定基线与验收方法

- 上游：`https://github.com/tytannial/rich4-re`；分支 `main`；固定 SHA `b7b76570f445ad07c0788314062b8500e77259e7`（UTC 2026-10-05 12:41:36，2026-10-19 核验）。
- 上游 Git tree：`https://api.github.com/repos/tytannial/rich4-re/git/trees/b7b76570f445ad07c0788314062b8500e77259e7?recursive=1`，`truncated=false`、423 项，`tests/scenarios/*.txt` **99**，`tests/unit/*.cpp` **9** 加 `microtest.h`（共 10 文件）。
- 本仓库比较基线：`dev@be88f92936e553bd369fe3c142394cd612659f5f`，研究任务 #96。GitHub 页面上方显示的“latest”会变化，以本文件带 SHA 的链接复核。
- 外部血缘对照：`mytbk/rich4@f81954d6a5675f63297036f9252720c6ca32a2b4`，其树主要为 `asm/rich4*.asm` / `.c` 与 `COPYING`（GPL-3.0）；上游 `fork=false`，未发现 `mytbk` 文字匹配并非无来源/独立创作证明。

## A. 必查源码锚点（B 级：实际读取固定 SHA 的代码，未执行程序）

| 证据 ID | 路径:行 | 行为判断与边界 |
| --- | --- | --- |
| B01 | [`LICENSE:1-21`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/LICENSE#L1-L21) | MIT 作者声明与授权条款（不推及原版资产） |
| B02 | [`src/main.cpp:30-149`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/main.cpp#L30-L149) | CLI/headless/seed/quickstart/script 解析 |
| B02 | [`CMakeLists.txt:1-113`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/CMakeLists.txt#L1-L113) | C++17、SDL3/FreeType、FetchContent、rich4_core/rich4_tests/ctest |
| B03 | [`src/application.cpp:22-112`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/application.cpp#L22-L112) | SDL 初始化、dummy 驱动、Surface/Freetype 与 gameInit |
| B03 | [`src/app/game/game_init.cpp:16-47`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/game_init.cpp#L16-L47) | Data/Speaking/Panel/Effect MKF 必需资源 |
| B03 | [`src/app/game/new_game.cpp:407-435`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/new_game.cpp#L407-L435) | 地图 MKF 与 MAPDAT 载入 |
| B04 | [`src/app/game/turn_system.cpp:982-1010`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/turn_system.cpp#L982-L1010) | estateRouteRent：同名路段、连锁店数与物价乘子 |
| B04 | [`src/app/game/turn_system.cpp:2042-2169`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/turn_system.cpp#L2042-L2169) | landingEvent 事件分派与关键格类型 |
| B04 | [`src/app/game/turn_system.cpp:2360-2420`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/turn_system.cpp#L2360-L2420) | 同盟租金、代付、转账、地主份额与记录 |
| B05 | [`src/app/game/economy.cpp:129-206`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/economy.cpp#L129-L206) | transferMoney 银行/现金顺序、收款方与破产 |
| B05 | [`src/app/game/economy.cpp:215-260`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/economy.cpp#L215-L260) | debt 和盟约状态 |
| B06 | [`src/app/game/stock_system.cpp:105-171`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/stock_system.cpp#L105-L171) | 12 股票、144 天循环、停牌/新闻及波动 |
| B06 | [`src/app/game/stock_system.cpp:262-330`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/stock_system.cpp#L262-L330) | 买卖与资金校验 |
| B07 | [`src/app/ai/ai_card.cpp:1224-1285`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/ai/ai_card.cpp#L1224-L1285) | AI 选卡目标分派 |
| B07 | [`src/app/ai/ai_item.cpp:620-745`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/ai/ai_item.cpp#L620-L745) | AI 道具选择及骰子调整 |
| B07 | [`src/app/game/card_effects.cpp:84-146`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/card_effects.cpp#L84-L146) | 实际卡片效果函数入口 |
| B07 | [`src/app/game/item_effects.cpp:375-477`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/item_effects.cpp#L375-L477) | 道具效果/放置入口 |
| B08 | [`src/resource/mkf.cpp:24-98`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/resource/mkf.cpp#L24-L98) | MKF offset/index 校验、条目解析与 LZHUF 读取 |
| B08 | [`src/render/fli.cpp:27-57`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/render/fli.cpp#L27-L57) | FLC 解码器入口 |
| B08 | [`src/render/iso_blit.cpp:11-65`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/render/iso_blit.cpp#L11-L65) | 等距菱形合成 |
| B08 | [`src/render/surface.cpp:12-58`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/render/surface.cpp#L12-L58) | XRGB1555 surface 到 SDL 纹理呈现 |
| B09 | [`src/app/game/save_data.cpp:453-548`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/save_data.cpp#L453-L548) | 旧版字段序/股票记录/地图与快照序列化 |
| B09 | [`src/app/game/save_data.cpp:549-684`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/save_data.cpp#L549-L684) | 存档字段解析 |
| B10 | [`tests/unit/test_rent.cpp:26-65`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/unit/test_rent.cpp#L26-L65) | 同街总额/连锁两店/倍率精确断言 |
| B10 | [`tests/unit/test_save.cpp:10-46`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/unit/test_save.cpp#L10-L46) | 缺档 SKIP / 有档进行回写与字节比对 |
| B10 | [`tests/unit/test_mkf.cpp:8-24`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/unit/test_mkf.cpp#L8-L24) | 无 Data.mkf 时 SKIP |
| B11 | [`tools/run_tests.py:44-98`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tools/run_tests.py#L44-L98) | headless seed/scenario 启动及 TEST asserts 退出码 |
| B11 | [`tools/run_tests.py:119-198`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tools/run_tests.py#L119-L198) | matrix 数量/报表/ctest 编排 |
| B11 | [`.github/workflows/tests.yml:1-48`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/.github/workflows/tests.yml#L1-L48) | 公共 CI 两平台 L0；L1 因私有素材未包含 |
| B11 | [`src/core/rng.cpp:13-21`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/core/rng.cpp#L13-L21) | 确定性伪随机序列 |
| B11 | [`src/core/clock.cpp:15-40`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/core/clock.cpp#L15-L40) | 虚拟时钟/延时免睡眠 |
| B12 | [`tests/scenarios/20_rent_route.txt:1-16`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/scenarios/20_rent_route.txt#L1-L16) | 收租时现金减少状态断言 |
| B12 | [`tests/scenarios/72_chain_rent.txt:1-14`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/scenarios/72_chain_rent.txt#L1-L14) | 仅检查转账 Trace 金额 |
| B12 | [`tests/scenarios/246_save_load.txt:1-21`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/scenarios/246_save_load.txt#L1-L21) | 234567→999999→读档回234567 |
| B12 | [`tests/scenarios/112_stock_smoke.txt:1-16`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/scenarios/112_stock_smoke.txt#L1-L16) | 股票 UI 点击 trace 与 errors==0 |
| B12 | [`tests/scenarios/226_stock_trade.txt:1-30`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/scenarios/226_stock_trade.txt#L1-L30) | 交易日志触发，但无股份/余额精确断言 |
| B12 | [`tests/scenarios/268_ai_stock_buy.txt:1-14`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/scenarios/268_ai_stock_buy.txt#L1-L14) | AI 买股日志出现但只断言 errors==0 |
| B12 | [`tests/scenarios/270_ai_stock_sell.txt:1-15`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/scenarios/270_ai_stock_sell.txt#L1-L15) | AI 卖股日志出现但只断言 errors==0 |
| B12 | [`tests/scenarios/304_music_resume.txt:1-13`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/scenarios/304_music_resume.txt#L1-L13) | 音乐事件全为 trace 断言 |
| B12 | [`tests/scenarios/68_news_fate.txt:1-13`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/scenarios/68_news_fate.txt#L1-L13) | 两处 wait trace、无 assert |
| B12 | [`tests/scenarios/50_god_free_rent.txt:1-16`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/tests/scenarios/50_god_free_rent.txt#L1-L16) | 神明免租现金不变的状态断言 |
| B13 | [`src/app/game/new_game.cpp:579-583`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/new_game.cpp#L579-L583) | intro AVI playback skipped |
| B13 | [`src/app/game/victory.cpp:399-418`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/src/app/game/victory.cpp#L399-L418) | 全图结局 AVI playback TODO A5 |

其他原版反汇编链交叉索引：
- [`docs/reverse/functions/41982d-estate-rent.md:12-80`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/docs/reverse/functions/41982d-estate-rent.md#L12-L80)：原版 `0x41982D` 与 `0x419744`、同盟分账、租金例外。
- [`docs/reverse/functions/41982d-estate-rent.md:83-150`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/docs/reverse/functions/41982d-estate-rent.md#L83-L150)：联合租金和地产类别/企业点。
- [`docs/testing.md:1-52`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/docs/testing.md#L1-L52)：A=真正独立编译运行时才可写，作者的 headless/clock 自测是 C。
- [`README.md:10-50`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/README.md#L10-L50) 与 [`README.md:106-135`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/README.md#L106-L135)：功能与“99场景”**作者自述（C01）**。
- [`LICENSE:1-21`](https://github.com/tytannial/rich4-re/blob/b7b76570f445ad07c0788314062b8500e77259e7/LICENSE#L1-L21)；[GPL 对照 `COPYING`](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/COPYING) 与 [汇编入口](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4.asm)。授权范围、历史继承关系另有 D03 未定事项。
- [ReactMono `src/core/game.ts:85-110`](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/game.ts#L85-L110)、[`src/core/cards.ts:1-47`](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/cards.ts#L1-L47)、[`src/core/maps.ts:13-36`](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/maps.ts#L13-L36)、[`src/core/stocks.ts:1-49`](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/stocks.ts#L1-L49)、[`src/core/bank.ts:1-47`](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/bank.ts#L1-L47)：本仓库差异判断（B15）。

## B. 测试方法审计（不冒称跑通）

1. 文件树直接计数得到 **99 个 L1 场景文件**；各脚本有 `# id` / `# covers` / `# timeout` 和可能的 `# quickstart`。`tools/run_tests.py` 根据它们执行 `--headless --seed ... --quickstart ... --script`；`--matrix` **并非只打印覆盖清单，它也会尝试运行场景及 ctest**。代码用退出码和 `TEST asserts=... failures=...` 判定成功，未见其独立捕捉画面语义。
2. 场景实际检查了几种**不同层级**：`30_buy_land`、`20_rent_route`、`246_save_load` 和 `50_god_free_rent` 有真实 `assert state`；`72_chain_rent` 断言 `xfer` trace；`112_stock_smoke` 核对面板点击与通用错误，`226_stock_trade` 验证日志序列但不测准确现金/持仓；`268_ai_stock_buy` / `270_ai_stock_sell` 只查 AI 日志加通用错误；`304_music_resume` 是演出 trace；`68_news_fate` 只有两个等待，没有显式断言，属于弱回归用例。
3. `tests/unit/test_rent.cpp` 是精确数学检查，不需要商业资产；`tests/unit/test_save.cpp`、`test_mkf.cpp` 在资产不存在时输出 `SKIP` 并正常返回。`.github/workflows/tests.yml` 只安排 Linux/Windows L0 单测；**99 L1 文件数 ≠ CI 通过数 ≠ 原版资产差分数**。
4. 上游 `src/core/rng.cpp` 的定序列、`src/core/clock.cpp` 的虚拟时间和 `src/application.cpp` 的 SDL dummy 驱动可用于未来复现；但需要本地游戏数据才能推进真实游戏进程。

## C. 可复核命令及本次执行结果

上游环境允许时（**这些是建议复现命令，并非本次成功日志**）：

~~~bash
git clone https://github.com/tytannial/rich4-re.git
cd rich4-re
git checkout --detach b7b76570f445ad07c0788314062b8500e77259e7
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build --target rich4_tests rich4
ctest --test-dir build -R unit --output-on-failure
python tools/run_tests.py --exe build/rich4 --game /path/to/legally-owned/game --filter rent --no-ctest
python tools/run_tests.py --exe build/rich4 --game /path/to/legally-owned/game --matrix
~~~

这次研究容器检测：Linux x86_64，`cmake 3.31.6`、`ninja 1.12.1`、`g++ 14.2`，`pkg-config --modversion sdl3` 与 `freetype2` 均缺失；`git ls-remote https://github.com/tytannial/rich4-re.git HEAD` 返回 `Could not resolve host: github.com`。Github 代码接口可读取源码，但无法直接克隆成可编译工作树；本地没有原版 `Data.mkf`、`Panel.mkf` 等版权资源。故 **L0/L1 本次均未执行（A=0）**；禁止用“作者标绿”补充为研究者实测。

本研究可在仓库内直接验证的部分：

~~~bash
python -m json.tool docs/research/repositories/tytannial--rich4-re/evidence.json > /dev/null
python -c "import json,pathlib; p=pathlib.Path('docs/research/repositories/tytannial--rich4-re'); j=json.loads((p/'evidence.json').read_text()); ids={e['id'] for e in j['evidence']}; assert len(ids)==len(j['evidence']); assert all(set(f['evidence_ids']) <= ids for f in j['features']); assert len(j['upstream_sha'])==40; assert all((p/f).exists() for f in ('README.md','source-index.md','evidence.json')); print('research contract PASS')"
git diff --check
~~~

**验证边界**：这些命令只验证研究交付的结构，不是游戏编译或真实玩家体验；后续开发者如果补做原版行为测试，应把本报告的源码观察转成**独立实现的** ReactMono 测试输入与不变量。

## D. 索引维护与差分风险

上游源码/日期变化必须升级 SHA 并重新核对行号、场景数量与作者自述；不同原版发行版对 `SAVE*.DAT` 字节结构可能不同。禁止提交商业版 MKF、EXE、AVI、字体或未经确认继承授权的代码。研究报告把 ABI/资产事实与产品借鉴分离：许可证声明不是原版素材许可证，复现现象不是画质验收。
