# 主游戏音频增量

固定参考 `native_audio.cpp`793行、`board_audio.hpp`170行、`audio_limiter.hpp`59行已核对；跟踪 #156，正式应用 #148。这里区分资源选择/策略、混音算法、设备契约与真实音频，不以声音编号一致代替实际播放。

## 策略、限幅与设备入口（2026-10-24）

三个运行模块284行：`audio_types.py`62、`board_audio.py`155、`audio_limiter.py`67；五项定向和阶段Python516项、Ruff通过。原三个循环通道、18上下文编号、走路/交通/水面/机器人/附身炸弹选择、原决策/节庆音乐、公共前缀退栈/单层替换、300毫秒音乐退场与150毫秒步行停止均有对应。

[原策略对照](evidence/board-audio-differential.json)8769命令，完整策略私有状态、资源编号/调用顺序及每步World DAT一致，查询检查世界不变。包含八地图、四玩家交通掩码/水面/特殊槽、越界节点的安全查询、全部21决策与七组年份的实际有效日期、零/最高uint64/倒退时钟、嵌套静音与忘记栈。越界节点只检验参考安全读取，不是可玩存档。C++直接编译原内联策略，`Audio`方法仅作为请求记录汇点；它没有运行原混音器，不将这些记录当作真实声音。

[原限幅对照](evidence/audio-limiter-differential.json)2496命令、2359728个采样值，输出及内部上限/释放/包络/增益的IEEE单精度位模式全部一致。四采样率（含零）、三上限、零/150毫秒释放、符号零/非正规数/NaN/无穷/最大有限值、奇数尾项、持续过载与静音释放均验。阈值内原样穿过、立体声共峰值与立即限制后释放有独立测试。采用同宿主标准数学库`expf`和显式单精度舍入；没有链接或调用C++参考引擎。其它平台数学库仍须复跑。

Pygame原生`_sdl2.audio.AudioDevice`可提供48000Hz、立体声F32、512帧/4096字节块：[dummy探针](evidence/audio-device-probe.json)24回调、[本机CoreAudio探针](evidence/audio-device-coreaudio-probe.json)22回调均通过。探针仅填零，证明设备契约，不证明真实音频已听到。初次按本机2.6.1内置文档传`devicename=None`被实际绑定拒绝（`TypeError: devicename must be a string`），现枚举设备并选择第一个，未伪造默认设备名称。

```sh
uv run --project pygame python pygame/tools/differential_board_audio.py \
  --source .research-upstreams/richman4-remastered --build .research-cache/cpp-core \
  --assets /path/to/Rich4 --report .research-cache/board-audio.json
uv run --project pygame python pygame/tools/differential_audio_limiter.py \
  --source .research-upstreams/richman4-remastered --build .research-cache/cpp-core \
  --report .research-cache/audio-limiter.json
uv run --project pygame python pygame/tools/probe_audio_device.py \
  --driver dummy --report .research-cache/audio-device.json
```

## 后续真实音频路径

原PCM为48000Hz立体声F32、每块512帧，语音单独中断/排队、最多16同时效果、效果/语音增益0.6，正常MIDI歌单`rich08/16–22.mid`及18上下文表按源保留。MIDI软件合成增益0.28、关闭混响/合唱、按采样推进，压栈需保留播放tick而非重头开始；静音时推迟重建，恢复后续播。三个循环槽独立，不能被转盘停止一起切断。

首批记录时完整混音/WAV/语音队列/MIDI/后台供料未实现；下面增量补齐WAV层。真实混音、语音队列、MIDI播放/恢复、后台供料和应用接线继续实施。外部音库、WAV、MIDI与捕获始终不入Git。

最终还需真实效果/语音重叠、循环/上下文切换、小游戏交接、长局时音频持续性、波形/时钟、听感和正式窗口验收。当前设备零样本、策略记录、数值限幅均不满足这些交付条件。

## 原WAV解码与重采样（2026-10-24，#156）

`wave_decoder.py`101行，保持原`decode_wave`的整条WAV载入、48000Hz立体声F32转换、正且8字节整除的输出长度和内存释放。通过标准SDL3公开C接口完成解码/重采样，Pygame负责后续窗口与设备；没有调用C++参考项目的任何运行逻辑。这样保留原重采样器，而不是假定Pygame SDL2转换与SDL3相同。原MKF仍由独立Python读取。

[完整转换对照](evidence/wave-differential.json)直接编译固定`native_audio.cpp::decode_wave`，1613输入/237033784个F32采样逐位一致。真实Effect115条中99个WAV、Speaking1374个WAV均明确要求非空原WAV成功转换，共1473条全部通过；16个空条目按原拒绝。另含80条截断、40组单双声道/8–32位PCM/8000–48000Hz合成格式和四个坏输入，合计1529次成功/84次拒绝。两端共同拒绝有效RIFF将立即失败，不能靠共同跳过报成功。空/坏输入只核对成功/失败分类，不声称错误文本完全相同。

