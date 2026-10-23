# SPDX-License-Identifier: GPL-3.0-or-later
# 固定 C++ terrain_tests.cpp 的 GND格式、半开边界与不透明绘制。
# ◑ 导入
import struct

import pytest

from rich4.graphics import 图像_类
from rich4.terrain import 地形_类, 地面_类


# ◕ 功能
def 合成地面() -> bytes:
    数据 = bytearray(2580)
    struct.pack_into("<4sHHII", 数据, 0, b"GND\0", 2, 1, 2, 0x12345678)
    struct.pack_into("<HH", 数据, 18, 0x1234, 0x4321)
    struct.pack_into("<HH", 数据, 528, 1, 0)
    数据[532:1556] = bytes([1]) * 1024
    数据[1556:] = bytes([2]) * 1024
    return bytes(数据)


def test_地面调色板索引瓦片及总览布局() -> None:
    数据 = 合成地面()
    地 = 地面_类.api_解码(数据)
    assert (地.宽瓦片, 地.高瓦片, 地.api_瓦片数(), 地.保留) == (2, 1, 2, 0x12345678)
    assert 地.索引 == [1, 0] and 地.api_瓦片(0)[1023] == 1
    总览 = 地.api_总览()
    assert (总览.宽, 总览.高) == (64, 32)
    assert 总览.像素 == ([0x4321] * 32 + [0x1234] * 32) * 32
    with pytest.raises(IndexError):
        地.api_瓦片(2)
    with pytest.raises(ValueError):
        地.api_总览(2047)


@pytest.mark.parametrize("arg_长度", [0, 15, 527, 531, 2579])
def test_截断地面拒绝(arg_长度: int) -> None:
    with pytest.raises(ValueError):
        地面_类.api_解码(合成地面()[:arg_长度])


def test_地面签名空尺寸过量瓦片和坏索引拒绝() -> None:
    for 偏移, 格式, 值 in [(3, "B", 1), (4, "H", 0), (8, "I", 0xFFFFFFFF), (528, "H", 2)]:
        数据 = bytearray(合成地面())
        struct.pack_into("<" + 格式, 数据, 偏移, 值)
        with pytest.raises(ValueError):
            地面_类.api_解码(bytes(数据))


def test_零索引仍不透明半开矩形和掩码() -> None:
    图 = 图像_类(8, 8, [0x7BDE] * 64, 不透明=bytes(64))
    调色 = [0x1234] + [0] * 255
    角 = ((2, 2), (2, 6), (6, 6), (6, 2))
    地形_类.api_绘瓦片(图, bytes(1024), 调色, 角, (0, 0, 8, 8))
    for y in range(8):
        for x in range(8):
            内 = 2 <= x < 6 and 2 <= y < 6
            assert 图.像素[y * 8 + x] == (0x1234 if 内 else 0x7BDE)
            assert 图.不透明[y * 8 + x] == int(内)


def test_裁剪空框退化和错误画布拒绝() -> None:
    图 = 图像_类(8, 8, [0x7BDE] * 64)
    调色 = [0x1234] + [0] * 255
    角 = ((2, 2), (2, 6), (6, 6), (6, 2))
    地形_类.api_绘瓦片(图, bytes(1024), 调色, 角, (3, 3, 5, 5))
    assert 图.像素.count(0x1234) == 4
    原 = 图.像素.copy()
    地形_类.api_绘瓦片(图, bytes(1024), 调色, 角, (3, 3, 3, 5))
    地形_类.api_绘瓦片(图, bytes(1024), 调色, ((0, 0),) * 4, (0, 0, 8, 8))
    assert 图.像素 == 原
    with pytest.raises(ValueError):
        地形_类.api_绘瓦片(
            图, bytes(1024), 调色, ((-32768, 0), (0, 2), (2, 2), (2, 0)), (0, 0, 8, 8)
        )
    图.像素.pop()
    with pytest.raises(ValueError):
        地形_类.api_绘瓦片(图, bytes(1024), 调色, 角, (0, 0, 8, 8))
