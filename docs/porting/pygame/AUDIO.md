# 主游戏音频增量

最新增量：回调统计开销优化、完整PCM数值复验、dummy软件时钟的错误判据及保留失败性能指标，见 [时钟与性能记录](AUDIO_DUMMY_CLOCK.md)。本轮不重新开启桌面采集或真实游戏窗口。

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

## 原MIDI与PCM合流（2026-10-24，#156）

`fluid_synth.py`142行、`midi_player.py`192行、`audio.py`93行，共427行；三个定向测试，带全部显式外部SDK/MIDI/音库时阶段524项通过。使用标准FluidSynth公开C接口软件合成，不建立FluidSynth音频设备，不调用C++参考引擎。原48000Hz、增益0.28、采样时钟、关闭混响/合唱、八首歌单、十八上下文编号与栈保留；全部MIDI启动时预读，回调不读MIDI文件，不消耗规则随机数。

[完整实际原MIDI/PCM对照](evidence/midi-differential.json)1190命令、200695808个F32采样逐位一致。比较公开控制、曲目/上下文/栈/tick/播放器状态、过期与恢复标记、所有原MIDI缓存内容摘要、全部13个统计、限幅内部状态和trace；包含十八上下文的嵌套压栈/替换/弹出、静音开关/暂停、静音中切曲、清空栈、全禁用、缺银行以及唯一预期非法曲目9。真实语音/排队/三个循环叠加与MIDI共混；有效输入共同失败不能计通过。

八首歌单全部自然播完并前进，十七个有声上下文全部检测到真实tick回绕，原播放器按无限循环继续；没有强制DONE、跳到结尾或固定结果。共离线合成100347904帧，约34分50.6秒；这是软件音频时间，不是实际设备连续运行或完整游戏长局。[12命令短流程](evidence/midi-smoke.json)是完整组子集。

### 恢复tick的参考缺陷

最初定向测试要求恢复后不早于保存tick，实际失败：保存442，恢复并渲染四块后只有13。直接原C++控制复现同一结果；固定FluidSynth2.6.1的`fluid_player_seek`在先`play`而新MIDI尚未加载时检查`total_ticks=0`，拒绝大于0的位置，原调用忽略返回。Python保持同一调用顺序和忽略行为，测试与报告明确保存442→实际13，禁止将它说成已经成功断点恢复。后续若修复需单独记录相对参考差异；此处未擅自改规则/音频行为。

正常静音不销毁当前播放器，停止合成即暂停采样时钟；静音中换曲会设置过期标记，开启时才重建并尝试恢复。静音上下文与没有上下文分别对应无声屏幕/正常歌单，不能混用。缺银行保留原诊断且PCM仍可播放；缺歌单是错误，缺可选上下文按原诊断并使对应屏幕静音。

本机外部系统DLS仅只读，摘要写入报告，绝不复制/分发。FluidSynth先尝试SF2读取此DLS时会输出`Not a SoundFont file`，随后原生DLS加载实际成功，两端有同样消息；对照只允许这条已核实诊断，其它标准错误立即失败。首次测试工具猜错限幅字段而失败，改用已存在`_包络/api_增益`后重跑，无运行代码改动。真实音库加载、非零MIDI和全部自然循环都明确验证，不以静音通过冒充声音。

完整对照仍是同arm64/Clang14、固定SDL3/FluidSynth/同音库的离线范围；换库/音库/平台必须重跑，不声称与1998官方合成音色逐位相同。实际Pygame设备持续供料、异步MKF、捕获、正式主游戏/小游戏接线和听感仍待验。

复现沿用WAV的`PKG_CONFIG_PATH`、`--source/--build/--assets/--report`，脚本为`differential_midi.py`，另传`--bank /path/to/GeneralMIDI.sf2`、`--sdl-library .../libSDL3.dylib`和`--fluid-library .../libfluidsynth.dylib`。定向测试需显式设置`RICH4_TEST_ASSETS`、`RICH4_FLUIDSYNTH_LIBRARY`、`RICH4_SOUNDFONT`；缺任一则真实MIDI测试明确跳过。

