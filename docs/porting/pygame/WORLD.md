# 世界、存档与初始状态接口

依据固定 `save.hpp/world.hpp/world.cpp/world_validation.cpp`，规则与图形宿主只能通过已解读模型读写数据，未知字节仍保留。当前已完成原档模型恢复与八图初始化，未实现运行中会话恢复。

## 类型对应

| C++ | Python | 说明 |
| --- | --- | --- |
| `SaveHeader/PlayerState/MapSummary/SaveRegion` | `save_records.py` | 原始日/月/年与字段；归档解码不强制可玩规则 |
| `World` | `world.py::世界_类` | `api_从存档/api_从地图/api_导出/api_清破产字段/api_活跃玩家` |
| `PlayerStatus/WorldPlayer` | `world_player.py` | 全部策略、状态天数、计数与四份敌意；存档玩家记录另存 |
| `StockHolding/StockState/TradeOffer` | `world_stocks.py` | 保留成本和股票浮点的原32位编码 |
| `MapNode/Land/Facility/Commercial/Landscape` | `world_map.py` | 原编号、五表与零号项；事件复合码不重新编号 |
| `SpecialActor/MapObject` | `world_actors.py` | 特殊角色、物件与原运动浮点位 |
| `NewGamePlayer/NewGameOptions` | `world_options.py` | 默认值来自参考核心；宿主后续显式传入用户设置和当前日期 |
| `profiles/initial_stocks/initial_cards` | `world_defaults.py` | 12角色数值、96股票数值、30卡供应；没有商业名字/素材 |
| `validate_playable_world` | `world_validation.py::世界验证_类.api_验证` | 不修改世界；归档允许的某些字节在可玩会话中须拒绝 |

逐函数定位与测试见 [映射](mapping.json) 和 [清单](source-inventory.json)。

## 原样保留与导出

DAT 主地图块起点 `0x274B`；五表相对偏移和原步长 `40/52/56/52/28`，数量不含零号记录。导出拒绝增删表记录、改变编号或玩家数量。Python 中额外显式检查固定数组大小，以补回 C++ 类型系统的 `std::array` 约束。

世界保留未知字段、历史玩家快照、尾字节、序列化旧地址和名字填充。旧地址永不解引用。未改动名字即使未以 NUL 结束也按原样保留；变更的地产/设施名字最多15个原编码非 NUL 字节。节点、公司和景物名字按参考仅供只读显示，不回写。

破产清除只清玩家104字节记录的28..103；策略、控制字节、独立卡/道具、持仓表仍按 C++ 保留，不以重建整个玩家对象代替。原始 binary32 位与 NaN payload 在归档模型中保留；可玩验证明确拒绝非有限值，两个层次不能混同。

## 初始化与随机流

全局图号 `stage*4+map` 对应 `map.mkf` 奇数元数据条目。原点零表示首次回合延迟出生；显式起点按原邻居顺序消费一次 Watcom 随机数。角色策略、现金/银行比例、交通骰数、初始道具供应、公司股份和96股票表均来自固定 C++ 数值。

新闻/命运洗牌从剩余的有序候选选择第 `rng % remaining` 项；不能换成 Fisher–Yates 或 Python `random.shuffle`。`初始随机状态/有初始随机状态` 明确区别新局与原DAT：旧DAT不包含随机流状态，不能据模型往返宣称会话随机流已恢复。

## 可玩验证边界

检查玩家/地图引用、物件/神明引用、牌堆排列、股价/成本/股史有限性、出售类型与项目等。未活跃特殊角色、未引用且无位置/附身的物件保留无效旧值；空出售项保留其他字段；交通和状态日高位有原玩法语义，不能当普通计数范围截断。

验证器当前跨语言对比了两份真实原档与72组八图新局的接受结果；损坏输入的主要拒绝边界有局部测试，尚非穷举跨语言错误状态差分。正式宿主在替换会话或写入导入世界前必须调用验证器，且不得通过吞异常继续运行。
