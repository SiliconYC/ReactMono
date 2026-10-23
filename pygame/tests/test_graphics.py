# ◑ 导入
import struct

import pytest

from rich4.graphics import 图像_类


# ◕ 功能
def test_索引零透明与调色板黑色独立() -> None:
    调色板 = struct.pack("<256H", 0x7C00, 0, *([0] * 254))
    数据 = b"SPR\x00" + struct.pack("<IIhhhhI", 1, 24, 2, 1, -2, 3, 2) + 调色板 + b"\x00\x01"
    图 = 图像_类.api_解码(数据, 0)
    assert (图.原点x, 图.原点y) == (-2, 3)
    assert 图.像素 == [0x7C00, 0]
    assert 图.不透明 == b"\x00\x01"
    assert 图.api_RGBA() == bytes([255, 0, 0, 0, 0, 0, 0, 255])


def test_绿色转换保持原第六位为零() -> None:
    图 = 图像_类(1, 1, [0x03E0])
    assert 图.api_RGBA() == bytes([0, 250, 0, 0xFF])


def test_原点裁剪与黑色掩码绘制() -> None:
    目标 = 图像_类(3, 2, [1] * 6)
    源 = 图像_类(2, 1, [0, 3], 1, 0, b"\x01\x00")
    目标.api_绘制(源, 1, 1)
    assert 目标.像素 == [1, 1, 1, 0, 1, 1]


def test_自拷贝不污染后续源像素() -> None:
    图 = 图像_类(3, 1, [1, 2, 3])
    图.api_绘制(图, 1, 0)
    assert 图.像素 == [1, 1, 2]


def test_拒绝图像表与负尺寸() -> None:
    with pytest.raises(ValueError):
        图像_类.api_解码(b"SMP\x00" + struct.pack("<II", 1, 12), 0)
    with pytest.raises(ValueError):
        图像_类(-1, 2, [])
