# Pygame《大富翁4》移植子项目

状态：**固定 C++ 桌面范围的 macOS 移植已交付**。默认入口包含原菜单、新局、八地图、独立规则、专属界面、保存槽、托管和音频；验收范围、参考自身缺口与平台限制见 [移植台账](../docs/porting/pygame/README.md)。原 React 游戏保持独立。

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

### Windows：Conda `vt` 双击启动

Windows 10/11 可在仓库根目录双击 `Play-Pygame.bat`，也可以进入 `pygame/` 双击 `start-game.bat`。两个入口运行的是同一套 Pygame 主游戏，不是 React 浏览器版。无需从 Anaconda Prompt 手动激活环境；启动器会优先寻找当前 Conda，再检查常见 Anaconda、Miniconda 安装目录，并且**只使用名为 `vt` 的环境**，不会退回 `base` 或其它 Python。

- **一次性前提**：Windows 已安装 Conda，并且现有 `vt` 环境使用 Python 3.11 或更新版本。启动器只使用 `vt`，不会退回 `base` 或其它 Python；若 `vt` 的版本过旧，会提示升级该环境。
- **正版素材**：本机必须有 `pygame/assets/manifest.json` 及相应授权导入文件。此目录被 Git 忽略，克隆或拉取仓库不会获得这些文件；导入方式见上面的 `import_open_assets.py` 命令。
- **首次依赖**：检测到 `vt` 缺少指定的 Pygame 2.6.1 时，启动器会在 `vt` 内安装该版本；后续通过当前源码目录直接启动。游戏使用 `pythonw.exe` 运行，游戏窗口正常显示且不附带 Python 控制台；环境检查和首次安装失败仍会在启动器控制台提示。

Windows 原生音频尚未通过实机验收。启动时将检查 SDL3、FluidSynth 及当前 Pygame 的 SDL2 接口；若不可用，会**明确提示并使用 `--silent` 启动真实游戏**，避免音频缺失直接阻止打开游戏。该模式没有音乐、音效与语音，但不改变游戏规则。提供兼容的本机原生库之后会再次尝试启用音频，不能将启动器静态检查当作 Windows 完整试玩通过。macOS 的 `start-game.command` 保持不变。

默认真实规则与时钟，960×720窗口显示原640×480画布，等比最近邻缩放与黑边。原菜单选择人物/地图后进入对局，鼠标操作原控件，`Esc`按原路径返回。存档缺省写入游戏自身的`pygame/userdata/saves/`；`--save-dir`可明确覆盖；`--load`读取原DAT及RNG旁车；`--silent`关闭音频。声音缺省跟随系统默认输出及其切换；需要固定设备时使用`--audio-device '设备名称'`或`RICH4_AUDIO_DEVICE`，无效名称明确报错。

当前用户已实际试玩并确认操作/画面、BGM/点击音效/角色语音及运行中耳机拔插正常；这是有限流程的人工反馈。完整长局已有加速自动差分，两文件写入强杀恢复已有真实进程验证，见 [恢复说明](../docs/porting/pygame/RECOVERY.md)。原参考不提供任意中途完整检查点；全部地图/功能逐项人工验收没有冒领为完成，见 [主应用记录](../docs/porting/pygame/APPLICATION.md)。

`--headless --frames 2`只用于有限帧冒烟运行，不能当作游戏验收。`--screenshot`只写本地忽略目录。音频需要标准SDL3/FluidSynth运行库，GM音库已由导入工具部署到自己的素材目录；缺少依赖应显式处理，不以静音假装成功。

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
uv build --project pygame
uv run --project pygame python pygame/tools/audit_distribution.py
uv run --project pygame python pygame/tools/source_inventory.py \
  --source /path/to/pinned-cpp --output /tmp/source-inventory.json
uv run --project pygame python pygame/tools/differential_assets.py \
  --source /path/to/pinned-cpp --build /tmp/rich4-cpp-core \
  --assets /path/to/Rich4 --report /tmp/assets-differential.json
```

差分工具会核对参考提交、构建固定 C++ 核心，在临时目录比较全部解码字节及首尾图像/动画帧，退出后移除商业解码文件；报告只含元数据和哈希。C++ 不参与正常 Pygame 运行。合成样本为格式边界测试，不作为真实游戏事件或规则替代。

源码及素材权利边界见 [NOTICE.md](NOTICE.md)。

## 主游戏音频依赖

原WAV转换、完整混音、语音队列与MIDI已逐采样对照，主应用已接线；已取得本机设备与有限真人听感验收，长期/其它平台限制见音频记录。开发依赖可在独立Worktree的忽略缓存构建，不安装系统包：

```sh
uv run --project pygame python pygame/tools/build_audio_dependencies.py --workspace . --jobs 4
mkdir -p pygame/.local/lib
cp .research-cache/audio-runtime/lib/libSDL3.dylib pygame/.local/lib/
cp .research-cache/audio-runtime/lib/libfluidsynth.dylib pygame/.local/lib/
uv run --project pygame rich4-pygame
```

以上复制命令为已验收的macOS配置；工具需要已有CMake/GLib，Linux共享库通常为`libSDL3.so`，其它平台尚未进行同等部署验收。正式游戏优先使用`pygame/.local/lib/`，不依赖研究缓存；显式库参数或环境变量仍优先。GM音库固定读自己的`assets/music/`。设备探针、离线波形与用户实际听感分别留痕，细节与可复现命令见 [音频记录](../docs/porting/pygame/AUDIO.md)。
