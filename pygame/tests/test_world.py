# ◑ 导入
import struct

import pytest
from test_save import 合成存档

from rich4.save import 存档_类
from rich4.world import 世界_类


# ◕ 功能
def test_所有世界已解读字段与未知原字节无损往返() -> None:
    数据 = 合成存档() + b"\x80\xfftrailer"
    世界 = 世界_类.api_从存档(存档_类.api_解码(数据))
    assert len(世界.玩家) == 4
    assert [len(t) for t in (世界.节点, 世界.地产, 世界.设施, 世界.公司, 世界.景物)] == [
        8,
        4,
        2,
        3,
        5,
    ]
    assert 世界.玩家[0].状态.初始现金比例 == 数据[0x10 + 25]
    assert 世界.玩家[2].持仓[5].数量 == struct.unpack_from("<i", 数据, 0x21F6 + 2 * 96 + 5 * 8)[0]
    assert 世界.股票[3].浮点位 == list(struct.unpack_from("<5I", 数据, 0x2376 + 3 * 36 + 12))
    assert 世界.api_导出() == 数据


def test_世界变更只回填对应字段() -> None:
    数据 = 合成存档()
    世界 = 世界_类.api_从存档(存档_类.api_解码(数据))
    期望 = bytearray(数据)
    世界.玩家[0].记录.银行 = -123
    struct.pack_into("<i", 期望, 0x10 + 32, -123)
    世界.玩家[1].状态.附身炸弹 = 3
    期望[0x10 + 104 + 64] = 3
    世界.股票[2].浮点位[3] = 0x7FC01234
    struct.pack_into("<I", 期望, 0x2376 + 2 * 36 + 24, 0x7FC01234)
    世界.节点[1].x = -32768
    偏移 = 世界.地图摘要.表[0].偏移 + 0x274B + 40
    struct.pack_into("<h", 期望, 偏移, -32768)
    assert 世界.api_导出() == 期望


def test_破产只清记录28到103而不清库存与控制字节() -> None:
    数据 = 合成存档()
    世界 = 世界_类.api_从存档(存档_类.api_解码(数据))
    世界.api_清破产字段(2)
    期望 = bytearray(数据)
    期望[0x10 + 2 * 104 + 28 : 0x10 + 3 * 104] = bytes(76)
    assert 世界.api_导出() == 期望
    assert 世界.玩家[2].记录.卡片 == list(range(1, 16))
    assert 世界.玩家[2].状态.初始现金比例 == 数据[0x10 + 2 * 104 + 25]


def test_拒绝修改表规模和记录编号() -> None:
    世界 = 世界_类.api_从存档(存档_类.api_解码(合成存档()))
    世界.节点[1].编号 = 9
    with pytest.raises(ValueError):
        世界.api_导出()


def 合成地图() -> bytes:
    计数 = [4, 1, 0, 1, 0]
    步长 = [40, 52, 56, 52, 28]
    数据 = bytearray(40 + sum((n + 1) * s for n, s in zip(计数, 步长)))
    偏移 = 40
    for i, (n, s) in enumerate(zip(计数, 步长)):
        struct.pack_into("<II", 数据, i * 8, n, 偏移)
        偏移 += (n + 1) * s
    for i, (x, y, a, b) in enumerate(
        [(32, 32, 2, 4), (64, 32, 1, 3), (64, 64, 2, 4), (32, 64, 3, 1)], 1
    ):
        struct.pack_into("<hh", 数据, 40 + i * 40, x, y)
        struct.pack_into("<4H", 数据, 40 + i * 40 + 24, a, b, 0, 0)
    return bytes(数据)


def test_新局资料交通库存显式起点与延迟出生() -> None:
    from rich4.world_options import 新局设置_类, 新玩家_类

    世界 = 世界_类.api_从地图(
        合成地图(), 新局设置_类(玩家=[新玩家_类(10, 1), 新玩家_类(3, 2, 0, 1)])
    )
    assert 世界.头.人类人数 == 1
    assert (世界.玩家[0].记录.现金, 世界.玩家[0].记录.银行, 世界.玩家[0].记录.节点) == (
        100000,
        100000,
        0,
    )
    AI = 世界.玩家[1].记录
    assert (AI.现金, AI.银行, AI.节点, AI.上次节点, AI.方向) == (120000, 80000, 1, 2, 6)
    assert AI.道具 == [1, 1, 1, 1, 0, 0, 0, 1, 1, 0, 0, 0, 0, 0, 0]
    assert 世界.道具供应 == [8, 8, 8, 8, 10, 10, 10, 8]
    assert 世界.节点[1].标志 == 0x200
    assert sorted(世界.新闻牌堆) == list(range(36))
    assert sorted(世界.命运牌堆) == list(range(37))
    assert 世界.有初始随机状态
    assert 世界_类.api_从存档(存档_类.api_解码(世界.api_导出())).api_导出() == 世界.api_导出()


def test_新局拒绝无路出生与越界链接() -> None:
    数据 = bytearray(合成地图())
    for i in range(1, 5):
        struct.pack_into("<4H", 数据, 40 + i * 40 + 24, 0, 0, 0, 0)
    with pytest.raises(ValueError, match="可出生"):
        世界_类.api_从地图(bytes(数据))
    数据 = bytearray(合成地图())
    struct.pack_into("<H", 数据, 40 + 40 + 24, 900)
    with pytest.raises(ValueError, match="链接"):
        世界_类.api_从地图(bytes(数据))


def test_破产字段赋值保留状态对象和嵌入敌意数组引用() -> None:
    世 = 世界_类.api_从地图(合成地图())
    状 = 世.玩家[0].状态
    敌意 = 状.敌意
    状.累计支出, 状.敌意[:], 状.初始现金比例 = 123, [1, 2, 3, 4], 73
    世.api_清破产字段(0)
    assert 世.玩家[0].状态 is 状 and 状.敌意 is 敌意
    assert 状.累计支出 == 0 and 敌意 == [0] * 4 and 状.初始现金比例 == 73


def test_世界值赋保持旧世界参数引用并独立于快照() -> None:
    from copy import deepcopy

    from rich4.random import 随机数_类
    from rich4.tools import 道具_类, 道具回调_类

    世 = 世界_类.api_从地图(合成地图())
    世.玩家[0].记录.道具[9] = 1
    快照 = deepcopy(世)
    快照.头.当前玩家 = 1
    快照.玩家[0].记录.道具[9], 快照.玩家[1].记录.道具[9] = 8, 2

    def 恢复() -> bool:
        世.api_覆盖(快照)
        return True

    果 = 道具_类.api_使用(世, 随机数_类(1), 0, 10, 0, 0, 道具回调_类(恢复上次=恢复))
    assert 果.已应用 and 世.头.当前玩家 == 1
    assert 世.玩家[0].记录.道具[9] == 8 and 世.玩家[1].记录.道具[9] == 1
    assert 快照.玩家[1].记录.道具[9] == 2
