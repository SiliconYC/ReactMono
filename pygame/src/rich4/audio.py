# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_audio.cpp；纯Python PCM混音与标准FluidSynth共用原音频状态锁。
# ◑ 导入
from array import array
from collections.abc import Callable
from pathlib import Path
from time import monotonic_ns

from rich4.audio_player import PCM播放器_类
from rich4.audio_types import 音乐_类
from rich4.midi_player import MIDI播放器_类


# ◕ 功能
class 音频_类(PCM播放器_类):
    """
    原游戏音频控制与MIDI/PCM合流；设备宿主另接，同一锁只保护播放状态。

    更新日志：
    2026.10.24 - 缺银行不阻止PCM；原音乐自然切换日志先于同块语音排队日志。
    """

    def __init__(
        self,
        arg_素材: Path,
        arg_启用: bool = True,
        arg_音库: Path | None = None,
        arg_SDL库: Path | None = None,
        arg_Fluid库: Path | None = None,
        arg_时钟: Callable[[], int] = monotonic_ns,
    ) -> None:
        super().__init__(arg_素材, arg_启用, arg_SDL库, arg_时钟)
        self._音乐 = MIDI播放器_类(arg_素材, arg_音库, arg_Fluid库, arg_启用)
        if arg_启用:
            self.诊断 = self._音乐.诊断
        else:
            self._音乐.诊断 = ""
        self._音乐.api_追踪(self._日志)

    def api_推音乐(self, arg_音乐: 音乐_类) -> None:
        with self._锁:
            self._音乐.api_推音乐(arg_音乐)

    def api_换音乐(self, arg_音乐: 音乐_类) -> None:
        with self._锁:
            self._音乐.api_换音乐(arg_音乐)

    def api_弹音乐(self) -> None:
        with self._锁:
            self._音乐.api_弹音乐()

    def api_选音乐(self, arg_曲目: int) -> None:
        with self._锁:
            self._音乐.api_选音乐(arg_曲目)

    def api_音乐开关(self, arg_开关: bool) -> None:
        with self._锁:
            self._音乐.api_音乐开关(arg_开关)

    def api_音乐可用(self) -> bool:
        return self._音乐.可用

    def api_音乐启用(self) -> bool:
        return self._音乐.开关

    def api_音乐深度(self) -> int:
        return len(self._音乐._栈)

    def api_音乐上下文(self) -> 音乐_类 | None:
        return self._音乐.上下文

    def api_音乐曲目(self) -> int:
        with self._锁:
            return self._音乐.曲目

    def api_音乐名称(self) -> str:
        with self._锁:
            return self._音乐.api_文件()

    def api_渲染块(self, arg_音乐: array | None = None) -> array:
        if arg_音乐 is not None:
            raise ValueError("游戏音频只允许实际MIDI产生背景采样")
        with self._锁:
            music = self._音乐.api_渲染块()
            self._混音._待日志.extend(self._音乐._待日志)
            self._音乐._待日志.clear()
            if self._音乐._渲染错误:
                self._渲染错误, self._音乐._渲染错误 = self._音乐._渲染错误, ""
            return self._混音.api_混合(music)

    def api_关闭(self) -> None:
        with self._锁:
            self._音乐.api_关闭()
