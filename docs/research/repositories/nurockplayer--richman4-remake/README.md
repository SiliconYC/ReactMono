# nurockplayer/richman4-remake — Godot 保真复刻与失败验收研究

> 独立研究对象：[nurockplayer/richman4-remake](https://github.com/nurockplayer/richman4-remake)，上游固定 main **961bdf47389a08e3143c0340490896b9f50edef9**；检查于 **2026-10-19T01:19:33Z（UTC）**。本报告只审计开源代码及公开证据，不更改 ReactMono 游戏代码，不声称独立运行 Godot/有权限的原版资产。证据映射见 [source-index.md](source-index.md) 与 [evidence.json](evidence.json)。

## 1. 研究身份与复现基线

- 产品定位：Godot 桌面端、高保真重做 **1998 年《大富翁4》**，起始平台为 Apple Silicon macOS；所标“90–95% 玩家感知保真”只是上游目标，**并非测得的完成率**（C05）。
- 固定 Commit：961bdf47389a08e3143c0340490896b9f50edef9；上游默认分支 main，仓库元数据 fork=false（不等于已证明原创或已查完所有代码血缘）。GitHub 记录仓库于 2026-09-08 创建、最新推送于 2026-10-16；与已发布历史包的 commit 不是一回事。
- 公开 Git 树下未发现 LICENSE/COPYING 文件，GitHub API 的 license 字段为 null：**代码当前没有可据以移植的明确公开许可**（B12）。原版商业资源通过单独的私有 Git LFS 仓库关联；授权从公开可读不能推定（B11）。
- Godot 项目入口为 project.godot → game/main.tscn；上游要求 Godot 4.7.2 stable、Python 标准库和 macOS 私人封包脚本（B10）。本研究容器没有 Godot；本地网络无法解析 github.com 以完整克隆，亦无 Mac、私有原版目录与授权的游戏包，**所有本次运行测试均为 NOT RUN，A 级实测数量为 0**。通过 GitHub 仓库 API 已实际读取固定 SHA 的项目/测试脚本及对应文件树；可复现命令列于源码索引。
- 注意上游 [Issue #99](https://github.com/nurockplayer/richman4-remake/issues/99) 是**上游原版呈现验收**，与本仓库 ReactMono Issue #99 的任务编号相同，但不是同一 Issue。

## 2. 产品目标、原作与资料片的边界

本项目的目标是**原作忠实重制**，并非只借棋盘规则创造新作。原始《大富翁4》基础版（Game）和《超时空之旅》（MultiverseJourney）在本研究中按不同资源来源追踪，不混用名称、地图来源或同一张截图。上游的公开解析程序为 Game 指定四组股表、资料片八组股表；文档声称地图分别为 **4 张与 8 张**，总计 12 张，不是十二张完全独立的基础游戏地图（B02、C03）。

上游报告称两版的前四张地图在数据形态上对应，后续资料片另有新图；例如第八张可只有商业设施而无住宅，第五张存在 20 个孤立的非住宅节点（C03）。这些都是作者基于私有地图所述结果；本次仅确认解析器具备相应结构和地图身份保护，**未重新计算私有地图字节**。在 ReactMono 不把资料片专属规则或原版受版权约束的资源误认为通用桌游设计。

## 3. 架构、数据流、测试与产物

实际公开代码形成五层（B01–B11）：

1. **输入/溯源**：tools/import_original.py 解析 MKF 索引、十字宽地图头、节点/土地/设施/企业/景观表、PE 的十二股源表，保存 edition、resource index、payload hash 与完整文件 hash；tools/verify_private_assets.py 验证私有仓库修订与 manifest，导出的资源不直接进入公开 Git。
2. **规范化与准入**：game/content/original_maps.gd 读取 catalog、拒绝重复身份及非法结构，按是否有完整源股票和设施数据授予功能能力标志。不完整或旧数据可以被识别，不应暗中升级成原版完整体验。
3. **独立规则状态**：game/core/game_state.gd 创建含 seed / rng_state / 当前回合 / route_options / 剩余步数 / market / bank 的确定性局面；各独立 core 模块处理股价、账本、事件、神明、卡道具等，choose_action 与 end_turn 成为动作入口。
4. **玩家表现与输入**：game/ui/main_ui.gd（本次读得约 4696 行）连接旧界面和 source-shaped GameShell；game/ui/board_view.gd 在平面世界坐标绘图、缩放、旋转、遮挡和 fallback；game/ui/stock_panel.gd 以局面快照渲染十二股面板，通过 trade_requested 回传动作而非自行改账。
5. **回归与打包**：tests/graph_flow.gd、tests/stock_presentation.gd、tests/scene_visuals.gd 是有效的**测试设计证据**，含分岔选路、合成 12 股、4×4 画布及来源哈希回退；tools/check.sh 调用大量 Godot headless 测试；tools/package_macos.sh 为私人桌面封包。没有独立运行/开发者口述以外的最终像素验收依据。

这不是一个浏览器或 React 仓库；其 macOS .app 和受限资源管线与 ReactMono 的纯静态 PWA 交付约束不同。可研究逻辑与检验思想，**不能移植其二进制资源、Godot 场景或直接复用存档**。

## 4. 功能完成度与证据矩阵

本表“部分”指可定位**代码路径**；“作者称”只对应上游自述；“未知”不能等同不存在。因为本研究未运行 Godot，表格没有独立 A 级整局、视觉 PASS。

| 范围 | 本次判定 | 原因/证据 | 仍需的实证 |
| --- | --- | --- | --- |
| 标题/角色/开局 2–4 人 | 部分 + 作者称可用 | GameShell/MainUI 接入，旧包流程报告 B06/C01 | 普通 Mac 实机从标题选择到合法回合 |
| 地图与路网 | 来源 4+8 为作者称；解析代码已核查 | B01/B03/C03；原始节点、邻接与标识的校验 | 对两版 12 张实际输入及对应源 checksum 再计算 |
| 掷骰/分岔/回合与 AI | 部分 + 历史包作者称过关 | B04/B09/C01；路网图局与自动回合 | 当前 SHA 的完整真人+AI 反复对局 |
| 住宅/商业、租金/破产 | 部分 | B03/B04/C01/C06，无法由测试存在认定与原作数值一致 | 同版源数值、具体税费、结算顺序的黄金轨迹 |
| 银行/ATM/贷款 | 部分；当前原版展示受阻 | B04/C04；完整 encounter 改动位于未合入草稿 | 经过银行的资金时序、原版银行画面与连续动作 |
| 股票与公司 | 十二股域模型有代码；旧档有三股路径 | B02/B05/B06/B08 | 普通已封包新局 + 旧存档两路径、同版图表实机核查 |
| 卡片/工具/商店 | 部分 | 上游多独立模块及 fidelity 记录 C06 | 逐项触发/取消/反制/供给与原作规则校对 |
| 神明/新闻/命运/设施/特殊事件 | 部分 | core 模块可见，作者明确承认部分 unknown C06 | 完整原始事件清单、原版触发与处理顺序 |
| 存档/读档/重开 | 部分 + 历史包作者称通过 | seed/rng_state、保存结构 B04/C01 | 当前候选跨进程真实保存恢复及版本化复现 |
| 画面、镜头、音效与输入节奏 | **未通过最终呈现 gate；本次不给数值分** | B07/B08/C02/C06/D01 | 同版本逐幕、可用控制、独立视觉对照 |
| 桌面包/无素材运行 | 历史私有包作者称通过；公开完整复现受限 | B10/B11/C01/C04 | 最终源、素材清单、二进制包与真机输入 |
| Web/PWA/纯静态 | **未知/非项目目标** | Godot/macOS 路线 B10 | 不应默认宣布兼容 ReactMono 部署 |

**地图量化上限**：有可证作者表格的 12 个源地图目录、4+8 分版、上游记录的各图节点/地产数量，不能推出“12 图玩家体验均已完成”或“原作玩法完成 X%”。**资源量化上限**：文档还报告 878 个压缩条目跨源代码 oracle 一致，但该结果仍是作者陈述，不是本研究独立测得的视觉/声音复刻率（C03/C06）。股票模型同时存在十二股与旧三股路径，不能把双路径混为“全部正常开局必然十二股”（B05/B06）。

## 5. 深挖的五个核心代码证据点

**① 地图输入不是画地图截图。** tools/import_original.py 的 parse_map_payload（L710–768）输出节点、土地、设施、企业、景观表及源 hashes；import_source（L904–1000）区分 Game/MultiverseJourney 和股票 EXE 表、校验后绑定 payload。original_maps.gd 的 normalize_map（L310–535）执行能力和图结构校验（B01/B03）。有可重复数据血缘链，缺私有原图时仍无法直接检验像素与剧情。

**② 原版十二股不等于用户看到十二股。** original_stock_market.gd COUNT=12、HISTORY_LIMIT=144，tick（L155–180）按保存 RNG 更新报价；源表解析器按版读取原始企业（B02/B05）。但 main_ui.gd 的 _on_source_stocks_requested（L479–494）对不具备 original_companies 的局面转回 stocks_popup，旧存档又明确有“继续使用旧版三股市”确认（L1146–1154，B06）。上游 [#100](https://github.com/nurockplayer/richman4-remake/issues/100) 直接描述装机版旧档显示 tech/transport/energy。这是一种**实际产品能力入口/保存版本/表现路径**不一致，而非“股票模型全没写”。

**③ 规则与 UI 是有界分层，但仍有维护压力。** game_state.gd 在图局初始化（L590–650）保存种子、随机数、phase、route_options、market、bank；UI 的 stock_panel.gd（L4–19）明确说明只发交易事件，不直接调用模拟或 RNG（B04/B08）。好处是可做状态不变测试；限制是 9590 行的核心和 4696 行的 MainUI 集成面很大，文档/测试/源码都没有保障每一种旧态/新态入口无回归。

**④ 造出原作形状的 GUI 不是原版视觉 PASS。** game_shell.gd 将工作坐标固定为 640×480、棋盘区域 440×440；board_view.gd（L15–25）自己标注 440 世界单位截取只是“推断”，原版投影未恢复；缺原贴图时 L560–615 使用路网线、文字/降级精灵呈现（B07）。stock_panel.gd 仍提供 fallback 背景（B08）。没有对比原版同一截图及交互轨迹，几何区域数字与绿测不构成保真度验收。

**⑤ 测试的边界写得比“全测绿”重要。** tests/stock_presentation.gd（L24–59）自己制造股票持仓和 144 天价序列；tests/scene_visuals.gd（L27–58）制造 4×4 绿色 PNG 并检查对应哈希；tests/graph_flow.gd（L87–170）检查合成路口、选择和确定性（B09）。这些代码足以支持静态认定其在**设计用于**检查合法路由、快照/UI 和来源验证，不能冒充已实际跑过、也不能推导真实原版画面已看过。

对应每一段的永久代码链接、类/函数位置、校验条件见 [source-index.md](source-index.md)。

## 6. 供 ReactMono 借鉴的五项具体策略

按“预期价值 / 落地成本 / 与现有 React+TypeScript+Three.js 兼容性”排序；这里只建议**新建原创实现与测试**，不拷贝原版资源或 Godot 源码。

| 优先级 | 吸收／排除事项 | 价值 / 成本 / 兼容性 | 复现与验收办法 |
| --- | --- | --- | --- |
| 1 | **分开三条验收线：逻辑可玩、真实玩家操作、最终美术审查**（C01/C02） | 极高 / 低 / 高 | 固定种子与同局 save → 核对完整对局 → 公网页面桌面/手机人工可操作 → 保留规定视角截图、独立商业审美评审；少一环即不宣称正式版 |
| 2 | **源数据和工程产物身份锁定**（B01/B03/B11） | 高 / 中 / 高 | 给地图数据、规则 fixture、UI 参考图/模型配版本/sha256；构建与回归日志指向同一 SHA，失配 fail closed |
| 3 | **存档版本与能力提示可见，不让旧态伪装新系统**（B06） | 高 / 中 / 高 | 在本地存档 schema 上做旧档、缺地图、能力不全、取消恢复测试；页面明确说明受限功能，不偷偷将旧档升版或清空 |
| 4 | **切分“域状态、玩家操作与来源化 UI”**（B04/B08） | 高 / 中 / 高 | 只让 React/Three.js dispatch 合法纯规则命令，所有显示从同一状态投影；验收取消/选股/开关面板不改变 RNG 和金钱 |
| 5 | **拒绝硬套 Godot 原版像素镜头/假完成度目标**（B07/C05） | 高 / 低 / 高 | ReactMono 采用自己的 low-poly 现代商品级视觉标准，建立固定相机/地块/建筑阴影、2–4 人 HUD、股市、手机操作的一组真实截图与审查；不要为“95%”编假数字 |

针对曾出现的形式主义风险：**有能玩的封包，不等于原版画面达到商品标准**。本例也提醒不要用头less 截图、源风格窗口、测试数/模块数去抵消最终的玩家观感。这些是审核方法，而不是把本项目变成 Godot 模仿品。

## 7. 缺口、风险与互相矛盾的证据

**已经确定的证据差别**：
- [docs/fidelity.md](https://github.com/nurockplayer/richman4-remake/blob/961bdf47389a08e3143c0340490896b9f50edef9/docs/fidelity.md#L5-L9) 与上游 [#89](https://github.com/nurockplayer/richman4-remake/issues/89) 声称历史 packaged 应用在人机/AI/结算、存读档通过（**C，历史候选**）。而作者于 2026-09-10 对主棋盘和股市提出**最终呈现 FAIL**，上游 [#1](https://github.com/nurockplayer/richman4-remake/issues/1)、[#99](https://github.com/nurockplayer/richman4-remake/issues/99)、[#101](https://github.com/nurockplayer/richman4-remake/issues/101)、[#102](https://github.com/nurockplayer/richman4-remake/issues/102) 均仍 OPEN（C02）。这是不同验收层，不是报告互相否定。
- 上游 [#52](https://github.com/nurockplayer/richman4-remake/issues/52) 称 main 等价旧候选有过“普通原生完整单局到结算”的额外观察，但银行恢复停留在 **draft PR212**、旧源视图还缺 Panel21/23/24，Mac 锁屏和当机磁盘门槛阻断后续银行/原版包测试（C04）。此处不把 PR212 的修复算作固定 main 事实，亦不将旧候选的 PASS 转嫁到新未合并提交。
- 上游数据称原版地图、压缩资源有大量已核对内容，然而 docs/fidelity.md 明示原版投影/动画/音效映射和同局 golden trace 尚未完成（C03/C06）。**解析正确 ≠ 游戏视听/规则整体忠实**。
- 原版 [#100](https://github.com/nurockplayer/richman4-remake/issues/100) 的“屏幕只有三股”与十二股源码并不相斥：旧保存局面的 capability 与 UI 分流在 B05/B06 中有具体路径。

**工程/法律差异**：许可证未声明（B12），不可直接 transplant 代码；私有原版素材（B11）不具备公开分发许可。代码文档引述 mytbk/rich4 的资源格式研究、多个以 Tachiko 命名的验证/迁移模块，尚不能从仓库元数据 fork=false 判断组件原创程度，必须追溯具体第三方 LICENSE/作者授权。

**环境和验收限制**：不能下载私有资产、无法进行 Godot/AArch64 Mac 实验，也没有同版原作和新版复刻的独立视觉成对捕捉；没有进行 PWA 性能或浏览器兼容测量；不能对整个系统标“缺失”或“商业级通过”。这些是明确阻塞，不应被截图 mock 或替代设计掩盖。

## 8. 五维 0–5 评分（证据等级与置信度）

评分仅是研究者对**公开证据成熟度与 ReactMono 价值**的有界判断，而非游戏绝对质量排名；无充分证据填写 null，不合成总分。

| 维度 | 分值 | 支持证据 / 置信度 |
| --- | ---: | --- |
| 原版规则覆盖 | **null** | B01/B04/C06；功能模块多但无同版原作流程的独立 golden trace，不给貌似精确的忠实分 |
| 代码可维护性 | **3/5** | B03/B04/B08/B09，B 级中置信；输入/规则/显示模块分离，惟核心状态及主 UI 单文件庞大 |
| 独立可复现性 | **2/5** | B10/B11、C01/C04，中置信；公开有命令及验证器，完整原版包依赖私有资产、特定机器，本轮未运行 |
| 画面与交互完成度 | **null** | B07/B08/C02/D01；存在源式表现代码，历史画面被退回，缺当前同态视觉比对及真实独立裁决 |
| 对 ReactMono 的实用价值 | **4/5** | B01/B03/B06/C02，中置信；数据契约、存档能力和独立验收方法很有价值，但不适合直接移植源代码/资源 |

## 9. 研究结论与后续

**结论：只读参考（read_only_reference）**。这不是“失败代码”：大量地图/股票/事件/账本解析、可重现规则设计与公开回归脚本是真实可追溯的工程工作。它的主要教训是**历史应用能结束对局，仍然可以因主棋盘/股市最终用户视觉不合格而无法算原版高保真完成**。对 ReactMono 应取走证据纪律、数据溯源与三分验收制度，拒绝把原版 UI 与版权资源当作捷径。

未解问题：① 私有地图/股票源 SHA 与功能表能否由合法独立机器复核；② 全部原版必需画面是否有同版本同状态配对、可操作跟踪与独立视觉 PASS；③ 上游旧存档进入三股的实际封包选择能否在最新候选复现；④ PR212 的银行可玩和原图 gate 是否最终通过并合并；⑤ 无明确 LICENSE 与外部格式/源码研究的组件来源如何获得可移植许可。这些均**不阻塞本次只读研究报告**，但阻止宣称上游最终保真达标。

本次交付只更新 docs/research/ 下研究文件；没有新视觉稿、假截图、导入原版图片、修改 ReactMono 游戏或更改 main。具体链接与命令见 [source-index.md](source-index.md)，逐项证据与可机读评分见 [evidence.json](evidence.json)。
