# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from array import array

import pytest

from rich4.audio_pcm import PCM混音_类
from rich4.audio_types import 循环通道_类


# ◕ 功能
def test_语音排队等整块结束才启动下一条中断会清空旧队列() -> None:
    s = PCM混音_类()
    s.api_起音(array("f", [1, 1]), True)
    assert not s.api_排语音(2, array("f", [0.25, 0.25]))
    assert not s.api_排语音(3, array("f", [0.5, 0.5]))
    first = s.api_混合()
    assert list(first[:2]) == pytest.approx([0.6, 0.6]) and not any(first[2:])
    assert s._片段[0].位置 == 0 and len(s._语音队列) == 1
    assert s.api_取日志() == [("speech", "2")]
    second = s.api_混合()
    assert list(second[:2]) == pytest.approx([0.15, 0.15])
    s.api_起音(array("f", [0.75, 0.75]), True)
    assert s._语音队列 == [] and s.api_有语音()
    assert list(s.api_混合()[:2]) == pytest.approx([0.45, 0.45])


def test_十六效果上限包含循环且替换最旧者不影响独立语音() -> None:
    s = PCM混音_类()
    oldest = array("f", [0.1, 0.1])
    s.api_起音(oldest, False, arg_循环=True, arg_通道=循环通道_类.步行)
    s.api_起音(array("f", [0, 0]), True)
    for _ in range(16):
        s.api_起音(array("f", [0.01] * 2048), False)
    assert len(s._片段) == 17 and not any(p.样本 is oldest for p in s._片段)
    assert s._统计.效果启动 == 17 and s._统计.语音启动 == 1
    assert s.api_混合()[0] == pytest.approx(0.096)
    assert len(s._片段) == 16 and not s.api_有语音()


def test_短循环每次跨尾均计完成且停止只清指定循环通道() -> None:
    s = PCM混音_类()
    s.api_起音(array("f", [0.1, 0.1]), False, arg_循环=True, arg_通道=循环通道_类.步行)
    s.api_混合()
    assert s._统计.片段完成 == 512 and s._片段[0].位置 == 0
    s.api_起音(array("f", [0.1, 0.1]), False, arg_循环=True, arg_通道=循环通道_类.炸弹)
    s.api_停循环(循环通道_类.步行)
    assert len(s._片段) == 1 and s._片段[0].通道 == 循环通道_类.炸弹
    s.api_起音(array("f"), True)
    s.api_混合()
    assert s._统计.片段完成 == 1025 and not s.api_有语音()
