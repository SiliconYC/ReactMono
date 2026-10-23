# Pygame《大富翁4》移植子项目

状态：**移植进行中，尚不是完整可玩游戏**。现有资源/棋盘验收入口和可独立操作的三个原小游戏；当前进度与缺口见 [移植台账](../docs/porting/pygame/README.md)。原 React 游戏保持独立。

## 环境与运行

使用 Python 3.12 与 Pygame 2.6.1。推荐独立 CPython，避免本机 Conda 的 `readline` 原生扩展冲突。以下命令在仓库根目录执行；`/path/to/Rich4` 必须是自己合法持有的外部原版素材目录。

```sh
uv sync --project pygame --python 3.12
uv run --project pygame rich4-pygame --assets /path/to/Rich4 --archive Data.mkf --entry 601
uv run --project pygame rich4-pygame --assets /path/to/Rich4 --archive Data.mkf --entry 128
```

窗口保持 640×480 逻辑画布，缩放时等比留黑边；左右键切换资源内精灵帧，`Esc` 退出。`--frame` 指定初始帧；`--screenshot` 只写本地忽略目录，`--frames` 用于有限帧窗口冒烟运行。不接收或假装执行任何尚未实现的游戏指令。

地图合成工具可读取全部八图：

```sh
uv run --project pygame python pygame/tools/preview_board.py --assets /path/to/Rich4
```

方向键平移，`Q/E`旋转，`F`换人物帧，`Tab`换图，`Home`归位，`Esc`退出。`Space`是精灵帧采样，不是正式动画时序。黑色应用栏/侧栏尚无游戏UI，也没有可玩的回合；性能与真实桌面操作范围见 [棋盘说明](../docs/porting/pygame/BOARD.md)。

三个原小游戏可独立操作：

```sh
uv run --project pygame python pygame/tools/preview_minigames.py --assets /path/to/Rich4 --game penguin
uv run --project pygame python pygame/tools/preview_minigames.py --assets /path/to/Rich4 --game balloon
uv run --project pygame python pygame/tools/preview_minigames.py --assets /path/to/Rich4 --game catcher --character 7
```

鼠标左键操作，天降按住跟随；原WAV/MIDI由外部素材载入，`--silent`静音，`Esc`退出。完成后关闭窗口并可通过`--log`保存结果/输入/随机状态/画布哈希。默认真实时钟，`--auto`、`--fixed-ms`只供开发验证。像素对照与音频/桌面验收边界见 [画面说明](../docs/porting/pygame/MINIGAME_PRESENTATION.md)。

## 测试

```sh
uv run --project pygame python -m pytest pygame/tests -q
uv run --project pygame ruff check pygame
uv run --project pygame python pygame/tools/source_inventory.py \
  --source /path/to/pinned-cpp --output /tmp/source-inventory.json
uv run --project pygame python pygame/tools/differential_assets.py \
  --source /path/to/pinned-cpp --build /tmp/rich4-cpp-core \
  --assets /path/to/Rich4 --report /tmp/assets-differential.json
```

差分工具会核对参考提交、构建固定 C++ 核心，在临时目录比较全部解码字节及首尾图像/动画帧，退出后移除商业解码文件；报告只含元数据和哈希。C++ 不参与正常 Pygame 运行。合成样本为格式边界测试，不作为真实游戏事件或规则替代。

源码及素材权利边界见 [NOTICE.md](NOTICE.md)。
