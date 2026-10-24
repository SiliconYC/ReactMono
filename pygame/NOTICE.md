# 来源与许可边界

本子项目为非官方、独立 Python 移植，与大宇资讯及其他商业权利人无授权或从属关系。

## 程序代码

`pygame/` 内自有引擎、工具和测试采用 `GPL-3.0-or-later`，全文见 [LICENSE](LICENSE)。依固定上游 [lhr0909/richman4-remastered](https://github.com/lhr0909/richman4-remastered/tree/3f4209a7dfb5b2f20799bf54e6c03c5faa11c557) 翻译；格式与算法知识继承 `mytbk/rich4@ec7d70e693059d1e781d9d1cc2ad7f36d360d39e`，包括 Copyright © 2018 Iru Cai 等人的工作。每个派生模块标注具体来源，函数映射和规则依据在 [移植文档](../docs/porting/pygame/README.md)。参考的公开源文件没有复制进运行时；测试端适配器只链接用户本机固定 C++ 核心。

本子项目的许可声明只覆盖 `pygame/` 内本次产生的程序，不重授或更改既有 React 项目的代码、资源或许可。两个项目独立构建、独立运行，不共享实现模块。

## 商业内容

《大富翁4》名称、角色、地图、美术、音效、语音、音乐、字体、台词和原版程序的版权与商标属于大宇资讯及各自权利人。GPL 代码许可不授予这些内容的任何权利。执行需使用用户自己合法持有的游戏数据，通过外部目录只读加载；本仓库不提供、下载或分发这些素材。MKF、EXE、DAT、音视频、原字体及解码/截图产物不进入版本控制，也不得打包为可公开下载的含素材应用。后续如转录商业原文，须在对应文件另标权属，不能仅以 GPL 头声称取得其权利。

## 依赖

Pygame 2.6.1 的许可为 LGPL，底层 SDL 及其他随包依赖以其发行许可证为准。字体渲染通过`ctypes`调用宿主或Pygame随附FreeType的公开C接口，FreeType适用其FTL/GPL许可；字体文件另受各自许可约束，须由用户外部提供。运行时不链接 C++ 参考引擎。pytest、Ruff、tree-sitter、CMake 和 C++ 编译器仅作开发与测试；具体锁定版本见 `pyproject.toml` 与 `uv.lock`。

音频WAV转换通过`ctypes`使用标准SDL3公开C接口，SDL3适用 [Zlib许可证](https://github.com/libsdl-org/SDL/blob/829a65d769d935c4852f8159e964312c0957260a/LICENSE.txt)。后续软件MIDI依赖FluidSynth，其源码声明 [LGPL-2.1-or-later](https://github.com/FluidSynth/fluidsynth/blob/71e85b2ca6bf48641ba7e2261d8f2640ae473773/src/synth/fluid_synth.c)，许可全文见其 [LICENSE](https://github.com/FluidSynth/fluidsynth/blob/71e85b2ca6bf48641ba7e2261d8f2640ae473773/LICENSE)。构建工具将SDK及传递依赖放本机忽略缓存，不将其二进制、源码或音库装入Python发行包；各依赖保留其原许可，商业SF2/DLS/MIDI/WAV另受各自权利约束。
