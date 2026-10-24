# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_audio.cpp::capture_block_locked/write_capture；不分发录音。
# ◑ 导入
import ctypes as c
import math
import sys
import wave
from array import array
from pathlib import Path


# ◕ 功能
class 音频捕获_类:
    """
    原至多60秒预分配F32捕获，退出时转48000Hz立体声PCM16。

    更新日志：
    2026.10.24 - 设备回调只复制至固定缓冲，不写文件；保留F32乘法和远零取整。
    """

    def __init__(self, arg_路径: Path | None) -> None:
        self.路径, self.数量 = arg_路径, 0
        self._样本 = array("f", [0]) * (48000 * 2 * 60 if arg_路径 is not None else 0)

    def api_追加(self, arg_块: array) -> None:
        if self.路径 is None:
            return
        n = min(len(self._样本) - self.数量, len(arg_块))
        memoryview(self._样本)[self.数量 : self.数量 + n] = memoryview(arg_块)[:n]
        self.数量 += n

    def api_写出(self) -> None:
        if self.路径 is None:
            return
        with wave.open(str(self.路径), "wb") as output:
            output.setparams((2, 2, 48000, 0, "NONE", "not compressed"))
            for start in range(0, self.数量, 16384):
                pcm = array("h")
                for i in range(start, min(start + 16384, self.数量)):
                    value = c.c_float(min(max(self._样本[i], -1), 1) * 32767).value
                    pcm.append(int(math.copysign(math.floor(abs(value) + 0.5), value)))
                if sys.byteorder != "little":
                    pcm.byteswap()
                output.writeframesraw(pcm.tobytes())
