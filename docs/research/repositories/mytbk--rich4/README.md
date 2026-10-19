# mytbk/rich4：原版《大富翁4》可追溯逆向研究

> 对应 [ReactMono #95](https://github.com/SiliconYC/ReactMono/issues/95)。研究范围仅为上游 [mytbk/rich4](https://github.com/mytbk/rich4)，不移植源码、不提交商业素材、不改游戏。**本报告是指定版本源码的静态审计，不是一次独立游戏试玩。**证据 ID 与等级见 [evidence.json](evidence.json)，可复制的源码锚点与检查命令见 [source-index.md](source-index.md)。

## 一、研究身份与复现基线

| 项目 | 固定值或核查结论 |
| --- | --- |
| 上游仓库 | [mytbk/rich4](https://github.com/mytbk/rich4) |
| 默认分支与锁定提交 | **master / f81954d6a5675f63297036f9252720c6ca32a2b4**（提交作者时间 2026-10-08 02:06:42 UTC） |
| 核查时间 | 2026-10-19 01:17 UTC |
| 研究基线 ReactMono | dev **be88f92936e553bd369fe3c142394cd612659f5f** |
| 作者溯源 | Iru Cai / mytbk；部分 C 文件有 2018 年起的版权标注 |
| 根目录许可证 | [COPYING](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/COPYING) 为 GPLv3 正文；[C 文件 SPDX](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_info.h#L1) 明示 **GPL-3.0-or-later**；不是原作美术和游戏二进制的授权 |
| 上游原版目标 | 作者指称为《大富翁4》v3.11，rich4.exe 为 588 KiB，SHA-256 为 5a90aee28ee5f7a5c3ba5cb935c9e55751a529c25fcd91208748a66293569550，**未持原文件独立校验** [C01] |
| 本次执行环境 | 仓库和源码由 GitHub 连接器逐文件读取；隔离 Linux 命令行无法解析 github.com，且缺 i686 MinGW、NASM、Wine multilib 与原版游戏 MKF，未编译、未运行、未截图 [D01] |
| 原创/派生关系 | 本仓库自身是**原版二进制的逆向资料和部分功能等价重链接工程**，不是原厂开源；此报告结构化 relation 记为 tool，以免将其误评为独立完整复刻 |

证据按规范 A 独立实测、B 固定 SHA 源码核查、C 原作者/第三方声明、D 未验证推断区分。本次 **A=0**，所有“可以启动”“玩法完整”等结论都不得把 C 或 B 直接提升成 A。

### 逆向里程碑与证据强度

| 时间 | 可追溯事件 | 核验层级 |
| --- | --- | --- |
| 2018 | 作者称用约三个月发现游戏资源解压算法与存档格式；项目早期 C 代码留有 2018 版权说明，仓库历史含 2018-11 的图形反编译提交 | 时间线 C02，旧代码存在 B02/B12 |
| 2021-05 | 作者称使用 r2dumpbin 把原 exe 转为可修改、链接的汇编，边修改边测试；2021-05 的 issue #4 曾报告“股票界面不能卖股票”，反映重链接工程仍有回归风险 | C02、[issue #4](https://github.com/mytbk/rich4/issues/4) |
| 2025-05 至 07 | 作者称在 Codeberg 的 rich4_asm 加注释、分拆汇编，移除 Watcom 运行时后使用 MinGW/msvcrt 链接；现行构建文件确实显示这条工具链 | C02 + B01 |
| 2026-08 至 09 | 提交历史出现卡片/工具子程序由汇编改写为 C 的增量工作，如 ec7d70e、548a01f、54ff267；**“改写”不证明游戏功能全部已修复** | 提交元数据 + [卡片源码](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_card_table.c#L1) |
| 2026-10-08 | 最新锁定提交 f81954d6 主要变更相关项目链接，不代表代码完成度发生跳跃 | 提交元数据 |

原作者在 [readme.rst](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/readme.rst#L54) 特别说明，工程**不追求与原 exe 字节完全相同**，目标是功能等价的可读代码；应将“作者主张可构建运行”和“二进制等价验证”严格分开。[C01、C02、D01]

## 二、产品定位、版本边界与代码血缘

这是一份针对原版 Windows x86 程序的逆向与链接工程。**asm/** 分拆原版汇编及少量已翻译的 C；**csrc/** 留存历史 C 层逆向工作与独立的资源解包工具；**docs/** 记录地址、结构和格式，**tools/** 包含地图数据提取/绘图实验。它不提供现代 React UI，也不是发布一套原创低多边形游戏。可见代码中的画面行为依赖原版 DirectDraw/MKF，画质与交互绝不可按现代成品打分。[B01、B02、B17、D01]

版本必须分清：作者逆向的目标是 **v3.11**，其 [docs/map.txt](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/docs/map.txt#L1) 明确讲“超时空之旅 V3.11”下的 8 张地图以及 game_stage ×4 + game_map 的编号。不能因此反推“1998 年最初零售版就有 8 张相同地图”，也不能默认所有 Steam 版与资料片具有相同 exe、保存布局或素材索引。[B03、C01]

关于后来的重建工程，**存在不同强度的关系证据**：

- **实质可定位的派生关系**：lhr0909/richman4-remastered 的 [README 致谢](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/README.md) 明言以 mytbk 的逆向工作为基础；[src/direction.cpp](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/src/direction.cpp) 源码中有 “Derived from mytbk/rich4 asm/rich4_calculate_direction.asm; see migration 004” 的逐文件标记；[THIRD_PARTY_NOTICES.md](https://github.com/lhr0909/richman4-remastered/blob/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557/THIRD_PARTY_NOTICES.md) 列出精确上游提交 ec7d70e693059d1e781d9d1cc2ad7f36d360d39e 与 GPL-3.0-or-later。这支持至少特定模块的明确派生/致谢，并**不**表示本次独立验证了该移植项目的平台声明。[C03]
- **参考关系而非已证明的源码复制**：tytannial 在 [mytbk/rich4 #6](https://github.com/mytbk/rich4/issues/6) 表示通过 IDA/MCP 另做逆向，同时参考 mytbk 的注释和笔记；上游也在“相关工作”列出 tytannial/rich4-re。这仅支持知识/注释参考关系，不足以声称其工程就是 GitHub fork 或法律上的源码衍生。[C04]
- **Git fork 与知识血缘不同**：是否为 GitHub 网络中的 fork、是否独立重写、是否为 GPL 代码派生是不同判断。以上关系依源码注释与当事者声明，**没有对两套重建工程进行全量逐函数相似度审计**。不能由“引用过 GPL 资料”自动推出它们全体文件的许可结论。[C03、C04、D02]

## 三、代码架构、模块与数据流

**主要执行链**：旧 Win32 程序入口、事件与消息分派 → 游戏初始化/地图 MKF 装载 → 玩家行动与路径选择 → 节点落地分派 → 地产、股市、银行、道具/卡片、事件等子系统 → 存档写盘及绘制。模块边界见 [asm/Makefile](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/Makefile#L7)，其中一次链接列出游戏、银行、UI、地图、道具、音效等对象；它是**单程序链接，不是现代组件隔离或 Web 引擎**。[B01]

- **入口、交互与消息**：asm/rich4_main.asm、rich4_new_game.asm、rich4_ui_main.asm、rich4_ui_bank.asm、rich4_ui_stock.asm 等；旧界面逻辑同交易状态耦合，DirectDraw/DirectSound 和 Win32 依赖明显。[B01、B08]
- **回合、地图**：asm/rich4_player_core_actions.asm、rich4_player_utils.asm、rich4_load_map.asm，以及 [rich4_map.h](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_map.h#L95)。地图节点 40 字节，节点类型使用区间编码，邻接用多个槽，而不是一张二维格表或单一环形路线。[B03、B05、B15]
- **地产与经济**：玩家状态 [rich4_player_info.h](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_info.h#L8) 记录现金、存款、贷款、神明、行动状态等；[rent](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L229)、[stock](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_stocks.asm#L94)、[price index](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_update_price_index.asm#L11) 更新关联的全局表。[B04、B06、B07、B13]
- **卡牌/工具/神明/AI**：卡、工具静态参数表与业务例程分离，主程序通过跳转表处理可用对象；神明影响玩家与地图对象；AI 自身也访问卡牌、人物、地产和股市状态。[B09、B10、B11、B18]
- **资源**：MKF 第一个 32 位小端数字指向**文件末尾的索引表**；资源偏移指向 16 字节块头（解压后长度、压缩长度、图像偏移/长度）；部分资源有 SPR/SMP 子图布局（SPR 的第一帧相对 start_offset 再偏移 512 字节）。[B02]
- **存档**：Windows 时代 SAVE%d.DAT 原始二进制序列直接序列化内部游戏状态；读档重新装载地图、校正人物名称指针，不能将结构体物理布局直接等同可移植的 JSON 契约。[B12、B13]
- **测试/产物**：有 [csrc/mkf/test/runtest.sh](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/csrc/mkf/test/runtest.sh#L1)，依赖未提交的原版 Data.mkf、32 位 GCC 与哈希基准；在本次隔离环境没法跑。asm Makefile 可以“构建出 Windows exe”只是作者给出的指令路径，**未进行运行证明**。[B01、B14、C01、D01]

值得强调：**csrc/** 中 [player_action.c](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/csrc/player_action.c#L29) 仍有不合法 C 标识样式（如 fcn.0040829d）；不可将它与 **asm/** 中已配置的汇编/C 链接工程合并描述成“完整 C 游戏源码”。[B17]

## 四、功能、规则、视觉与交互验证矩阵

以下“部分”仅指**指定代码路径可读、未经独立功能运行**；不是完成百分比。上游原版资产不可发布或作为截图“伪造”提供。

| 领域 | 可核查证据与机制 | 研究状态 | ID |
| --- | --- | --- | --- |
| 新局、回合、掷骰、移动 | asm/rich4_new_game.asm、行动函数、路线节点/遥控骰子处理；骰点概率与行为未动态对照 | **部分** | B05、B13、B18 |
| 地图与分支 | MAP.MKF/MAPDAT.MKF、40 字节节点及多槽邻接；v3.11 8 图来自资料说明 | **部分** | B02、B03、B15 |
| 住宅/地产与租金 | owner、level、连锁标记，租金累加和物价指数，购建扣现金；无独立原版逐局对照 | **部分** | B04、B05、B07 |
| 银行、借贷 | 钱包/银行存款/贷款是不同字段；银行 UI 与禁入状态存在；完整计息未核验 | **部分** | B06、B08、B13 |
| 股市/商业 | 有股票买卖、持仓成本计算、银行与现金结算路径、上市公司所有权 | **部分** | B06、B07、B13 |
| 30 种卡/13 种道具 | 源码静态表、使用与 AI 参数函数；**不等于**全项已独立测试 | **部分** | B09、B11、B18 |
| 神明、命运与新闻 | 神明附身/去除、特殊状态有代码；全事件及动画时序不明 | **部分** | B10、B13 |
| 电脑玩家 | 卡/道具选择依据参数、状态、随机分支与跳表；强度与对人策略未知 | **部分** | B11 |
| 原版二进制存/读档 | 双向按字节写读多个状态块；缺合法样本往返测试 | **部分** | B12、B13 |
| UI、帧动画、音乐/语音 | Win32/DirectDraw/DirectSound UI 与音效模块源码存在；无真实截图/听觉、帧率、完成度验收 | **未知** | B01、B08、D01 |
| 原版重链接游戏的实际启动 | 作者说在游戏目录下可借 Wine 启动；研究者未执行 | **仅作者声称** | B01、C01、D01 |
| Web/PWA 与移动平台 | 此仓库目标为老式 Win32 exe，相关的跨平台重建是**其他**工程 | **未知/不适用** | B01、C01、D01 |

**规则矩阵提醒**：原版“有公式”≠ ReactMono 必须照抄原版数值。尤其涨价规则、神明、集团持股存在设计与版本差异，只有建立黑盒对照样例后才可决定哪项是缺漏、哪项属于现代化重设计。[B04、B06、B07、B19、B20]

## 五、核心源码深挖：六条调用链、五组重点发现

### 发现 1：掷骰后不是简单格子循环，而是图节点与落地分派

[rich4_player_info.h](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_info.h#L12) 将 node_id、last_node_id、direction 与 ndices 存入角色；地图 [rich4_map.h](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_map.h#L99) 包含 4 个 16 位位置槽和 type_and_idx；[rich4_player_move_one_step_done](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L2604) 读取当前节点及其覆盖对象状态，然后 [rich4_handle_player_land_on_node](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L322) 取 type_and_idx：2000–3999 范围进入住宅地块路径，再按地块所有权、等级及现金判定。遥控骰子 [rich4_use_tool_yaokongtouzi](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_tool_yaokongtouzi.asm#L20) 有独立动作路径。[B05、B13、B15、B18]

**关键限度**：这些证据证实“数据设计容许多连接、落地先分派再执行”，但未完整恢复每条分叉选择、原作掷骰随机算法或所有动画。ReactMono 目前 [advancePosition](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/maps.ts#L36-L41) 只能走 route 上的一个后继；未来如要增加十字路口需要独立图拓扑模型，不应直接注入原版内存结构。[B19]

### 发现 2：产权/连锁租金/物价指数是**耦合规则**，不能只照数值

[rich4_get_player_num_chain_store](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L199) 数所有者满足链店标记的地块；[rich4_calculate_land_toll](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L229) 分支按 owner、地块名称与等级读取计价数据，另一分支按标记地块数增加基数 0x7d0（2000），最终将累计金额乘以 price_index。落地分支在 [L369–435](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L369) 决定所有权与升级费用；[rich4_check_pay_toll_to_owner](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L5310) 还检查同盟/拘留/神明等状态是否改变收租情形。独立 [update_price_index](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_update_price_index.asm#L11) 在玩家存活状态中汇总财富，平均财富÷初始资金并**仅在更大时**更新指数（L45–47 的 jle）。[B04、B05、B07]

**限制**：固定 2000 的分支不能直接宣传“所有连锁店每座恒收2000”——尚有名称、地块等级、临时状态、减免入口需要动态样本核对。ReactMono 当前 [property.ts](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/property.ts#L88-L116) 实现到访购/升级，[turns.ts](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/turns.ts#L44-L75) 用 tile 的等级租金结算；未按原版的同名街区/物价指数公式运行，不构成错账结论而是**模型不一致**。

### 发现 3：股票与银行并非一个独立的前端小工具

[r​​ich4_stocks.asm 的 buy/sell](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_stocks.asm#L94) 在不同分支对 [player_info](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_info.h#L34) 的现金字段偏移 +28 与银行存款偏移 +32 扣/加资金；股票表保存股数与持仓均价，买卖后调用 [rich4_update_commercial_owner](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_stocks.asm#L743) 更新企业控制状态。银行 [UI 入口](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_ui_bank.asm#L3490) 检查 days_rejected_by_bank 等标志并计算财富。静态股市表 [all_stocks](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_all_stocks.c#L1) 96 项对应 v3.11 的 8 图×12 股票表，运行期只有相关地图的一组股票。[B06、B08、B13、B20]

ReactMono [stocks.ts](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/stocks.ts#L6-L50) 则设计 5 个原创报价、0.5% 手续费、现金/存款可选结算；[bank.ts](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/bank.ts#L5-L47) 每完整回合结息。不能擅自认为“原作与 ReactMono 没有差别”，也不能把原版真实公司名移入新项目。合理做法是独立设计资产守恒、溢出、公司控制变更的测试，而非翻译这套 GPL 汇编。[B20、D02]

### 发现 4：卡/工具与神明通过静态元数据、AI 选择与状态寄存层相连

[rich4_card_table.c](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_card_table.c#L3) 有 30 项卡牌元数据，工具 [tool_table.c](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_tool_table.c#L3) 有 13 项；AI 卡片入口 [fcn_0041e69e](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_ai_use_card.asm#L42) 使用当前角色属性与伪随机判断后走 [jump table](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_ai_use_card.asm#L71)；[ai_use_tool](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_ai_use_tool.asm#L36) 同样检查类别并走策略表。神明 [rich4_attach_god](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_gods.asm#L472) 首先处理现存附身，随后改变玩家 god_info、地图对象和多项状态值。可见规则参数、使用判断与特效执行不是同一个平面。[B09、B10、B11]

ReactMono [cards.ts](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/cards.ts#L5-L50) 当前只有 5 种，能合法拒绝错误指令，已有清楚的可独立模拟入口。要扩充“神明影响×卡牌免租×AI 时机”，应先写效果状态机的**行为契约与不变量**，且坚持用原创卡牌名称、数值和表达，不直接搬入30卡表字节或神明原造型。[B21、D02]

### 发现 5：存档是内部结构串行化，不是可安全搬进 Web 的规范

[rich4_save_game_to_file](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_save_files.asm#L529) 文件起始 4 字节写 0x26，紧接日期、地图与玩家数，4 名玩家状态每人 0x68；随后对象、卡牌 0x3c 字节、道具 0x3c 字节等；[load_game_from_file](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_save_files.asm#L99) 反向读取并将角色名指针修正为运行时结构地址；[docs/saveload.txt](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/docs/saveload.txt#L1) 提供部分偏移（例如 0x654 卡片区域）。[B12、B13]

这种格式包括固定偏移和指针关联，只有老游戏数据及特定 ABI 下才可能正常工作。ReactMono [save.ts](https://github.com/SiliconYC/ReactMono/blob/be88f92936e553bd369fe3c142394cd612659f5f/src/core/save.ts#L7-L40) 是带版本/校验的本地 JSON 存档。**不建议直接兼容原作 SAVE%d.DAT**；若未来用户确实需要导入，可在版权合法、可检查样本条件下独立编写严格边界校验器，永不把历史指针解释成浏览器地址。[B12、B17、D02]

## 六、ReactMono 可借鉴之处（含不采用建议）

以下仅给**研究后的候选假设**，不是授权修改玩法、已有路线图或美术；所有实现应由未来独立 Issue 决定。

| 优先级 | 候选规则数据/测试方法 | 玩家价值、代价和兼容性 | 不应复制的边界 |
| --- | --- | --- | --- |
| 1 | **租金规则矩阵**：同主/异主、街区同名、连锁、神明/同盟、禁收租、物价指数边界，构造合成数据表跑确定性测试 | 高价值/低至中成本；复用现有 turns/property 纯规则接口，先证明模型差别 [B04、B07] | 不复制原租金实现及所有 1998 金额常数，不将原商用地区资产强塞到产品 |
| 2 | **地图图拓扑协议**：route 保持兼容，另研究节点多出边和转向状态的可选游戏地图 schema 与无界面路线测试 | 高价值/中至高成本；需要存档迁移与 AI 行为测试；目前环形 route 仍有效 [B03、B15、B19] | 不导入 MAP.MKF 商业地图或照抄内存字节布局 |
| 3 | **财务一致性测试**：现金/存款/股票成本与卖出、净资产/物价指数、企业控股临界点，分别测溢出与失败原子性 | 高价值/中成本；沿用已有 stocks/bank/save API，仅增加合成场景 [B06、B07、B20] | 不直接复制股票、真实企业名称与任意费率；不自动修改现有金融产品决策 |
| 4 | **卡/神明/AI 组合测试**：建立道具使用时机、合法目标、状态持续与卸载、AI 事件表；先小集合交叉测试 | 中高价值/中成本；复用 useCard、chooseStyledAction 入口 [B09、B10、B11、B21] | 不搬30卡全文、BIG5 文本、角色语音、美术，也不照搬汇编随机数实现 |
| 5 | **存档字段“可恢复/不可恢复”审计法**：建立字段归属清单、版本往返与不信任输入测试 | 中价值/低成本；提升当前 JSON save 验收质量 [B12、B13] | **否定直接二进制 SAVE 互通优先级**：缺合法样本、版差与结构不安全；不把原版存档发布 |

独立验证建议以**新建原创场景、固定随机种子、规则引擎生成事件日志**为基线，再人工拿**合法持有原版且明确版本相同**的机器做黑盒对照；可做对照表，但不复制任一边受保护的程序/资源。应先验证现有 ReactMono 的功能确有偏差，不以“比原版少 25 种卡”为自动 Bug。[B19、B20、B21]

## 七、局限、矛盾、许可证与交付风险

1. **可重编译不等于在本环境可运行**：目标仍为 32 位 PE/Win32/DirectDraw/DirectSound；[Makefile](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/Makefile#L1) 依赖 MinGW + NASM，且编译出的 exe 按作者说法需放回游戏目录由 Wine 启动。没有合法原版数据就不能保证显示、声音或完整对局；本次不生成截图、不标 A。[B01、C01、D01]
2. **作者声明与代码证据层级不同**：2018、2021、2025 年的阶段陈述和 2026 年其他人的“移植可玩”均属于有背景支撑的声明，**非本次独立复现**。尤其上游并未承诺字节级 exe 等价。[C01、C02、C03]
3. **源代码分层不齐**：asm/Makefile 是活跃目标，csrc 的 C 部分只是历史与工具材料；其中无效标识与 TODO 不能用于支撑“整个游戏已经 C 语言重写”。反编译符号、地址、压缩数据与作者注释可能尚有误解。[B01、B17]
4. **GPL 与著作权必须分开**：仓库 COPYING 是 GPLv3 条款，部分 C 源码 SPDX 指向 GPL-3.0-or-later。**它授权的是权利人有权授权的代码，并不自动授权原版游戏源码、地图、头像、声音、文字和数据资产**。对基于商业二进制形成的完整反汇编究竟享有哪些可再许可权利，不能由单张 LICENSE 得出法律结论。ReactMono 希望保留独立 React/Three.js 原创路线，故**不复制、改写/翻译或合并该项目代码；只用抽象的游戏机制事实设计原创规则和独立测试**。任何商业公开复用应另请专业法律评估。[B16、D02]
5. **血缘与许可不能一刀切**：lhr0909 有逐文件派生与 GPL 告知；tytannial 的明示是参考逆向注释，不足以证明直接代码继承；其他项目应由 #96/#97 单独审查，禁止在 #95 代为宣告结案。[C03、C04]
6. **画面价值有限**：这种二进制逆向不会直接产出《天天过马路》式低多边形人物、建筑与统一镜头光照。ReactMono 的视觉路线不应回退到原版资源、旧图层或 640×480 交互。[B01、D01]
7. **旧原版存档和旧官方发行版差**：未知是否能跨原始 1998 版、超时空之旅 v3.11 与当前其他商店分发版复现。尚未在原版生成合法测试集，未知租金/神明/银行特殊边界在不同版本的数值。[B03、B12、D01]

## 八、五维评分（0–5，仅对这个逆向资料工程）

| 维度 | 评分 | 等级/可信度与理由 |
| --- | ---: | --- |
| 原版规则覆盖 rules | **3/5** | **B，中等**：可查到移动、租金、物价指数、股票、AI、存档多个路径，但算法细节/运行等价未交叉实测 [B04–B13] |
| 可维护性 maintainability | **2/5** | **B，中等**：虽有命名的子模块、静态表和 Makefile，仍以巨量汇编、硬编码地址、旧 Windows ABI 为主，csrc 存未完成痕迹 [B01、B09、B17] |
| 独立可复现性 reproducibility | **null** | **未评分**：缺可运行工具链及合法原版资源，本人未完成构建和启动。不能给 0/5 假装已测试并失败，也不能照作者声称打高分 [B14、C01、D01] |
| 画面与交互 presentation | **null** | **未评分**：没有合法运行截图、录屏、真人对局或操作手感数据。二进制资源处理路径不能直接说明商品级美术 [B01、D01] |
| 对 ReactMono 的实用价值 reactmono_value | **4/5** | **B，中高**：可为拓扑、租金、金融守恒、状态机、存档字段审计提供高密度可追溯规则样例；前提是**不移植上游代码和资产** [B04、B06、B07、B12、B19–B21] |

**无总分、无完成度百分比、无“所有玩法已完成”断言。**此评分仅衡量源码作为研究参考的价值，不能代表原版或下游现代移植游戏的实际商品质量。

## 九、结论、建议与未解问题

**结论：只读、价值较高的原版行为参考，非代码复用候选（read_only_reference）。**固定 SHA 下存在清晰的原版 x86 符号、落地/租金、企业/银行、AI、神明、存档/资源读取链条，值得给 ReactMono 设计**全新合成数据、可验证测试矩阵**；但本次没有原版 exe、原版数据、Wine 32 位环境的独立运行证据，因此不能将重编译、真机运行、完整可玩、原版忠实度标记为“已证实”。[B01–B21、C01、D01]

剩余疑问与后续研究方向：

- 原版 v3.11、1998 零售版和当前发行版能否按哈希/地图/存档字节做合法且不分发素材的版本对照？
- Wine multilib 与 DirectDraw/DirectSound 下可否重编译并真实打开一局？若失败应留下工具链版本、报错及可复现路径。
- 连锁地产、免租/神明/同盟、物价指数之间的计价边界能否用最小黑盒场景验证，避免误读分支？
- 股票公司控制权变化、银行与现金账户的收费/转账、月末事件能否提供基于合法原版机器的数值轨迹？
- SAVE%d.DAT 的剩余偏移、指针重建及跨版本兼容性有哪些风险？有没有合规提供的最小合成样本？
- 后续 #96、#97 的另两套现代重建工程是否有实测的原版对照与许可证血缘证据？不可仅相信各自 README。

**下一步顺序**：先由 #96/#97 核查现代重建与跨版本规则差异；#104 再做跨仓库交叉核验并建立统一差异矩阵。若真的立项改 ReactMono，分别独立创建“原创拓扑模型/规则金样例/状态机测试” Issue，保留现有游戏主体、独立技术栈和商业级 3D 视觉方向。