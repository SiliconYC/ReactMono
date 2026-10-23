# SPDX-License-Identifier: GPL-3.0-or-later
# 固定 C++ tests/flc_tests.cpp 的合成样本规则，用于验证所有已支持块类型。
# ◑ 导入
import struct

import pytest

from rich4.flc import 动画_类


# ◕ 功能
def 块(arg_类型: int, arg_体: bytes) -> bytes:
    return struct.pack("<IH", len(arg_体) + 6, arg_类型) + arg_体


def 影片() -> bytes:
    调色 = struct.pack("<H", 2) + bytes([0, 2, 255, 0, 0, 0, 255, 0, 1, 1, 8, 16, 248])
    内容 = [
        [块(4, 调色), 块(18, bytes(20)), 块(15, bytes([0, 2, 1, 254, 3, 0, 0, 4, 0]))],
        [块(7, struct.pack("<4H", 1, 65535, 0x8003, 1) + bytes([0, 255, 1, 3]))],
        [块(16, bytes([3, 3, 3, 3, 1, 1, 1, 1]))],
        [块(7, struct.pack("<HH", 1, 1) + bytes([2, 1, 0, 1]))],
        [块(13, b"")],
    ]
    头 = bytearray(128)
    struct.pack_into("<5H", 头, 4, 0xAF12, 5, 4, 2, 8)
    struct.pack_into("<I", 头, 16, 70)
    return (
        bytes(头)
        + 块(0xF100, bytes(10))
        + b"".join(块(0xF1FA, struct.pack("<H", len(帧)) + bytes(8) + b"".join(帧)) for 帧 in 内容)
    )


def test_五种块及增量帧透明和倒带() -> None:
    动画 = 动画_类(影片())
    预期 = [
        [1, 1, 3, 0, 0, 0, 0, 0],
        [1, 1, 3, 0, 1, 3, 0, 3],
        [3, 3, 3, 3, 1, 1, 1, 1],
        [3, 3, 0, 1, 1, 1, 1, 1],
        [0] * 8,
    ]
    for 状态 in 预期:
        assert 动画.api_下一帧()
        assert list(动画.像素索引) == 状态
    assert not 动画.api_下一帧()
    assert 动画.调色板[:4] == [0x7C00, 0x03E0, 0, 0x045F]
    动画.api_倒带()
    assert 动画.api_下一帧()
    assert 动画.api_图像().不透明 == bytes([1, 1, 1, 0, 0, 0, 0, 0])


def test_全部截断不越界读取() -> None:
    数据 = 影片()
    for 长度 in range(len(数据)):
        try:
            动画 = 动画_类(数据[:长度])
            while 动画.api_下一帧():
                动画.api_图像()
        except ValueError:
            continue


def test_零长度游程拒绝死循环() -> None:
    数据 = bytearray(影片()[:128])
    数据.extend(块(0xF1FA, struct.pack("<H", 1) + bytes(8) + 块(15, bytes([0, 0]))))
    with pytest.raises(ValueError, match="零长度"):
        动画_类(bytes(数据)).api_下一帧()
