# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import io
import os
import struct
import wave
from pathlib import Path

import pytest

from rich4.wave_decoder import 原波形_类


# ◕ 功能
@pytest.fixture
def 波形() -> 原波形_类:
    路 = os.environ.get("RICH4_SDL3_LIBRARY")
    if 路 is None:
        pytest.skip("需要外部SDL3库，设置RICH4_SDL3_LIBRARY运行真实解码测试")
    return 原波形_类(Path(路))


def test_真实SDL3把单声道十六位复制为四十八千赫双声道F32(波形: 原波形_类) -> None:
    output = io.BytesIO()
    with wave.open(output, "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(48000)
        writer.writeframes(struct.pack("<4h", 0, 16384, -16384, 32767))
    samples = 波形.api_解码(output.getvalue())
    assert list(samples) == [0, 0, 0.5, 0.5, -0.5, -0.5, 32767 / 32768, 32767 / 32768]


def test_坏WAV拒绝并保留可定位错误不返回假静音(波形: 原波形_类) -> None:
    with pytest.raises(ValueError, match="原WAV解码失败"):
        波形.api_解码(b"not a WAV")
