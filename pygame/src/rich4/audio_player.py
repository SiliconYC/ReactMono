# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_audio.cpp的PCM载入、播放/语音/循环与主线程trace；设备与MIDI另接。
# ◑ 导入
import sys
from array import array
from collections.abc import Callable
from pathlib import Path
from threading import RLock
from time import monotonic_ns

from rich4.artwork import 美术_类
from rich4.audio_pcm import PCM混音_类
from rich4.audio_pcm_types import PCM统计_类
from rich4.audio_types import 循环通道_类
from rich4.wave_decoder import 原波形_类


# ◕ 功能
class PCM播放器_类:
    """
    真实外部WAV的原播放契约、三个独立循环和语音队列，无规则随机消费。

    更新日志：
    2026.10.24 - 解码在锁外，主线程/设备由同一锁保护混音状态，trace只在主线程送出。
    """

    def __init__(
        self,
        arg_素材: Path,
        arg_启用: bool = True,
        arg_库: Path | None = None,
        arg_时钟: Callable[[], int] = monotonic_ns,
    ) -> None:
        self.启用 = arg_启用
        self._美术, self._混音 = 美术_类(arg_素材), PCM混音_类()
        self._波形 = 原波形_类(arg_库) if arg_启用 else None
        self._锁, self._时钟 = RLock(), arg_时钟
        self._样本: dict[tuple[bool, int], array] = {}
        self._循环: list[int | None] = [None] * 3
        self._追踪: Callable[[str, str], None] | None = None
        self._上更新, self._渲染错误, self._已报错, self.诊断 = 0, "", False, ""

    def api_追踪(self, arg_追踪: Callable[[str, str], None] | None) -> None:
        self._追踪 = arg_追踪

    def _日志(self, arg_事件: str, arg_详情: str) -> None:
        if self._追踪 is not None:
            self._追踪(arg_事件, arg_详情)

    def _载入(self, arg_语音: bool, arg_编号: int) -> array:
        key = arg_语音, arg_编号
        if key not in self._样本:
            if self._波形 is None:
                raise RuntimeError("未启用的PCM播放器不能载入样本")
            # 原混音器只缓存转换后的F32，不额外永久保留每条解码WAV副本。
            data = self._美术.api_包("s" if arg_语音 else "e").api_解码(arg_编号)
            self._样本[key] = self._波形.api_解码(data)
        return self._样本[key]

    def _起音(
        self,
        arg_语音: bool,
        arg_编号: int,
        arg_留队: bool = False,
        arg_循环: bool = False,
        arg_通道: 循环通道_类 = 循环通道_类.转盘,
    ) -> None:
        if not self.启用:
            return
        pcm = self._载入(arg_语音, arg_编号)
        with self._锁:
            self._混音.api_起音(pcm, arg_语音, arg_留队, arg_循环, arg_通道)

    def api_播音(self, arg_编号: int) -> None:
        self._日志("sound", str(arg_编号))
        self._起音(False, arg_编号)

    def api_角色声音(self, arg_角色: int, arg_类别: int) -> None:
        if not 0 <= arg_角色 < 12 or not 0 <= arg_类别 < 27:
            raise ValueError("原角色语音编号越界")
        self._起音(True, 1050 + arg_角色 * 27 + arg_类别)

    def api_语音(self, arg_编号: int) -> int:
        if not self.启用:
            return 0
        self._日志("speech", str(arg_编号))
        pcm = self._载入(True, arg_编号)
        self._起音(True, arg_编号)
        return len(pcm) // 2 * 1000 // 48000

    def api_排语音(self, arg_编号: int) -> None:
        if not self.启用:
            return
        pcm = self._载入(True, arg_编号)
        with self._锁:
            now = self._混音.api_排语音(arg_编号, pcm)
        if now:
            self._日志("speech", str(arg_编号))

    def api_停语音(self) -> None:
        with self._锁:
            self._混音.api_清语音()

    def api_有语音(self) -> bool:
        with self._锁:
            return self._混音.api_有语音()

    def api_播循环(self, arg_编号: int, arg_通道: 循环通道_类 = 循环通道_类.转盘) -> None:
        if self._循环[arg_通道] == arg_编号:
            return
        self.api_停循环(arg_通道)
        self._循环[arg_通道] = arg_编号
        self._日志("loop_start", ("spinner", "walk", "bomb")[arg_通道] + " " + str(arg_编号))
        self._起音(False, arg_编号, False, True, arg_通道)

    def api_停循环(self, arg_通道: 循环通道_类 = 循环通道_类.转盘) -> None:
        index = self._循环[arg_通道]
        if index is None:
            return
        self._日志("loop_stop", ("spinner", "walk", "bomb")[arg_通道] + " " + str(index))
        self._循环[arg_通道] = None
        with self._锁:
            self._混音.api_停循环(arg_通道)

    def api_停全部循环(self) -> None:
        for c in 循环通道_类:
            self.api_停循环(c)

    def api_正在循环(self, arg_通道: 循环通道_类) -> int | None:
        return self._循环[arg_通道] if 0 <= arg_通道 < 3 else None

    def api_统计(self) -> PCM统计_类:
        with self._锁:
            return self._混音.api_统计()

    def api_渲染块(self, arg_音乐: array | None = None) -> array:
        with self._锁:
            return self._混音.api_混合(arg_音乐)

    def api_更新(self) -> None:
        if not self.启用:
            return
        now = self._时钟()
        with self._锁:
            if self._上更新:
                self._混音._统计.最长更新间隔 = max(
                    self._混音._统计.最长更新间隔,
                    ((now - self._上更新) & 0xFFFFFFFFFFFFFFFF) // 1000000,
                )
            logs = self._混音.api_取日志()
            error, self._渲染错误 = self._渲染错误, ""
        self._上更新 = now
        for event, detail in logs:
            self._日志(event, detail)
        if error and not self._已报错:
            self._已报错, self.诊断 = True, error
            print("[错误] 音频：" + error, file=sys.stderr)
