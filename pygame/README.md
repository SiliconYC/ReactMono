# Pygame《大富翁4》移植子项目

状态：**真实主游戏已接通，完整移植验收未完成**。默认入口包含原菜单、新局、八地图、独立规则、专属界面、保存槽、托管和音频；当前进度与缺口见 [移植台账](../docs/porting/pygame/README.md)。原 React 游戏保持独立。

## 环境与运行

使用 Python 3.12 与 Pygame 2.6.1。推荐独立 CPython，避免本机 Conda 的 `readline` 原生扩展冲突。以下命令在仓库根目录执行。正版来源仅供一次性导入，正式游戏使用子项目自己的`pygame/assets/`，商业内容被Git忽略。

```sh
uv sync --project pygame --python 3.12
uv run --project pygame python pygame/tools/import_open_assets.py \
  --source /path/to/licensed/Rich4 --font /path/to/authorized-font.ttc \
  --soundbank /path/to/authorized-gm.dls
uv run --project pygame rich4-pygame
```

已完成导入时直接运行最后一行。所有图片、动画帧、音效/语音、音乐、字体、音库和原文字都位于游戏自己的资源目录；正式入口不再接受原MKF/EXE目录。源码差分/旧格式预览工具仍可只读正版来源用于研究，不能充当正式运行依赖。格式、审计、部署与旧副本清理记录见 [开放素材迁移](../docs/porting/pygame/OPEN_ASSETS.md)。

默认真实规则与时钟，960×720窗口显示原640×480画布，等比最近邻缩放与黑边。原菜单选择人物/地图后进入对局，鼠标操作原控件，`Esc`按原路径返回。`--save-dir`指定外部存档目录；`--load`读取原DAT及RNG旁车；`--silent`关闭音频。声音缺省跟随系统默认输出及其切换；需要固定设备时使用`--audio-device '设备名称'`或`RICH4_AUDIO_DEVICE`，无效名称明确报错。

当前用户已实际试玩并确认操作/画面、BGM/点击音效/角色语音及运行中耳机拔插正常；这是有限流程的人工反馈。完整长局已有加速自动差分，任意中途检查点、写入中断恢复与所有地图/功能人工验收仍未完成，见 [主应用记录](../docs/porting/pygame/APPLICATION.md)。

`--headless --frames 2`只用于有限帧冒烟运行，不能当作游戏验收。`--screenshot`只写本地忽略目录。音频需要标准SDL3/FluidSynth运行库及外部GM音库，配置见下文音频记录；缺少依赖应显式处理，不以静音假装成功。

原资源预览入口保留为独立命令：

```sh
uv run --project pygame rich4-preview --assets /path/to/Rich4 --archive Data.mkf --entry 601
uv run --project pygame rich4-preview --assets /path/to/Rich4 --archive Data.mkf --entry 128
```

左右键切换资源内精灵帧，`Esc`退出；`--frame`指定初始帧。

地图合成工具可读取全部八图：

```sh
uv run --project pygame python pygame/tools/preview_board.py --assets /path/to/Rich4
```

方向键平移，`Q/E`旋转，`F`换人物帧，`Tab`换图，`Home`归位，`Esc`退出。`Space`是精灵帧采样，不是正式动画时序。此独立棋盘工具的黑色栏没有主游戏UI或回合；性能与真实桌面操作范围见 [棋盘说明](../docs/porting/pygame/BOARD.md)。

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

## 主游戏音频依赖（移植中）

原WAV转换、完整混音、语音队列与MIDI已逐采样对照，主应用已接线；设备压力与听感验收继续实施。开发依赖可在独立Worktree的忽略缓存构建，不安装系统包：

```sh
uv run --project pygame python pygame/tools/build_audio_dependencies.py --workspace . --jobs 4
RICH4_SDL3_LIBRARY=/path/to/libSDL3.dylib uv run --project pygame python -m pytest pygame/tests -q
```

工具需要已有CMake/GLib；Linux共享库通常为`libSDL3.so`。音库从用户外部路径读取，当前没有把设备探针或声音请求当作完整音频验收，细节与可复现命令见 [音频记录](../docs/porting/pygame/AUDIO.md)。