## Pygame真实设备、异步档案与捕获（2026-10-24，#156）

新增`audio_archives.py`43行、`audio_capture.py`44行、`audio_feed.py`72行、`audio_device.py`68行、`device_audio.py`88行，共315行，另优化PCM的标准FMA调用。后台自有线程一次开Effect/Speaking，两者成功才发布；首次声音在锁外等待/解码，失败保留并重复报告。回调只消费已解码样本、合成MIDI和积存日志，主线程送trace；关闭先停设备，再写捕获/等待资源/释放合成器，正式应用最终负责`pygame.quit()`。

Pygame SDL2回调是填满固定缓冲，参考SDL3则可把整块余量排入流。`audio_feed.py`始终按512帧渲染并保留余量，定向验证不整块请求不丢/重复采样、不提前续接语音。`api_排队字节()`只报告Python余量，未把SDL2驱动内部待播量当作原SDL3流的queued计数。移动平台背景/前台事件将由应用调用暂停接口，尚未验。

[实际dummy流程](evidence/audio-dummy.json)593回调/303616帧，[本机CoreAudio](evidence/audio-coreaudio.json)726回调/371712帧，均真实48000Hz/立体声F32/512帧，原音效/语音排队/人物语音/步行炸弹循环/音乐上下文/静音切曲/16效果压力、捕获与正常退出通过。后台档案加载成功，音效19次/语音3次且非零采样明确验证。CoreAudio主线程睡眠一秒推进48640帧、忙算一秒推进47616帧；均为短流程自动设备操作，没有声称人工听感或图形游戏长局。

CoreAudio压力仍有1次11.717毫秒回调超过10.667毫秒预算，累计超出按原整数口径1毫秒，`real_time_budget_pass:false`保留；前次同流程有5次/18毫秒。dummy本次零超预算，但它主线程忙算一秒仅推进24576帧：SDL2 dummy的调度与实际设备不同，也不能从统计零推出没有停顿。回调计时起于Python入口，不能直接测到拿GIL之前的等待；真实帧/墙钟与后续完整游戏仍须共同审查，未宣称无欠载。

### 真实回调失败与GIL死锁