两项真实SDK测试验证单声道16位转F32左右复制与坏WAV错误；设置`RICH4_SDL3_LIBRARY`后的阶段518项通过，无依赖时这两项明确跳过，不计通过。首次C++测试工具缺少`iostream`而编译失败，补齐测试端include后重跑；游戏运行代码未为此改动。完整对照后增加有效WAV门控/输出截断检查再跑，输入与全部状态/采样摘要仍相同。

### 固定依赖与复现

本机macOS14的Homebrew无预编译包并准备升级多项全局依赖，已停止该次安装，未安装其列出的SDK。现有CMake/GLib足够在忽略缓存构建：SDL3 3.4.18固定`829a65d769d935c4852f8159e964312c0957260a`，FluidSynth2.6.1固定`71e85b2ca6bf48641ba7e2261d8f2640ae473773`，双精度DSP、原生DLS开启，关闭不使用的FluidSynth设备后端/网络/SF3/混响扩展构建。安装位置、参数和公开来源见 [构建记录](evidence/audio-dependencies.json)，原库源码保持干净。它们是通用SDK，不含Rich4参考引擎；后续MIDI将用公开FluidSynth合成接口。

```sh
uv run --project pygame python pygame/tools/build_audio_dependencies.py --workspace . --jobs 4
PKG_CONFIG_PATH="$PWD/.research-cache/audio-runtime/lib/pkgconfig" \
uv run --project pygame python pygame/tools/differential_wave.py \
  --source .research-upstreams/richman4-remastered --build .research-cache/cpp-core \
  --assets /path/to/Rich4 --library .research-cache/audio-runtime/lib/libSDL3.dylib \
  --report .research-cache/wave.json
RICH4_SDL3_LIBRARY="$PWD/.research-cache/audio-runtime/lib/libSDL3.dylib" \
uv run --project pygame python -m pytest pygame/tests -q
```

以上命令在独立开发Worktree执行；Linux共享库后缀为`.so`，其余平台需复跑。构建工具只使用已有CMake/GLib，不自动安装系统包；GCEM等传递源码由FluidSynth原构建系统放缓存。原ABI与整条转换限制见 [SDL3接口](https://wiki.libsdl.org/SDL3/SDL_ConvertAudioSamples)，采样时钟设置见 [FluidSynth官方说明](https://www.fluidsynth.org/api/settings_player.html)。本批只验证解码与重采样；尚无真实混音/语音队列/MIDI或完整主应用听感通过结论。

## 原PCM混音、语音与循环控制（2026-10-24，#156）

`audio_pcm.py`119行、`audio_pcm_types.py`48行、`audio_player.py`157行，共324行。纯Python处理原512帧/1024个F32交错采样、0.6增益、最多16个效果、单语音中断/队列、三个独立循环、统计与原限幅。只缓存转换后的F32样本，不另永久缓存每条原WAV副本，保持原缓存的内存口径。设备与主线程将共用一把锁；trace由主线程送出，渲染只积存日志。

[原公开控制与实际混音块对照](evidence/pcm-differential.json)3881命令、4400128个输出采样逐位一致，包含全部片段来源/游标/语音/循环通道、队列/缓存键和长度、原13个统计字段、限幅内部状态、trace和显式更新时钟。全部99个有效音效、1374条真实语音、十二人物×27角色入口均实际调用并渲染，按有限批重置控制缓存峰值；单独持续重叠/中断/排队、三通道循环、空/非有限数字PCM夹具和五个预期非法输入。有效输入若两端共同失败仍判失败，不靠忽略声音报成功。[11命令短流程](evidence/pcm-smoke.json)为完整组子集。

C++直接使用原`Audio`控制和`render_block_locked`，关闭构造设备后显式装入真实档案并启用，阻止硬件线程抢先推进；测试时钟只替换`SDL_GetTicksNS`，没有改混音算法。数字PCM仅在测试中插入新缓存项，不作为正式声音。原实际设备、MIDI、异步档案加载和听感不在此证据范围；离线统计中的欠载/耗时零值不能当作实际无欠载。

三项定向测试及带SDK阶段Python521项通过。队列在当前整个512帧块结束后才启动下一条，声音不会在同块尾部偷偷接上；语音中断清队列。16效果上限包括循环，替换最旧效果而保留语音；短循环每次越尾都增加原完成计数。所有行为都由真实操作和原算法对照，不固定游戏结果。

当前arm64/Apple Clang14参考把混合乘加融合为F32操作，Python用同宿主标准数学库`fmaf`保持舍入；编译器/架构写入报告。其它平台若参考生成不融合乘加须复核并记录位差，不能宣称本机逐位结果通用。MIDI叠加尚未接线。

原边界也保留：循环可被16效果上限挤掉，但逻辑循环编号仍在，再请求同编号不会重新启动；原载入失败先写循环标记，随后相同请求会提前返回。输入115越界的失败/再次请求已对照，未把该失败场景计为有效声音。完整应用需在资源与异常恢复环节明确处理，不能悄悄改原控制或假装已经听到。

复现使用上述WAV公共参数，将脚本换成`differential_pcm.py`；`--smoke`只跑短流程。完整结果可重复比较采样位和状态；真实设备持续供料、MIDI/上下文恢复、捕获、听感及正式主应用仍在实施。
