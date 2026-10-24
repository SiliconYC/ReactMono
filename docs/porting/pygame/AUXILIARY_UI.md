# 地图信息、帮助、开局与结局增量

固定参考与许可边界沿用 [总计划](PLAN.md)；跟踪 #155，正式接线仍属 #148。这里增量记录四个已核对原源文件的实现与证据，不重抄前期研究。

## 实施顺序与边界

先移植 `tile_popup.cpp`226行和 `help.cpp`197行，定向测试保留收费口径、角色优先拾取、列表八行滚动/跨重开状态、十四行及显式分页。直接编译原组件，使用八地图真实世界、真实外部素材和同一字体比较完整画布、私有状态、按钮/声音请求与世界只读。再分别接入 `intro.cpp`141行与 `endgame.cpp`269行，逐帧比较原电影/声音时点、倒数、追逐和续图选择，最后交给正式主应用。

参考 `instance_at` 明确使用投影锚点包围盒近似原 ID 缓冲；本移植保留它，不把与 C++ 一致称为官方像素拾取。研究所产出道具那一行在参考中因未解字段省略，也需明确记录。帮助正文只读外部 `help.mkf`；冬眠说明按公开源码修正该包里的红卡拷贝。源码短标签按 GPL 派生，不发布商业正文或画面。

初始记录仅进入实现；下面分批记录实际通过范围。开局AVI占位、400毫秒Loading等参考自身未证官方时长，以及已清全部地图后的结局AVI缺失，将随对应模块记录。

## 地图信息与帮助自动验收（2026-10-24，#155）

四运行模块共532行：`tile_pick.py`77、`tile_popup.py`160、`help_screen.py`160、公开源码短目录`help_topics.py`135。五项定向测试、同树511项通过，其中本批提交对应507项，下一批开局/结局的四测试和实现单独留在开发树，不混入本批合并。

[完整组件对照](evidence/auxiliary-ui-differential.json)36211命令、8847完整画布/2717798400像素及全部文字/页面、私有状态、按钮/声音请求、世界DAT逐步一致。八地图×六组业主/等级/连锁/类型显示夹具，11616次全部有效表项文字与边界、8448次四方向/玩家/物件弹框，15488次八旋转/两个实际节点中心拾取，全部99话题与原列表/页面/重开状态覆盖。世界修改仅来自明确展示夹具；查询/绘制/帮助动作均检查DAT不变。没有将这些夹具当作自然事件或真实桌面操作。

[正文预检](evidence/auxiliary-ui-resources.json)逐项确认外部99话题均有非空资源与解读内容，实际123页/1054行，防止原组件与Python共同回退空页而误判。报告只发布尺寸/摘要/页行数，不发布商业正文。[14命令短流程](evidence/auxiliary-ui-smoke.json)为完整组子集，不重复累计。

两次移植偏差通过差分发现并加RED回归后修复：[金额前缀遗漏](evidence/auxiliary-ui-currency-failure.json)源于误用无`$`分组格式，现按`ui::money`；[原点错位](evidence/auxiliary-ui-anchor-failure.json)源于误用抵消原点的`Frame.picture`，原弹框直接`blit`到点击锚点，现已保留。最初测试夹具只有一块地产，已显式复制第二块供同街汇总测试，没有放宽运行世界规则。曾误写已有投影/字样类名的导入，定位后改为现有公开API；未改既有模块。

参考拾取是包围盒近似，研究所省略道具名称、触屏EXIT/放大命中和帮助字体无阴影均是固定C++设计，不证明官方1998行为。完整主程序、自然触发、真实窗口/音频尚未验收。

```sh
uv run --project pygame python pygame/tools/differential_auxiliary_ui.py \
  --source .research-upstreams/richman4-remastered --build .research-cache/cpp-core \
  --assets /path/to/Rich4 --font /path/to/font.ttc \
  --report .research-cache/auxiliary-ui.json
```

`--smoke`只跑短流程；`--resources`生成正文存在/分页预检，不运行C++。原消息绘图所需`SDL_GetTicks`仅在测试提供常零符号，当前屏幕不读取它，正式Python包无该符号或C++。
