# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_audio.cpp::feed；适配Pygame的原生F32填充回调。
# ◑ 导入
from _thread import RLock
from array import array
from collections.abc import Callable
from time import monotonic_ns

from rich4.audio_capture import 音频捕获_类
from rich4.audio_pcm_types import PCM统计_类


# ◕ 功能
class 设备供料_类:
    """
    始终整512帧渲染，原块剩余采样保留到下次设备请求。

    更新日志：
    2026.10.24 - 原SDL3把余量排入流，Pygame SDL2固定填充接口由Python显式保留。
    """

    def __init__(
        self,
        arg_渲染: Callable[[], array],
        arg_统计: PCM统计_类,
        arg_锁: RLock,
        arg_捕获: 音频捕获_类,
        arg_时钟: Callable[[], int] = monotonic_ns,
    ) -> None:
        self._渲染, self._统计, self._锁 = arg_渲染, arg_统计, arg_锁
        self._捕获, self._时钟 = arg_捕获, arg_时钟
        self._块 = array("f")
        self._位置 = 0
        self.回调次数 = 0

    @property
    def 余量(self) -> int:
        return len(self._块) * 4 - self._位置

    def api_填充(self, arg_缓冲: memoryview) -> None:
        target = arg_缓冲.cast("B")
        if len(target) % 8:
            raise ValueError("音频设备请求必须按立体声F32帧对齐")
        if not target:
            return
        begin = self._时钟()
        with self._锁:
            written, produced = 0, 0
            while written < len(target):
                if not self.余量:
                    block = self._渲染()
                    if block.typecode != "f" or len(block) != 1024:
                        raise ValueError("音频渲染未返回原512帧立体声F32块")
                    self._块, self._位置 = block, 0
                    self._捕获.api_追加(block)
                    produced += 512
                n = min(self.余量, len(target) - written)
                target[written : written + n] = memoryview(self._块).cast("B")[
                    self._位置 : self._位置 + n
                ]
                self._位置 += n
                written += n
            spent = self._时钟() - begin
            s = self._统计
            s.最长渲染微秒 = max(s.最长渲染微秒, spent // 1000)
            # 仅消耗已有余量时相当于原SDL流直接交付，不再重复混音预算。
            if produced:
                budget = produced * 1000000000 // 48000
                if spent > budget:
                    s.超时次数 += 1
                    s.饥饿毫秒 += (spent - budget) // 1000000
            self.回调次数 += 1
