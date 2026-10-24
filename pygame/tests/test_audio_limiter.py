# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import math
from array import array

from rich4.audio_limiter import 限幅器_类


# ◕ 功能
def test_阈值内样本逐位不变且非有限输入归零奇数尾项按原不处理() -> None:
    s = 限幅器_类(48000)
    quiet = array("f", [0.0, -0.0, 0.8, -0.7])
    original = quiet.tobytes()
    assert s.api_处理(quiet) == 0 and quiet.tobytes() == original
    bad = array("f", [float("nan"), float("inf"), float("-inf")])
    assert s.api_处理(bad) == 0 and bad[:2] == array("f", [0, 0])
    assert math.isinf(bad[-1])


def test_立体声共用峰值立即限制且静音期间指数释放而非硬截断() -> None:
    s = 限幅器_类(48000)
    loud = array("f", [2, 1, 0.5, -0.25])
    assert s.api_处理(loud) == 4
    assert loud[0] == s.api_上限() and loud[1] == s.api_上限() / 2
    assert loud[2] < 0.5 and loud[3] > -0.25
    before = s.api_增益()
    silence = array("f", [0] * 1024)
    assert s.api_处理(silence) == 1024 and before < s.api_增益() < 1