[失败与修复记录](evidence/audio-device-failures.json)保留两种实际失败。Pygame传入Cython`_memoryviewslice`，它没有标准`memoryview.cast`，先取`memoryview(buffer)`才可处理。另一处CoreAudio在暂停/退出附近挂住：本机原生线程采样显示主线程`AudioDevice.pause→SDL_PauseAudioDevice→SDL_LockMutex`持GIL等设备，设备`recording_cb→PyGILState_Ensure→take_gil`等GIL。Pygame2.6.1[固定源码](https://raw.githubusercontent.com/pygame/pygame/2.6.1/src_c/cython/pygame/_sdl2/audio.pyx)与实测一致。

修复只调用同一Pygame SDL2库的公开暂停接口，`ctypes.CDLL`释放GIL等待回调结束，随后Pygame自身`close()`清理其deviceid，避免外部关闭后重复析构。没有调用参考引擎，也没有把设备关掉冒充持续音频。旧挂起探针在保留栈后仅终止自有PID；修复后的实际CoreAudio正常退出。此同库符号解析已验macOS；Windows DLL解析和其它系统仍需补验，不能外推。

回调异常不能穿过C边界，故记录原因并清未填缓冲，下一次主线程检查必重新抛出进入恢复；不会把异常后的静音计为成功声音。完整应用的恢复落盘仍待接线。七个资源/捕获/余量测试加一个真实外部SDK子进程回调测试，本阶段共532项通过；无外部SDK/MIDI/音库时真实项明确跳过。

### 捕获位精度与性能回归

[原捕获文件对照](evidence/capture-differential.json)五组、5960047个输入F32，含空、奇数尾、取整边界、随机范围和超过60秒；实际原`capture_block_locked/write_capture`与Python全部WAV字节一致。60秒预分配上限5760000采样，回调不扩容、不写文件；退出F32钳制/乘32767后远零取整，与Python银行家取整不同。合成数值只验文件格式，实际声音捕获留忽略目录，全部媒体不入Git。

标准`fmaf`保留GIL并缓存函数引用，避免每个采样跨线程切换；[可重放16真实效果基准](evidence/audio-ffi-performance.json)32块输出摘要相同，CDLL中位8.518毫秒/PyDLL7.917毫秒；不是完整窗口FPS。优化后重新跑[完整PCM](evidence/pcm-device-regression.json)3881命令/4400128采样与[完整MIDI](evidence/midi-device-regression.json)1190命令/200695808采样，输入/状态/波形摘要均与原报告相同，八曲/十七上下文自然进展仍通过。导入Pygame后显式库版本也核验为FluidSynth2.6.1，不误用其打包的其它FluidSynth。

```sh
RICH4_SDL3_LIBRARY="$PWD/.research-cache/audio-runtime/lib/libSDL3.dylib" \
RICH4_FLUIDSYNTH_LIBRARY="$PWD/.research-cache/audio-runtime/lib/libfluidsynth.dylib" \
uv run --project pygame python pygame/tools/probe_game_audio.py \
  --assets /path/to/Rich4 --driver coreaudio --output .research-cache/audio-device
```

上例CoreAudio仅macOS，`--driver dummy`为静音设备流程；另以`benchmark_audio.py --assets ... --report ...`复现FMA性能，`differential_capture.py`沿用WAV的源码/构建/SDK参数。正式主程序/小游戏接线、移动生命周期、长期图形对局、人工听感仍待验，不把本节短设备流程当最终完整音频验收。

## 正式游戏人工听感与默认输出修复（2026-10-24）

首次用户在真实桌面试玩两三分钟：操作与画面正常，但完全静音；耳机在启动后插入，浏览器音频正常。应用日志同时有17720320渲染帧/33845264非零采样，故不能继续把混音计数冒充可听。启动时旧绑定的实际设备名未记录，不能声称已从日志直接证明旧路由。

源码核查发现Python固定打开枚举首项，参考`native_audio.cpp:235`打开默认播放设备。Pygame2.6.1 [绑定源码](https://raw.githubusercontent.com/pygame/pygame/2.6.1/src_c/cython/pygame/_sdl2/audio.pyx)虽在文档允许`None`，实际强制字符串。SDL2 [固定CoreAudio源码](https://raw.githubusercontent.com/libsdl-org/SDL/release-2.28.4/src/audio/coreaudio/SDL_coreaudio.m)仅为默认句柄注册默认输出变化监听；将当前默认名查询后再次按名称打开，也不能保留热插拔跟随语义。

`audio_device.py/audio_sdl.py`直接调用Pygame同一SDL2的公开`SDL_OpenAudioDevice(NULL)`，保持F32/48000Hz/双声道/512帧及原供料器；Python回调引用保留至暂停/关闭完成，`CDLL`暂停与关闭释放GIL。没有调用C++参考引擎，没有改混音、MIDI或规则。`--audio-device`/`RICH4_AUDIO_DEVICE`仅在明确要求固定输出时传名称；无效设备报错，不静默换到其它输出。

默认/明确名称/无效设备三项真实SDL子进程测试先RED再GREEN；另验真实回调错误仍经主线程抛出并可关闭。用户先听到实际CoreAudio探针的原BGM/语音；随后完整游戏加载上一轮自然AUTO，用户明确确认“**三类声音正常，拔插后也正常**”。三类是BGM、点击音效、角色语音。观测器只记录原生输入，不投递事件。证据及运行文件哈希见 [人工反馈](evidence/application-human-audio.json)。

这是有限桌面流程/热插拔的人类听感通过；不等于全部曲目/角色/小游戏/长局都逐一人工听验。压力回调仍有超预算，旧阶段统计继续保留，不能由听到声音推导零欠载。macOS已验，其它平台的同库符号与设备行为仍未验。商业声音、捕获、应用包及字体全部未上传。

本次默认输出阶段完整600项Python测试通过，无跳过；Ruff、152文件wheel及源包商业素材/二进制隔离检查通过。作者自审，未派发其它Agent。
