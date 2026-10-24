# 移动主板面场景

## 实现与边界（2026-10-24，#148）

`main_scene.py`143物理行转写固定`tools/native_game.cpp::Application::draw_board()`的场景构造段，复用已经逐值对照的静止场景/物件/待播人物辅助。`表现步_类`保持原可选事件/效果数据，正式队列应按原`after_events`顺序提供；本模块不自行推进规则。

- 显示回合取尚在表现的玩家，`None`和玩家0分开；呈现完毕恢复真实当前玩家。
- 玩家及槽4–8特殊角色以原端点/已过时间/总时长插值，负方向整数除法向零截断。玩家移动时朝向依步进向量计算，特殊角色保留原字段方向。
- 附身神明/炸弹跟随当前绘制位置和朝向；投掷帧0有效，服装、水面、梦游与受伤标志保留。
- 待播运输人物覆盖真实世界已移动/隐藏的角色，首个电影优先；把同一待播列表交给真实电影播放器。
- 尚未呈现的购地/升级及神明升级通知按队列逆序撤回场景中的业主/等级，世界值仍保持真实已结算状态。
- 相机依次取当前绘制人物、自由中心、等待决策的目标中心、有效说话者当前绘制位置；高优先级覆盖前项。
- 当前电影和应用队列中的待抛物从地面隐藏，附身物件不受地面隐藏谓词影响。地产/设施/公司/业主颜色与特殊角色状态完整传给渲染器。

## 自动验证

四项定向测试从缺模块失败推进到通过，完整Python418/418、Ruff通过。原八图、72种显式状态及六组移动/全局时钟的[3456完整场景](evidence/main-scene-differential.json)，连同相机、显示玩家、待播人物以及世界完整DAT和随机状态不变，对照一致。

参考适配器直接从固定原`native_game.cpp`读取1456–1599行：从`void draw_board()`到真实`board_->render(...)`为止，保留构造语句与调用顺序并仅补闭合花括号。原文本SHA256记录在报告；不手写一份C++场景算法作为期望。使用原GameSession、MainScreen及effects辅助，渲染调用处捕获完整Scene供比较。

这是一条明确的源码切片边界：外部`sync_decision()`在此宿主中为空，忙碌/焦点/目标/骰姿态是显式夹具；末端使用场景捕获器，不绘制图片。没有编译完整Application、没有GUI输入/最终画布/音频证据，也不把这些移动状态称为自然规则产生的移动。

首轮发现移动槽位`v%9`与特殊角色停用状态夹具相关，虽然选到全部槽位，部分角色从未实际显示其移动。补充[13824场景交叉网格](evidence/main-scene-movement-grid.json)通过：八图×32状态×9独立移动槽×六时钟/插值点，不再让选槽和停用条件绑定。四名玩家及槽4–8均有可见移动状态。两组语料重叠，不相加冒充更多独立覆盖。开发脚本添加开关时漏增方法形参的TypeError已修正，正式实现未为适配器改规则。

```sh
uv run --project pygame python pygame/tools/differential_main_scene.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --assets /Users/laocao/Downloads/Rich4 \
  --report .research-cache/main-scene-differential.json
# 独立移动槽交叉网格
uv run --project pygame python pygame/tools/differential_main_scene.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --assets /Users/laocao/Downloads/Rich4 \
  --report .research-cache/main-scene-movement-grid.json --movement-grid
```

## 后续接线

正式应用仍须同步真实决策，按原`observe/pump_presentation`交错事件和效果，在队列/消息/骰子/电影/专属屏幕忙碌时暂停核心。场景值一致不能替代与MainScreen、消息、电影及菜单叠加后的像素、桌面操作和图形自然长局验收。相机冷中心停顿仍是 [板面](BOARD.md) 的未解决项。
