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

正式Python混音器、原WAV解码/重采样、语音队列、MIDI播放/恢复、后台设备供料与应用接线仍未实现。参考使用SDL3重采样，Pygame绑定SDL2；后续必须实际比较波形并记录差别，不能因同为SDL就宣称相同。CoreAudio系统`gs_instruments.dls`在本机存在，FluidSynth/SDL3开发库当前未安装；尚未构成完整MIDI播放链。外部音库、WAV、MIDI与捕获始终不入Git。

最终还需真实效果/语音重叠、循环/上下文切换、小游戏交接、长局时音频持续性、波形/时钟、听感和正式窗口验收。当前设备零样本、策略记录、数值限幅均不满足这些交付条件。
