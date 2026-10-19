# mytbk/rich4 源码索引与复核脚本

研究对象固定为 [mytbk/rich4](https://github.com/mytbk/rich4) 的 **master@f81954d6a5675f63297036f9252720c6ca32a2b4**（2026-10-08 02:06:42 UTC；核查于 2026-10-19 01:17 UTC）。所有行号以该提交为准；后续主分支行号变动须重新锁定 SHA。根目录许可路径为 [COPYING](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/COPYING)，部分源文件标 GPL-3.0-or-later。研究分类与完整结论见 [README.md](README.md)，程序证据引用 [evidence.json](evidence.json)。

## 1. 精确源码锚点表

| ID | 研究模块 | 固定 SHA 源码与行号 | 具体函数/变量/用途 | 证据 |
| --- | --- | --- | --- | --- |
| R01 | 构建链 | [asm/Makefile:1-80](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/Makefile#L1) | rich4_mscrt.exe、i686-w64-mingw32-gcc、NASM、Windows 系统库 | B01 |
| R02 | 主流程与地图入口 | [asm/rich4_load_map.asm:71-165](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_load_map.asm#L71) | _rich4_load_map：读取 MAP.MKF，MAPDAT.MKF 可选优先 | B03 |
| R03 | 地图节点类型 | [asm/rich4_map.h:95-127](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_map.h#L95) | rich4_map_node：40 字节节点、4 槽出边、type_and_idx | B15 |
| R04 | 地图源数据/结构 | [docs/map.txt:1-34](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/docs/map.txt#L1) | 8 张 v3.11 地图、索引、各类型节点/表 | B03 |
| R05 | 掷骰与单步完成 | [asm/rich4_player_core_actions.asm:2604-2680](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L2604) | _rich4_player_move_one_step_done：状态、节点类型、地图对象 | B05 |
| R06 | 骰子工具 | [asm/rich4_tool_yaokongtouzi.asm:1-83](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_tool_yaokongtouzi.asm#L1) | _rich4_use_tool_yaokongtouzi：玩家/AI 参数入口 | B18 |
| R07 | 地产落地操作 | [asm/rich4_player_core_actions.asm:322-435](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L322) | _rich4_handle_player_land_on_node：按节点范围分派、owner/level/cash | B05 |
| R08 | 连锁地块计数与租金 | [asm/rich4_player_core_actions.asm:199-298](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L199) | _rich4_get_player_num_chain_store、_rich4_calculate_land_toll | B04 |
| R09 | 停留租金条件 | [asm/rich4_player_core_actions.asm:5310-5425](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_core_actions.asm#L5310) | _rich4_check_pay_toll_to_owner：同盟/拘留与其他例外分支 | B04 |
| R10 | 物价指数 | [asm/rich4_update_price_index.asm:11-53](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_update_price_index.asm#L11) | _rich4_update_price_index：活人净资产均值/初始资金、仅上涨 | B07 |
| R11 | 银行 UI | [asm/rich4_ui_bank.asm:3490-3563](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_ui_bank.asm#L3490) | _rich4_ui_bank_entry：禁入状态、净资产、面板加载 | B08 |
| R12 | 股票交易 | [asm/rich4_stocks.asm:94-224](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_stocks.asm#L94) | _rich4_buy_stock、_rich4_sell_stock：现金/存款、持仓成本 | B06 |
| R13 | 上市公司控制权 | [asm/rich4_stocks.asm:743-820](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_stocks.asm#L743) | _rich4_update_commercial_owner：买卖后被调用；具体全分支另核 | B06 |
| R14 | 原版地图股票表 | [asm/rich4_all_stocks.c:1-96](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_all_stocks.c#L1) | game_stocks[96]，多个地图各12支初始配置；Big5字节名称 | B20 |
| R15 | 玩家经济与动作状态 | [asm/rich4_player_info.h:8-80](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_info.h#L8) | player_info：cash/存款/贷款、node、神明、特殊状态等 | B13 |
| R16 | 卡片静态表 | [asm/rich4_card_table.c:1-34](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_card_table.c#L1) | card_table[]：30 个项目；注意字段释义未全验证 | B09 |
| R17 | 道具静态表 | [asm/rich4_tool_table.c:1-17](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_tool_table.c#L1) | tool_table[]：13 个项目；遥控骰子等 | B09 |
| R18 | 神明附身 | [asm/rich4_gods.asm:472-553](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_gods.asm#L472) | _rich4_attach_god：旧神解除、新神与对象状态、回调表 | B10 |
| R19 | AI 卡牌调用 | [asm/rich4_ai_use_card.asm:42-79](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_ai_use_card.asm#L42) | fcn_0041e69e：类别筛选、随机分支、回调表 | B11 |
| R20 | AI 道具调用 | [asm/rich4_ai_use_tool.asm:36-73](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_ai_use_tool.asm#L36) | fcn_00420e9a：权重/随机条件后动态分派 | B11 |
| R21 | 存档读取 | [asm/rich4_save_files.asm:99-187](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_save_files.asm#L99) | _rich4_load_game_from_file：状态恢复、角色名称重新指向 | B12 |
| R22 | 存档写入 | [asm/rich4_save_files.asm:529-620](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_save_files.asm#L529) | _rich4_save_game_to_file：玩家数组、道具等二进制字段 | B12 |
| R23 | 存档说明 | [docs/saveload.txt:1-12](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/docs/saveload.txt#L1) | 卡和道具记录的偏移；须与汇编读写再核验 | B12 |
| R24 | 资源档索引 | [csrc/mkf/mkf-format.md:4-72](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/csrc/mkf/mkf-format.md#L4) | MKF 索引表、16字节资源头、SPR/SMP 分片 | B02 |
| R25 | 读取资源与解包 | [csrc/mkf/mkf.c:32-59,73-92,132-173](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/csrc/mkf/mkf.c#L32) | load_mkf、read_mkf、update_spr_smp_ptr；附带旧代码风险 | B02 |
| R26 | 历史 C 代码局限 | [csrc/player_action.c:25-56](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/csrc/player_action.c#L25) | 反编译半成品含 fcn.004... 这样的无效 C 符号 | B17 |
| R27 | MKF 测试脚本 | [csrc/mkf/test/runtest.sh:1-21](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/csrc/mkf/test/runtest.sh#L1) | 32 位 GCC、Data.mkf 校验与 dump 输出散列 | B14 |
| R28 | 作者概述、里程碑 | [readme.rst:1-61](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/readme.rst#L1) | v3.11/二进制 SHA、Wine 条件、工程与链接、其他项目 | C01/C02 |
| R29 | GPL 原文 | [COPYING:1-35](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/COPYING#L1) | GPLv3 正文，无法覆盖原版权素材之再许可 | B16 |
| R30 | C SPDX声明 | [asm/rich4_player_info.h:1-4](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/asm/rich4_player_info.h#L1) | Iru Cai 与 GPL-3.0-or-later | B16 |

**解释原则**：这里的“证据”均为读取源码后的 **B**（或源作者声明 **C**）；即使文件名包含 test 也不等于测试已执行。多个函数的调用关系是静态解析入口/出口，并非完整执行轨迹；标签为反汇编恢复的名字和地址，可能尚有歧义。

## 2. 六条关键调用链核对

### 2.1 掷骰/移动/落地

- 参数和地图：R03 的 **rich4_map_node**（节点编号、邻接字段、地块类别）与 R15 的 **player_info**（node_id/last_node_id/direction/ndices）说明使用图节点作为移动语义核心。
- 单步返回：R05 的 **_rich4_player_move_one_step_done** 读当前 player.node_id 并根据节点和对象字段处理结束步骤。
- 落地交互：R07 的 **_rich4_handle_player_land_on_node** 读取地块 type_and_idx、所有者、等级和当前玩家现金，以分派购买、升级、收费等分支。
- 特殊掷骰：R06 **_rich4_use_tool_yaokongtouzi** 进入人工或 AI 参数支路，后续调用“使用道具后”函数。
- **尚未确定**：正常骰子生成的准确概率、逐帧动画与所有路线分叉条件不能从以上有限锚点直接断言。独立黑盒测试必须补充对合法原版机器的 trace。[B05/B13/B15/B18]

### 2.2 地产与租金

- R07：落地按土地编号范围定位每格，读取 owner、level，判断本人升级还是对手收费。
- R08：**_rich4_get_player_num_chain_store** 先遍历链店状态；**_rich4_calculate_land_toll** 按拥有者、街区名、等级等累计金额，最后乘 **rich4_price_index**。当连锁分支出现 0x7d0，须区分它是中间基数，不是任意条件下的最终定价。
- R09：**_rich4_check_pay_toll_to_owner** 涉及同盟、住院、监禁、休眠、神明/暂免状态，部分条件能改变常规收租解释。
- R10：**_rich4_update_price_index** 从存活玩家平均净资产与初始资金计算候选指数，L45–47 的条件分支只在候选值大于现值时采用。对除零、被排除角色和取整边界尚未真实执行。[B04/B05/B07]

### 2.3 银行/股市

- R15：**player_info** 现金位于 +28，银行存款 +32，另有 loan 和 special_finance，不能把资产当一个整数字段。
- R11：银行窗口读取禁贷/禁入相关天数、计算财富并加载面板，不据此推断银行整个财务公式。
- R12：**_rich4_buy_stock** 的一般证券分支读股价、扣 +32 银行资金并更新持仓均价；特定商业企业购买分支可扣 +28 现金。卖出中按参数写回存款或其他账户/资金池。**_rich4_update_commercial_owner** 在交易末尾调用。
- R14：静态股票总表共有 96 条初始化数据，但每地图在存档段可见 **12** 只股票，不应称“同时交易96支”。[B06/B08/B13/B20]

### 2.4 卡片/神明

- R16/R17：30 张卡/13 项工具表具可读顺序，但卡片效果的全体参数语义不能光凭未命名数字确定。
- R18：**_rich4_attach_god** 首先判定既有神明，按状态卸载、清除地图对象并设置新 god_info（玩家结构 +63），从数据表调整若干状态并通过跳转表触发具体能力。
- R06：遥控骰子是工具而非卡；AI 分支从 **_rich4_get_ai_tool_param_value** 获取参数。未来对照应分清原作卡牌、道具与神明三个实体。[B09/B10/B18]

### 2.5 电脑策略

- R19 **fcn_0041e69e** 根据卡片表值、玩家属性和随机数判断是否激活，并通过 ref_00475328 查回调入口。
- R20 **fcn_00420e9a** 的工具对应 ref_004753a0 调用表，后续访问租金、负面关系与地产状态。
- **不能断言**“AI 智能”“稳赢某难度”；只证明策略基于参数/情形/概率，而非纯随机。需要同种子输入多轮记录参数→动作→资产序列。[B11]

### 2.6 SAVE/LOAD

- R22 **_rich4_save_game_to_file** 从文件标识 0x26、日期、地图 ID、玩家总数开始写，玩家表固定四槽、每槽 0x68 字节，然后对象、卡、道具及其他全局状态。
- R21 **_rich4_load_game_from_file** 按顺序读取，并将角色名指针由角色模板重新绑定为运行时地址，说明二进制文件不是可直接 memcpy 给现代 JavaScript 的结构。
- R23 文件说明定位 0xC 处玩家数、0x10 玩家表、0x654 卡槽、0x690 道具；已和保存源码前段交叉核对，但**未对一份合法 SAVE 文件做十六进制/往返校验**。这不是 ReactMono 新 JSON 存档协议。[B12/B13]

## 3. 资源文件结构实核

可与 [文档](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/csrc/mkf/mkf-format.md#L4) 和 [C 实现](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/csrc/mkf/mkf.c#L132) 同时对照：

1. MKF 文件 offset 0 的 32 位 little-endian 值定位末尾资源索引表；索引表按 32 位整数保存各块的文件偏移。
2. 每块头四个 little-endian 32 位数（合计 16 字节）：未压缩长度、当前压缩长度、图像部分偏移、图像部分字节数。
3. **read_mkf** 直接读取原字节或调用 **mkf_decompress**；图像部分经像素布局更新，再检查 SPR/SMP 签名。
4. SPR 第一块 image data 从 start_offset + 512 起算，SMP 从 start_offset 起算；后续块按 chunk.gsize 累加。
5. MAP.MKF 可包含场景贴图和数据；R02 优先尝试 MAPDAT.MKF，若缺失才回退到 MAP.MKF 对应条目。v3.11 8 张地图属于该逆向目标，**不是授权资源清单**。
6. 任何解析器都应先校验文件长、索引偏移、长度溢出、块界限、SPR/SMP 计数与二维像素大小，避免因旧 C 的非安全输入假定导致越界。这里是安全建议，不是已对原作者二进制做漏洞评估。[B02/B03/B14]

## 4. 可重复的人工核查指令

后续研究者如果具备 Git 和许可的工具链，可在**私人、不随本仓库提交的工作区**运行以下命令。这里列出**复核协议，不宣称在本轮已成功执行**。

    git clone https://github.com/mytbk/rich4.git
    cd rich4
    git checkout --detach f81954d6a5675f63297036f9252720c6ca32a2b4
    git rev-parse HEAD
    git show -s --format='%H %cI %s' HEAD
    git grep -nE '_rich4_calculate_land_toll|_rich4_handle_player_land_on_node|_rich4_buy_stock|_rich4_attach_god|_rich4_save_game_to_file'
    sed -n '229,298p' asm/rich4_player_core_actions.asm
    sed -n '94,224p' asm/rich4_stocks.asm
    sed -n '529,620p' asm/rich4_save_files.asm
    sed -n '32,59p;132,173p' csrc/mkf/mkf.c
    sed -n '1,80p' asm/Makefile

如果研究环境为有 32 位 Windows 交叉编译和 Wine 支持的 Linux，独立测试所需前置为 **i686-w64-mingw32-gcc、nasm、make、32 位 Wine/Win32 依赖、原作者已标明版本的合法游戏目录**：

    cd asm
    make
    file rich4_mscrt.exe
    # 仅在合法自有的原版游戏数据目录，手动运行：
    # wine ./rich4_mscrt.exe

这些是原仓库的构建/运行思路，**不是本次成功日志**。不能把版权 exe、MKF、存档、反汇编二进制缓存、游戏截图复制进 ReactMono 仓库。原作者提供的 EXE SHA256 可用本地合法原版文件做：

    sha256sum /path/to/privately-owned/rich4.exe
    # 与 readme.rst 所列 sha256 对照；版本不同不应视为相同测试目标

MKF 工具自带回归由 [runtest.sh](https://github.com/mytbk/rich4/blob/f81954d6a5675f63297036f9252720c6ca32a2b4/csrc/mkf/test/runtest.sh#L1) 定义，要求 **gcc -m32** 且原版 **Data.mkf**。脚本的测试前置条件不能省略：

    cd csrc/mkf/test
    # 私有且合法获得的 Data.mkf 需存在于此临时工作目录
    sha1sum -c Data.mkf.sha1
    sh runtest.sh

若 Data.mkf 不存在，则 sha1sum 检查失败或跳过；**不能据此说解压实现失败**。若链接器报缺 32 位库，则应记录 gcc -m32 依赖缺失，而不是冒称资源格式异常。没有实际日志/结果的命令均为“待运行”。

## 5. 本轮实测边界与真实性记录

| 项目 | 本次状态 | 原因与不作的宣称 |
| --- | --- | --- |
| 上游当前 HEAD 与文件/行号 | **完成静态核查** | GitHub 连接器读取固定完整提交的文件；真实源码行/符号可经上述永久链接复查，属 **B** |
| 上游 C/ASM 构建 | **未执行** | 隔离 shell 对 github.com 域名解析失败，缺 NASM/i686 MinGW；GitHub 连接器读取不等于本地 git clone |
| Wine 启动与完整对局 | **未执行** | 无 32 位 Wine 和正版原版目录/声音资源；作者启动说明为 **C** |
| MKF 解包测试 | **未执行** | 缺 Data.mkf（原版商业数据）、gcc -m32 依赖 |
| 原版 rich4.exe 哈希 | **未执行** | 原始可执行程序并未提供，不能核对 v3.11 作者摘要 |
| 真机/截图/音频/玩家体验 | **无产物** | 禁止伪造 A 证据与上传未经授权商业素材 |
| ReactMono 架构差异 | **完成源码对照** | 读取 target dev 下 maps.ts、turns.ts、cards.ts、bank.ts、stocks.ts、save.ts 的实现，为 **B**，不是原版移植 |

**本文所有链接均与固定提交对应**。某些行号以范围列出，其含义是研究定位范围，不是精确覆盖整个被调用过程；后续请结合标签/跳表与原版运行 trace 复核。