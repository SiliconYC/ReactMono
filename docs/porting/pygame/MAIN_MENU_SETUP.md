# 原主菜单与新局设置

## 实现与依赖（2026-10-24，#152）

`main_menu.py`78行、`new_game_screen.py`283行、`new_game_types.py`23行和`menu_random.py`31行对应固定`tools/screens/menus.cpp`的主菜单/新局部分及头文件。使用原Data1菜单、Data2十二头像、Jump八背景/设置面板和36条骑乘动画，不引入替代美术。菜单五入口仅提供强制回调，完整应用负责真正打开对应功能。

主菜单保留图片原点、首个悬选优先、仅变化才发悬选声、禁用读取仍可悬选和扩大EXIT点击区。新局保留六行设置外观、四行有效控件、人物撤选/人数收缩、地图切换、滚动暗背景、1100毫秒每次只补一位电脑，以及50毫秒步进的加速退场。重新打开保留六项设置并清人选/时钟/缓存/私有种子；取消优先关闭下拉，忙碌时不退出。

原参考的游戏时间/胜利条件行没有核心选项或终局规则，仍以原灰态显示，不擅自启用或制造结局。正式`Host.instant=False`使用原随机补位；`instant=True`的首个可用角色补位只保留原开发重放用途，不能冒充正式随机选择。最终回调传完整人物/人类数/交通/地图/资金/租期，原规则仍由真实核心创建与执行。

## 新局私有MT与跨语言经验

新局补位使用`std::mt19937`原始输出模剩余人数；它与核心Watcom流不同。`menu_random.py`是独立的纯Python32位MT，不使用Python默认播种协议，也不改变核心RNG。

[原始引擎对照](evidence/menu-random-differential.json)六个边界种子、60000输出与本机libc++完整624词序列化状态一致。初版按整块换词实现虽输出一致，不能直接把其数组与libc++逐词更新的序列化窗口比较；最终改成逐词递推并按下一输出位置旋转，才得到可重复的完整状态对照。标准库私有/序列化布局不能被假设为跨实现统一；这里未验证libstdc++的序列化格式，运行引擎不依赖该C++格式。

## 自动证据

七项定向测试及阶段Python468/468、Ruff通过。覆盖菜单禁用/悬选/退出区、重新打开、满员不消耗随机、开局参数、取消/忙碌与MT换块。

[基础差分](evidence/main-setup-differential.json)1946命令、1171完整画布/359731200像素；菜单五入口/读取禁用、八图×三交通×二至四人、人物/下拉、正式补位/退场与即时分支，完整私有逻辑状态/624词MT、按钮/声音请求及NewGameChoice一致。

[动画与生命周期补测](evidence/main-setup-lifecycle.json)1553命令、1205完整画布/370176000像素；预检36骑乘条目全部461帧，并实际逐帧画出每个人物/交通。独立覆盖1099/1100补位边界、全部50毫秒退场阶段、二至四人满员仍保留原等待、点击加速与最终选择。两批3499命令、2376画布/729907200像素一致。缓存键/尺寸比较，缓存图像经最终画布验证；不宣称对未显示缓存像素另做逐字节状态比较。

完整画布使用变化底图，逐字节比较，载入故障不算略过通过。报告包含依赖与外部字体SHA，使用同机同一字体/FreeType；不能外推其它平台或官方1998年程序。声音只是请求观察。

```sh
uv run --project pygame python pygame/tools/differential_main_setup.py \
  --source .research-upstreams/richman4-remastered \
  --build .research-cache/cpp-core \
  --assets /Users/laocao/Downloads/Rich4 \
  --font '/System/Library/Fonts/Hiragino Sans GB.ttc' \
  --report .research-cache/main-setup-initial.json
# 增加 --lifecycle-only，另存 main-setup-lifecycle.json
uv run --project pygame python pygame/tools/differential_menu_random.py \
  --build .research-cache/cpp-core --report .research-cache/menu-random-differential.json
```

## 尚未验收

这些是完整真实组件及明确输入的回调对照，不是正式应用的开局→银行/股票→保存→结局流程。完整主循环、原选项/存档槽/玩家查询等接线、音频和窗口人工操作仍在实施；不以菜单画布或新局参数回调宣称可玩整局。
