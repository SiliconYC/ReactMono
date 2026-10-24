# 原玩家交易公告栏

## 实现与规则依据（2026-10-24，#153）

`trading_board_screen.py`416行、图文85行、类型54行，对应固定`market.cpp::TradingBoard`及辅助函数。原Panel73公告栏、四分类、股票数量/价格两级数字板、五地产分类/十一行分页、道具与卡片格、报价详情、满栏/失败通知和按钮命中顺序均保留。真实`交易_类`提供报价、可售项目与限价，主应用须提供实际挂牌/撤件/购买/关闭动作。

报价详情是原值快照；行情/所有权已变时不偷偷刷新成新报价。原股票数量转为uint16、价格上限及参考价直接取规则层，取消数值0不等于成功挂牌。地产行价与核心总资产口径的区别沿用 [玩家查询](PLAYER_INFO.md)，不重算成新规则。滚动`>=行数`归零，与玩家查询的`>行数`不同；按钮按其原窗口/外侧吞点击顺序注册。

公告栏只负责提出动作；出售不预留库存，购买在规则层检查现金、所有权、库存和失效报价。通知1500毫秒，到期只停止绘制，原字符串仍保留。原财产展示仍基于参考已实现的数据模型，不代表1998年官方所有规则均已证实。

## 自动证据

四项定向测试通过，其中实际交易回调验证挂牌时资产不动，购买按钮成交才扣买家现金、加卖家银行、转移道具并撤去报价。工作树同时包含下一阶段物品屏幕，其测试数单独记录，独立集成以本批文件为准。

[基础差分](evidence/trading-board-differential.json)2301命令/887画布，[全部物品操作扩展](evidence/trading-board-expanded.json)2434命令/871画布，合计4735命令、1758完整640×480画布/540057600像素；全部私有状态、数字板状态、按钮、声音请求、动作参数/结果和每步完整World DAT逐字节一致。绘制前后也各自检查世界不变，实际交易按钮允许真实规则改变世界。工具直接编入原`market.cpp`、调用原`trading::post/cancel/buy`，不作为正式运行后端。

八图、五地产分类/分页、十二人物×四槽、七件满栏、各类报价详情、真实现金不足、失效报价快照、空库存分类均有显式夹具。四槽×全部13道具/30卡片逐项通过真实数字输入挂牌与撤件；这些是可重复组件操作，不能称自然对局。回调拒绝模式只用于测试UI失败路径，正式组件没有默认伪成功动作；所有预期按钮必须存在、准备报价必须真正挂牌成功，避免对照空流程。

首轮适配器误用`股票`代替`持仓`、把原15字节道具数组缩成13、使用不存在的`存款`动态属性而未清`银行`。完整DAT对照在偏移48捕获最后一项；修正适配器后通过，运行时规则未改。三份失败报告分别留存：[持仓字段](evidence/trading-board-adapter-failure.json)、[固定数组](evidence/trading-board-array-failure.json)、[银行字段](evidence/trading-board-bank-field-failure.json)。这些属于测试工具错误，不伪称游戏规则修复。

```sh
uv run --project pygame python pygame/tools/differential_trading_board.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --assets /Users/laocao/Downloads/Rich4 \
  --font '/System/Library/Fonts/Hiragino Sans GB.ttc' \
  --report .research-cache/trading-board-initial.json
# 同参数加--expanded，报告使用另一路径。
```

## 尚未验收

正式Application/GameSession打开/关闭交易及主队列衔接、自然挂牌/购买、完整图形窗口、实际声音和听感仍待验。像素对照使用同机相同字体/FreeType，依赖哈希在报告，不证明其它平台或官方字体一致。素材、公司名、字体、原DAT和截图保持外部隔离。
