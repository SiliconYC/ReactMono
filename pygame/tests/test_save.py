# SPDX-License-Identifier: GPL-3.0-or-later
# 合成布局依据固定 C++ tests/save_tests.cpp；不包含商业存档字节。
# ◑ 导入
import struct

import pytest

from rich4.save import 存档_类


# ◕ 功能
def 合成存档(arg_人数: int = 4) -> bytes:
    计数 = (7, 3, 1, 2, 4)
    步长 = (40, 52, 56, 52, 28)
    地图长 = 40 + sum((n + 1) * s for n, s in zip(计数, 步长))
    大小 = 0x274B + 地图长 + arg_人数 * (0x2718 + 地图长)
    数据 = bytearray((i * 73 + i // 7 + 19) & 255 for i in range(大小))
    struct.pack_into("<I2BH2HI", 数据, 0, 0x26, 29, 2, 2000, 2, 1, arg_人数)
    for 偏移, 值 in [
        (0x1B0, 1),
        (0x2676, arg_人数 - 1),
        (0x268A, 200000),
        (0x268E, 3),
        (0x2747, 地图长),
    ]:
        struct.pack_into("<I", 数据, 偏移, 值)
    偏移 = 40
    for i, (n, s) in enumerate(zip(计数, 步长)):
        struct.pack_into("<II", 数据, 0x274B + i * 8, n, 偏移)
        偏移 += (n + 1) * s
    for i in range(arg_人数):
        起点 = 0x10 + i * 104
        struct.pack_into(
            "<II4H6B",
            数据,
            起点,
            0xFFFFFFFF,
            0x1234567 + i,
            320 + i,
            240 + i,
            5 + i,
            4 + i,
            1,
            2,
            3,
            7 + i,
            1,
            5 if i == 0 else 2,
        )
        struct.pack_into("<4i", 数据, 起点 + 28, -7, 100000 + i, 12345 + i, 6789 + i)
        struct.pack_into("<H", 数据, 起点 + 48, 90 + i)
        数据[0x654 + i * 15 : 0x654 + (i + 1) * 15] = bytes(range(1, 16))
        数据[0x690 + i * 15 : 0x690 + (i + 1) * 15] = bytes(range(0, 30, 2))
    return bytes(数据)


def test_存档解码有符号字段未知区域和尾字节不丢失() -> None:
    数据 = 合成存档() + b"\x00\xfe\x12\xff"
    存档 = 存档_类.api_解码(数据)
    头 = 存档.api_头()
    assert (头.日期, 头.地图, 头.阶段, 头.人数, 头.人类人数, 头.当前玩家, 头.初始资金, 头.物价) == (
        (29, 2, 2000),
        2,
        1,
        4,
        1,
        3,
        200000,
        3,
    )
    玩家 = 存档.api_玩家(3)
    assert (玩家.槽位, 玩家.现金, 玩家.银行, 玩家.角色, 玩家.节点, 玩家.上次节点) == (
        3,
        -7,
        100003,
        10,
        8,
        7,
    )
    assert 玩家.卡片 == list(range(1, 16))
    assert 玩家.道具 == list(range(0, 30, 2))
    assert 存档.api_地图摘要().字节数 == 976
    assert [t.数量 for t in 存档.api_地图摘要().表] == [7, 3, 1, 2, 4]
    assert 存档.api_导出() == 数据
    区域 = 存档.api_区域()
    assert 区域[-1].名称 == "raw_reserved_trailing_bytes"
    assert 区域[0].偏移 == 0
    assert all(a.偏移 + a.长度 == b.偏移 for a, b in zip(区域, 区域[1:]))
    assert 区域[-1].偏移 + 区域[-1].长度 == len(数据)


@pytest.mark.parametrize("arg_值", [0, -1, 123456789, -2147483648, 2147483647])
def test_只改指定四字节而不更新历史快照(arg_值: int) -> None:
    数据 = 合成存档()
    存档 = 存档_类.api_解码(数据)
    期望 = bytearray(数据)
    存档.api_设现金(2, arg_值)
    struct.pack_into("<i", 期望, 0x10 + 2 * 104 + 28, arg_值)
    assert 存档.api_导出() == 期望
    存档.api_设银行(2, arg_值)
    struct.pack_into("<i", 期望, 0x10 + 2 * 104 + 32, arg_值)
    assert 存档.api_导出() == 期望
    assert 存档_类.api_解码(存档.api_导出()).api_玩家(2).银行 == arg_值


def test_拒绝截断重叠越界且失败写入无副作用() -> None:
    数据 = 合成存档(1)
    for 大小 in [0, 4, 15, 0x274A, 0x274B, len(数据) - 1]:
        with pytest.raises(ValueError):
            存档_类.api_解码(数据[:大小])
    for 偏移, 值 in [
        (0, 0x27),
        (12, 0),
        (12, 5),
        (0x1B0, 2),
        (0x2676, 1),
        (0x2747, 0xFFFFFFFF),
        (0x274B, 0xFFFFFFFF),
        (0x274F, 39),
        (0x2757, 40),
    ]:
        损坏 = bytearray(数据)
        struct.pack_into("<I", 损坏, 偏移, 值)
        with pytest.raises(ValueError):
            存档_类.api_解码(bytes(损坏))
    存档 = 存档_类.api_解码(数据)
    for 槽位 in [-1, 1, 4, 2**64]:
        with pytest.raises(IndexError):
            存档.api_设现金(槽位, 0)
        assert 存档.api_导出() == 数据
