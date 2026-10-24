# 原小游戏画面与Pygame入口

规则见 [逐tick逻辑](MINIGAMES.md)，本增量对应固定`tools/screens/minigames.cpp`、`native_frame.hpp::Artwork`、`screens/draw.cpp::raw_picture`。Python为`artwork.py`、`minigame_presentation.py`及独立窗口工具，不依赖C++运行游戏。

## 画面、时序与输入

原Panel背景/帧、RGB555原图、LCD数字位置和大分数中心排版、企鹅洞/分数背景盖章、387像素游戏场裁切、原未缩放锚点的最近邻缩放、READY/GO与爆炸FLC均已移植。图像缓存与可写背景分离，防止洞盖章污染下次游戏。

显示帧按原上限100ms计入时间，准备FLC以自己的间隔推进并阻塞规则；结束后清除规则时间积余。声音按原tick取出，循环/停止只影响当前匹配的循环音。点击产生的声音等待下一规则tick处理，未提前触发或改变随机流。完成分数/随机次数只提交一次。

企鹅先查原Panel81命中图，再按原椭圆距离及扫描顺序寻找40像素范围内最近有效格；气球点击和天降按下跟随沿原顺序。开发机器人照固定C++验收机器人访问和等待，未进入正式电脑规则或改变得分。真实主游戏中的小游戏决策接入尚待GameSession实现。

## 像素差分

```sh
uv run --project pygame python pygame/tools/differential_minigame_presentation.py \
  --source /path/to/pinned-cpp --build /tmp/rich4-cpp-core \
  --assets /path/to/Rich4 --font /path/to/system-font.ttc \
  --report /tmp/minigame-presentation-differential.json
```

测试直接编译**固定原生屏幕源文件**与原绘制辅助；字体仅满足原Frame构造，小游戏数字来自原精灵，不绘制系统字形。测试依赖FreeType开发库与macOS libiconv，不加入正式Python运行依赖。固定源未修改，没有用重写的“参考合成器”对照自己。

[20条时间线](evidence/minigame-presentation-differential.json) 包含9512命令：7573显示帧、292实际点击、20建立及1627选定画布快照。三游戏、两种子、手动输入策略/原验收机器人，以及天降人物0/7/11全部完成真实结算；所有结果和声音回调逐命令一致。选定1627张完整640×480 RGB555画布的499814400像素逐字节相同，覆盖阶段转换、全部经过的READY/GO帧、经过的爆炸帧和常规每七帧采样。没有声称每一显示帧均已比较。

六项新增单测覆盖缩放锚点/透明、显示时钟/准备阻塞、命中回退、盖章隔离/单次提交、图帧元数据和原图补黑。自审发现帧数函数不应为了计数而要求像素布局可解，补失败用例后按原元数据解析修复。完整Python242/242、Ruff通过。

## 可直接操作的Pygame入口

```sh
uv run --project pygame python pygame/tools/preview_minigames.py \
  --assets /path/to/Rich4 --game penguin
uv run --project pygame python pygame/tools/preview_minigames.py \
  --assets /path/to/Rich4 --game balloon
uv run --project pygame python pygame/tools/preview_minigames.py \
  --assets /path/to/Rich4 --game catcher --character 7
```

原画布640×480、等比留黑边、左键操作，天降按住跟随，`Esc`退出。完成后窗口退出；`--log`记录输入/阶段/结果/画布哈希。默认真实时间，`--auto`和`--fixed-ms`仅用于开发验证；`--silent`完全关闭音频。

工具用Pygame播放原Effect WAV和MIDI13/12/11，保留原循环请求，并使用固定源的0.6音效增益和0.28音乐音量参数。SDL_mixer MIDI后端及该音量参数不等价于已经证明与固定C++ FluidSynth合成/限制器波形一致；完整主游戏音频系统仍待移植。

[三入口冒烟报告](evidence/minigame-pygame-smoke.json) 在dummy显示/音频配置、100ms开发步长下真实结算：企鹅63分/28随机、气球73分/1463随机、天降55分/174随机；原WAV/MIDI载入及播放路径成功。天降截图仅本地检查，未上传商业图片。

这不是实际桌面点击、人类听感或完整游戏试玩。原输入/绘制像素已自动对照，真实窗口操作、音频波形/听感以及GameSession主流接回仍待验收。

## 正式主游戏交接增量

三个小游戏已从真实新局的自然首回合触发，正常表现路径分别完成实际小游戏并返回主游戏；1979完整画布与逐步世界DAT/RNG/阶段直接对照原Application一致。输入只是实际902控件中心点击，得分由规则计算，无预置结果。详见 [主应用交接](APPLICATION.md)，音频/OS桌面/真人玩法仍未因此通过。
