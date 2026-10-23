# ◑ 导入
import struct

import pytest

from rich4.economy import 地产经济_类, 经济_类
from rich4.inventory import 库存_类


# ◕ 功能
def test_满手丢首张最低价且供应量按字节回绕() -> None:
    库存 = 库存_类()
    库存.卡片[:] = [1, 2, 3] * 5
    库存.卡价[:] = [8, 1, 1] + [5] * 27
    库存.卡供应[1] = 255
    库存.api_收卡(4)
    assert 库存.卡片 == [1, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 1, 2, 3, 4]
    assert 库存.卡供应[1] == 0
    assert 库存.卡供应[3] == 255


def test_丢半手每次读取移动后当前槽位() -> None:
    库存 = 库存_类()
    库存.卡片[:4] = [1, 2, 3, 4]
    assert 库存.api_丢半手()
    assert 库存.卡片 == [2, 4] + [0] * 13
    assert 库存.卡供应[:4] == [1, 0, 1, 0]
    assert 库存.api_有卡(0)


def test_不密集手牌拒绝修改() -> None:
    库存 = 库存_类()
    库存.卡片[:3] = [1, 0, 2]
    with pytest.raises(ValueError):
        库存.api_丢半手()
    assert 库存.卡片[:3] == [1, 0, 2]


def test_道具供应限制容量与保留槽位() -> None:
    库存 = 库存_类()
    assert not 库存.api_收道具(1)
    库存.道具供应[0] = 1
    assert 库存.api_收道具(1)
    assert 库存.道具供应[0] == 0
    assert 库存.api_用道具(1)
    assert 库存.道具供应[0] == 1
    库存.道具[8] = 9
    assert not 库存.api_收道具(9)
    库存.道具[14] = 77
    库存.道具[8] = 2
    库存.道具价格[8] = 5
    assert 库存.api_卖库存道具() == 10
    assert 库存.道具[14] == 77


def test_卖卡返回点数并归还供应() -> None:
    库存 = 库存_类()
    库存.卡片[:3] = [1, 2, 1]
    库存.卡价[:2] = [4, 6]
    assert 库存.api_卖卡() == 14
    assert 库存.卡片 == [0] * 15
    assert 库存.卡供应[:2] == [2, 1]


def test_地产租金按原字节街名和当前等级汇总() -> None:
    地 = [
        地产经济_类(b"road\0suffix", 0, 1, 2, (1, 2, 3, 4, 5, 6)),
        地产经济_类(b"road", 0, 1, 5, (10, 20, 30, 40, 50, 60)),
        地产经济_类(b"road", 1, 1, 99, (0,) * 6),
        地产经济_类(b"road", 0, 2, 99, (0,) * 6),
    ]
    assert 经济_类.api_通行费(地, 1, 2, b"road") == 126
    assert 经济_类.api_通行费(地, 1, -1) == -2000
    assert 经济_类.api_连锁数(地, 1) == 1
    assert 经济_类.api_通行费(地, 1, 0x7FFFFFFF) == -2000
    assert 经济_类.api_通行费(地, 1, 1, b"") == 0


def test_地产记录严格52字节与NUL名字() -> None:
    数据 = bytearray(52)
    数据[4:8] = b"road"
    数据[0x18:0x1B] = bytes([1, 2, 3])
    struct.pack_into("<6H", 数据, 0x20, 1, 2, 3, 4, 5, 6)
    地 = 地产经济_类.api_解码(bytes(数据))
    assert (地.街道名, 地.连锁, 地.业主, 地.等级, 地.各级租金) == (
        b"road",
        1,
        2,
        3,
        (1, 2, 3, 4, 5, 6),
    )
    数据[4:20] = b"x" * 16
    with pytest.raises(ValueError):
        地产经济_类.api_解码(bytes(数据))
