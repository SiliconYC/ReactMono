# iam567/rich4-renew-app 源码证据索引（Issue #98）

- 上游：https://github.com/iam567/rich4-renew-app
- 固定源码：`1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79`（`main`，2026-10-18 17:34:57 UTC）
- 查阅：2026-10-19 01:19–01:25 UTC；**逐文件读取指定 SHA，仅 B 级静态核查，未执行这些文件**。
- 源码链接统一绑定固定 SHA，不引用可能漂移的 `main`。定位范围只说明实现位置，不证明原版一致性。

## 核心调用链及可追溯锚点

| 编号 | 定位（固定 SHA） | 实际代码事实 | 证据等级 |
| --- | --- | --- | --- |
| S01 | [`game/src/core/game.ts#L248-L333`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L248-L333) `Game.constructor` | 建立玩家、地图副本、Rng、Stocks/Cards/Tools/Objects/Events/Places/BlackMarket/Forks；初始化有具体调用，黑市是明确标记的二创 | B |
| S02 | [`game/src/core/game.ts#L617-L653`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L617-L653) `run/loop/endTurn`、[`game/src/core/game.ts#L804-L877`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L804-L877) `playerTurn` | `Flow` generator 产出提问/事件，AI 先处理股票、黑市、卡道具，再掷骰；界面只消费流。此处不是 React 状态驱动 | B |
| S03 | [`game/src/core/game.ts#L1005-L1051`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L1005-L1051) `landOnLot/calcToll`、[`game/src/core/game.ts#L1320-L1470`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/game.ts#L1320-L1470) `atm/bankCounter/financeReserve/financeRecall` | 购买、升级、街区合计租金、ATM、贷款、银行控制者特别融资及资金准备金处理属于实际算法分支 | B |
| S04 | [`game/src/core/modules/stocks.ts#L137-L403`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/stocks.ts#L137-L403) `Stocks` | 交易日、价格趋势、停牌、流通股、买入、卖出、股份转移和企业控制有状态与具体方法 | B |
| S05 | [`game/src/core/modules/cards.ts#L37-L120`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/cards.ts#L37-L120) `CARDS/TYCOON_CARDS/KB_CARDS/REMAKE_SUPPLY`、[`#L148-L231`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/cards.ts#L148-L231) `Cards` | 30 张基础牌、6 张大富豪专属牌、2 张歌舞伎町牌分别登记；重制卡池与原卡池配置分离，领牌/消费/抽取有实现 | B |
| S06 | [`game/src/core/modules/tools.ts#L34-L79`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/tools.ts#L34-L79) `TOOLS/TYCOON_TOOLS`、[`game/src/core/modules/objects.ts#L32-L104`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/objects.ts#L32-L104) `OBJ/Objects` | 原作 13 种工具、跨城市三种实验室工具，46 个对象槽、神明幸运值及路障/地雷等模型；并非只列道具名字 | B |
| S07 | [`game/src/core/modules/events.ts#L32-L161`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/events.ts#L32-L161) `Events`、[`game/src/core/modules/places.ts#L31-L56`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/places.ts#L31-L56) `Places` | 新闻/命运、神明和地点事件、NPC/拍卖/乐透等有配置与执行类；对原版逆向细节的声称需独立对照 | B |
| S08 | [`game/src/core/board.ts#L1-L116`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/board.ts#L1-L116) `Board/Bytes/parseBoard`、[`#L117-L155`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/board.ts#L117-L155) | 按字节偏移读取 Big5 原始记录并转成带相邻节点、地产和公司信息的图；尺寸默认 2304，可由地图提供其它尺寸 | B |
| S09 | [`game/src/core/world.ts#L32-L70`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/world.ts#L32-L70) `TYCOON_MAPS`、[`#L277-L340`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/world.ts#L277-L340) `World/sharePool`、[`#L1085-L1162`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/world.ts#L1085-L1162) `run/arrive` | 五城各持 Game 状态、共享 12 玩家与全国卡池、城市间旅行、一轮多城市结算；不是原版单棋盘模式 | B |
| S10 | [`game/src/core/finale.ts#L28-L77`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/finale.ts#L28-L77) `Finale`、[`game/src/core/kabukicho.ts#L37-L80`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/kabukicho.ts#L37-L80) `KabukichoRules` | 大富翁城决战与歌舞伎町独立事件规则有代码入口；两者均属于重制新增而非 1998 年原作证据 | B |
| S11 | [`game/src/core/save.ts#L14-L106`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/save.ts#L14-L106) `saveGame/loadGame`、[`#L108-L235`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/save.ts#L108-L235) `saveWorld/loadWorld` | JSON 数据克隆模块状态并保留随机状态；大富豪另存五城/跨城状态，加载时兼容旧卡池和名称。版本字段仅常量 1，不等于跨发布完全兼容 | B |
| S12 | [`game/src/ui/main.ts#L450-L530`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/ui/main.ts#L450-L530) `begin`、[`#L913-L1068`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/ui/main.ts#L913-L1068) 事件消费 | 图片/地图预载后建 BoardView/Hud，异步处理掷骰、购地、收钱、动画；与核心规则是事件边界而非 React 组件边界 | B |
| S13 | [`game/src/ui/board-view.ts#L72-L151`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/ui/board-view.ts#L72-L151) `BoardView`、[`game/src/ui/orientation.ts#L7-L27`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/ui/orientation.ts#L7-L27) | 棋盘是 Canvas 2D（非 Three.js、非 React），手机横竖屏调用 Capacitor 屏幕方向插件；仅说明设计存在，不能由此验收触控手感 | B |
| S14 | [`game/src/ui/assets.ts#L4-L107`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/ui/assets.ts#L4-L107) `mapList/loadMap`、[`game/scripts/link-assets.mjs#L1-L29`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/scripts/link-assets.mjs#L1-L29) | 运行从 `assets/maps/maps.json` 和 `assets/maps/remake/index.json` 读取地图；缺失文件会报错；link-assets 仅为本地素材路径创建符号链接，仓库无完整资源 | B |
| S15 | [`game/src/ui/saves.ts#L1-L50`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/ui/saves.ts#L1-L50) | 使用 IndexedDB 共 7 个槽：普通 AUTO=0，大富豪 AUTO=6；与原生 Capacitor 沙盒共用网页存储接口 | B |
| S16 | [`game/package.json#L1-L36`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/package.json#L1-L36)、[`game/vite.config.ts#L1-L8`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/vite.config.ts#L1-L8)、[`game/scripts/package.mjs#L1-L63`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/scripts/package.mjs#L1-L63) | Vite 7 + TypeScript 5.9 + Vitest 3.2 + Capacitor 7；`base: './'`，网页构建、Android debug APK 与未签名 iOS IPA 分别走工具脚本；不是 PWA 实现 | B |
| S17 | [`game/src/core/bank.test.ts#L53-L211`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/bank.test.ts#L53-L211)、[`game/src/core/modules/stocks.test.ts#L46-L114`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/modules/stocks.test.ts#L46-L114) | 银行测试写有融资/准备金/破产预期；股票测试写有精确浮点/跳动价位预期；**股票图面场景采用 `describe.skipIf(!haveMaps)`**，资源缺失则跳过 | B（断言存在≠通过） |
| S18 | [`game/src/core/world.test.ts#L63-L128`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/world.test.ts#L63-L128)、[`game/src/core/save.test.ts#L24-L47`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/save.test.ts#L24-L47)、[`game/src/core/kyushu.test.ts#L202-L229`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/game/src/core/kyushu.test.ts#L202-L229) | 有跨城种子一致/旅行、普通存读档逐状态相等、九州 200 天四电脑回归的测试定义；资源和运行状态仍未复核 | B |
| S19 | [`README.md`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/README.md)、[`THIRD_PARTY.md`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/THIRD_PARTY.md)、[`LICENSE`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/LICENSE) | 作者声明 GPL-3.0-or-later、依赖 mytbk/rich4 和原版游戏商业素材；`THIRD_PARTY.md` 声称原样 Git 子模块，但该 SHA 树无 `.gitmodules` / `upstream/rich4`，当前不可按该说明复核子模块指针 | C+B |
| S20 | [`CHANGELOG.md`](https://github.com/iam567/rich4-renew-app/blob/1a85b631700e5bbc9da64d5d995c9f0f9d9b4f79/CHANGELOG.md)、[`Releases`](https://github.com/iam567/rich4-renew-app/releases)、[`assets` Release](https://github.com/iam567/rich4-renew-app/releases/tag/assets) | 源码和日志为 0.2.2，查验时最新公开安装包是 0.2.1（APK 1,643,367,575 B；未签名 IPA 1,628,419,621 B），独立素材包 `rich4-assets.tar` 1,696,005,120 B；存在版本/素材分发差距，未下载安装验证 | B（配置）/C（发行元数据） |

## 已核查的执行边界

建议上游复现命令（**未运行**）：

```sh
cd game
npm ci
npm test
npm run build
# 完整游戏须事先以获许可的本地资源或作者单独提供的素材构建 game/public/assets
npm run dev
# macOS+iOS 工具链才可 npm run package -- ipa；Android SDK/JDK 才可 npm run package -- apk
```

当前执行环境无 GitHub 网络克隆/依赖拉取能力，亦未获取约 1.7 GB 的独立素材包；未启动 Vite、Vitest、Chromium、Android 或 iOS；**A 级证据计数为零、无本项目独立截图**。测试文件中的 `describe.skipIf(!haveMaps)` 使「npm test 退出 0」不自动意味着地图功能全部受测。

### 研究产物自检（与上游运行测试不同）
- 所有 S01–S20 对应固定 SHA 下实际读取/目录树确认的源码路径；以上 URL 为确定性源码链接。
- 索引、报告与 JSON 采用一致的证据等级；执行缺口不能写成通过。
