# 原金额机与爱神轮盘

## 实现与规则分工（2026-10-24，#149）

`spinner_screen.py`278物理行对应固定`tools/screens/spinners.cpp/.hpp`。真实交互决策只读取核心`SpinnerState`并注册STOP回调，数字/结果仍由核心推进与结算。电脑金额效果从核心提供的种子建立私有Watcom随机流，重放原MoneySpinner；不把已结算金额再次写回世界，不使用固定数位或固定轮盘结果。

机器四类神明、三/四数位、原绘制位置、半数字帧、拉杆及结果文本均保留。神名指针表0x47ed7a、四种提示起点0x4652ab/0x4652c3/0x4652d3/0x4652e9、轮盘格式表0x475cf8及公司股票名称仅从外部原程序读取；不内置商业长文。普通字体/原文边界见 [字体](NATIVE_UI.md) 与 [消息](MESSAGES.md)。

- 金额机每30毫秒一步，轮盘每36毫秒一步；传入的单次时长先钳制100毫秒，第一帧也消费传入时长，区别于EffectPlayer的首帧重置。
- 电脑轮盘第40步射箭，随后按原计数/周期减速，停在类型对应的非空格，结果保持40步；人类已STOP效果在结果阶段可点击提前结束。
- `draw_decision`保留宿主按钮清理契约，注册全屏STOP且关闭通用点击音；`draw_effect`实际运行时清空覆盖操作，只在原人类结果阶段注册跳过。
- 收帧才应用循环声51/52的变化并清待循环。`clear()`只清队列/当前电影，不擅自重置决策阶段、跳过策略或循环标志；循环停止依原发生在后续收帧。
- `set_skip`只影响新入队，不追溯删除已开始或已排队效果；入队按值复制，并依原只要求存在`spinner`数据，正常应用路由另用`handles`限制种类。

## 自动证据

五项新定向测试、完整Python428/428、Ruff通过。定向覆盖三/四位金额及半数位、队列值拷贝/跳过、循环切换/清空、自动STOP和结果持有，未用单元夹具代替真实美术。

[完整组件对照](evidence/spinner-screen-differential.json)直接编译未修改的原`Spinners`和消息文字辅助，共3853命令、1830实际绘制640×480画布/562176000像素一致。基础覆盖八图、四类机器0–10阶段/数位组合、五种轮盘类型值（含255的原屏幕掩码行为）×12游标、名称有效/无效主体、全部handles数据存在判定。另有四机器及四轮盘×电脑/人类已停止共12条完整重放，逐绘制帧比较私有机器/轮盘/RNG全部状态、队列、按钮及声音请求；时长含0、29、1、30、60、100与9999毫秒。

[生命周期补测](evidence/spinner-screen-lifecycle.json)158命令、70实际画布/21504000像素一致，覆盖播放中清空、跳过非追溯、循环停止时点、决策阶段跨clear保留与连续轮盘→机器队列。总计1900实际绘制画布/583680000像素；非绘制命令只比较完整状态，不把空白模式画布计作动画帧。

每条命令另检查Python世界完整DAT在绘制前后不变。字体SHA256在报告；和参考使用同机同一FreeType字形路径，不能外推其它平台字体或官方1998年GDI完全一致。外部资源读取/解码故障会使适配器失败，不把略过图片算作通过。

```sh
uv run --project pygame python pygame/tools/differential_spinner_screen.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --assets /Users/laocao/Downloads/Rich4 \
  --font '/System/Library/Fonts/Hiragino Sans GB.ttc' \
  --report .research-cache/spinner-screen-differential.json
# 同命令增加 --lifecycle-only，另存生命周期报告
```

## 尚未验收

这些是明确的交互状态/已结算效果夹具，不是自然落点触发。按钮回调、一次音与循环音都由适配器观察，尚非完整主应用的真实STOP、实际音频波形/听感或窗口流程。正式主循环、股利/开奖/月报屏幕及金融菜单仍需实现/接线；不能据本组件通过宣称完整游戏。
