# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_audio.cpp::start_clip_locked/render_block_locked，独立Python混音。
# ◑ 导入
import ctypes as c
import ctypes.util
import sys
from array import array
from dataclasses import replace

from rich4.audio_limiter import 限幅器_类
from rich4.audio_pcm_types import PCM片段_类, PCM统计_类
from rich4.audio_types import 循环通道_类


# ◕ 功能
class PCM混音_类:
    """
    原512帧F32混音、16效果上限、单语音/排队与限幅。

    更新日志：
    2026.10.24 - 宿主必须用同一锁保护主线程与设备回调；样本缓存不得边播边修改。
    """

    # fmaf不调用Python；保留GIL避免每个采样跨线程让出导致回调超预算。
    _数学 = c.PyDLL("msvcrt" if sys.platform == "win32" else ctypes.util.find_library("m"))
    _融合 = _数学.fmaf
    _融合.argtypes, _融合.restype = [c.c_float, c.c_float, c.c_float], c.c_float

    def __init__(self) -> None:
        self._片段: list[PCM片段_类] = []
        self._语音队列: list[tuple[int, array]] = []
        self._待日志: list[tuple[str, str]] = []
        self._统计, self._限幅 = PCM统计_类(), 限幅器_类(48000)

    def api_起音(
        self,
        arg_样本: array,
        arg_语音: bool,
        arg_留队: bool = False,
        arg_循环: bool = False,
        arg_通道: 循环通道_类 = 循环通道_类.转盘,
    ) -> None:
        if arg_样本.typecode != "f":
            raise ValueError("原混音片段必须为F32")
        if arg_语音:
            if not arg_留队:
                self._语音队列.clear()
            self._片段[:] = [p for p in self._片段 if not p.语音]
            self._统计.语音启动 += 1
        else:
            self._统计.效果启动 += 1
        if not arg_语音 and sum(not p.语音 for p in self._片段) >= 16:
            del self._片段[next(i for i, p in enumerate(self._片段) if not p.语音)]
        self._片段.append(PCM片段_类(arg_样本, 0, arg_语音, arg_循环, arg_通道))

    def api_排语音(self, arg_编号: int, arg_样本: array) -> bool:
        if arg_样本.typecode != "f":
            raise ValueError("原排队语音必须为F32")
        if not self._语音队列 and not self.api_有语音():
            self.api_起音(arg_样本, True, True)
            return True
        self._语音队列.append((arg_编号, arg_样本))
        return False

    def api_清语音(self) -> None:
        self._语音队列.clear()
        self._片段[:] = [p for p in self._片段 if not p.语音]

    def api_有语音(self) -> bool:
        return any(p.语音 for p in self._片段)

    def api_停循环(self, arg_通道: 循环通道_类) -> None:
        self._片段[:] = [p for p in self._片段 if not (p.循环 and p.通道 == arg_通道)]

    def api_取日志(self) -> list[tuple[str, str]]:
        logs, self._待日志 = self._待日志, []
        return logs

    def api_统计(self) -> PCM统计_类:
        return replace(self._统计)

    def api_混合(self, arg_音乐: array | None = None) -> array:
        if arg_音乐 is not None and arg_音乐.typecode != "f":
            raise ValueError("原背景音乐混音必须为F32")
        output = array("f", [0]) * 1024 if arg_音乐 is None else array("f", arg_音乐)
        if len(output) != 1024:
            raise ValueError("原混音器每次必须处理512个立体声帧")
        if arg_音乐 is not None:
            self._统计.音乐帧 += 512
        fused = self._融合
        for clip in self._片段:
            written = 0
            while True:
                available = len(clip.样本) - clip.位置
                count = min(1024 - written, available)
                for i in range(count):
                    output[written + i] = fused(clip.样本[clip.位置 + i], 0.6, output[written + i])
                clip.位置 += count
                written += count
                if clip.位置 == len(clip.样本):
                    self._统计.片段完成 += 1
                    if clip.循环 and clip.样本:
                        clip.位置 = 0
                if not (clip.循环 and clip.样本 and written < 1024):
                    break
        self._片段[:] = [p for p in self._片段 if p.位置 != len(p.样本)]
        if self._语音队列 and not self.api_有语音():
            index, pcm = self._语音队列.pop(0)
            self._待日志.append(("speech", str(index)))
            self.api_起音(pcm, True, True)
        for sample in output:
            magnitude = abs(sample)
            self._统计.峰值 = max(self._统计.峰值, magnitude)
            if magnitude > 1:
                self._统计.削波采样 += 1
        self._统计.限幅采样 += self._限幅.api_处理(output)
        self._统计.非零采样 += sum(abs(s) > 0.000001 for s in output)
        self._统计.渲染帧 += 512
        return output
