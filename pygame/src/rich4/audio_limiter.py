# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/audio_limiter.hpp；IEEE单精度处理，不调用参考引擎。
# ◑ 导入
import ctypes as c
import ctypes.util
import math
import sys
from array import array


# ◕ 功能
class 限幅器_类:
    """
    原立体声共峰值、立即攻击、指数释放与最终单精度安全钳制。

    更新日志：
    2026.10.24 - 同宿主libm的expf保持参考单精度参数语义；不是音频播放后端。
    """

    _数学 = c.CDLL("msvcrt" if sys.platform == "win32" else ctypes.util.find_library("m"))
    _指数 = _数学.expf
    _指数.argtypes, _指数.restype = [c.c_float], c.c_float
    _单 = c.c_float

    def __init__(
        self, arg_采样率: float, arg_上限: float = 0.891251, arg_释放毫秒: float = 150.0
    ) -> None:
        f = self._单
        self._上限, self._包络 = f(arg_上限).value, 0.0
        denominator = f(f(f(arg_释放毫秒).value * f(0.001).value).value * f(arg_采样率).value).value
        self._释放 = self._指数(self._除(-1.0, denominator))

    @classmethod
    def _除(cls, arg_分子: float, arg_分母: float) -> float:
        if arg_分母 != 0:
            return cls._单(arg_分子 / arg_分母).value
        if arg_分子 == 0 or math.isnan(arg_分子):
            return float("nan")
        return math.copysign(
            float("inf"), math.copysign(1.0, arg_分子) * math.copysign(1.0, arg_分母)
        )

    def api_上限(self) -> float:
        return self._上限

    def api_增益(self) -> float:
        return self._除(self._上限, self._包络) if self._包络 > self._上限 else 1.0

    def api_处理(self, arg_交错: array) -> int:
        if arg_交错.typecode != "f":
            raise ValueError("原限幅器输入必须为单精度数组")
        limited, f, ceiling, release, envelope = 0, self._单, self._上限, self._释放, self._包络
        for i in range(0, len(arg_交错) - 1, 2):
            left, right = arg_交错[i], arg_交错[i + 1]
            if not math.isfinite(left):
                left = 0.0
            if not math.isfinite(right):
                right = 0.0
            envelope = max(max(abs(left), abs(right)), f(envelope * release).value)
            if envelope > ceiling:
                gain = self._除(ceiling, envelope)
                left = min(max(f(left * gain).value, -ceiling), ceiling)
                right = min(max(f(right * gain).value, -ceiling), ceiling)
                limited += 2
            arg_交错[i], arg_交错[i + 1] = left, right
        self._包络 = envelope
        return limited
