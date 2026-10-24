# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import struct
from copy import deepcopy

from test_game import 会话样本
from test_original_text import _程序

from rich4.cards import 卡片目标_类, 目标种类_类
from rich4.game_types import (
    公告种类_类,
    决策_类,
    决策种类_类,
    决策选项_类,
    游戏事件_类,
    游戏事件种类_类,
)
from rich4.message_rules import 消息规则_类
from rich4.original_text import 原版文字_类, 原版程序_类


# ◕ 功能
def test_原简易格式仅替换小写字符串及整数标签并按顺序消费() -> None:
    assert 消息规则_类.api_格式("%s:%d/%s/%%/%x", ["A", -7]) == "A:-7//%%/%x"


def test_确认判定保留卡片两选项特例与地产零一值判定() -> None:
    决 = 决策_类(决策种类_类.卡片目标, 0, 选项=[决策选项_类("A", 23), 决策选项_类("B", -1)])
    assert 消息规则_类.api_是确认(决)
    决.种类 = 决策种类_类.购地
    assert not 消息规则_类.api_是确认(决)
    决.选项[0].值, 决.选项[1].值 = 0, 1
    assert 消息规则_类.api_是确认(决)
    决.种类 = 决策种类_类.银行
    assert not 消息规则_类.api_是确认(决)


def test_目标名字使用实际世界和库存而不修改决策或规则世界() -> None:
    世 = 会话样本().世界
    原 = 世.api_导出()
    assert 消息规则_类.api_人名(世, -1) == ""
    assert 消息规则_类.api_地名(世, 2001) == 世.地产[1].经济.街道名.decode("cp950").replace(" ", "")
    决 = 决策_类(
        决策种类_类.提示, 0, 选项=[决策选项_类("原标签", 3, 对象=卡片目标_类(目标种类_类.角色, 0))]
    )
    原决 = deepcopy(决)
    # 此路径不读取原文；股票/公告文字由真实外部PE的差分另外验收。
    规 = 消息规则_类(原版文字_类(原版程序_类(_程序(b"\0"))))
    显 = 规.api_本地化(决, 世)
    assert 显.选项[0].标签 == 消息规则_类.api_人名(世, 0)
    assert 决 == 原决 and 世.api_导出() == 原


def test_加油公告使用真实费用表索引二而非修车索引三() -> None:
    数据 = bytearray(0x80000)

    def 写(arg_地址: int, arg_内容: bytes) -> None:
        偏 = arg_地址 - 0x401000
        数据[偏 : 偏 + len(arg_内容)] = arg_内容

    写(0x47517C, struct.pack("<4I", 0x401010, 0x401020, 0x401030, 0x401040))
    for i in range(4):
        写(0x401010 + i * 16, f"F{i}\0".encode())
    写(0x4639B3, b"%s|%s|%d|%s\0")
    规 = 消息规则_类(原版文字_类(原版程序_类(_程序(bytes(数据)))))
    e = 游戏事件_类(
        游戏事件种类_类.已付租, 0, 金额=123, 公告=公告种类_类.租金, 公告号=3, 地产=4001, 主体=0
    )
    assert 规.api_从事件(e, 会话样本().世界).文字.endswith("|123|F2")


def test_免费卡原文从格式串起点读取而不把前面的浮点数据当文字() -> None:
    数据 = bytearray(0x70000)
    偏 = 0x465384 - 0x401000
    数据[偏 : 偏 + 4] = b"\x99\x99\xc9\x3f"
    格式 = b"FREE %s\0"
    数据[偏 + 4 : 偏 + 4 + len(格式)] = 格式
    规 = 消息规则_类(原版文字_类(原版程序_类(_程序(bytes(数据)))))
    决 = 决策_类(决策种类_类.卡片目标, 0, 选项=[决策选项_类("A", 1), 决策选项_类("B", 0)])
    世 = 会话样本().世界
    assert 规.api_确认问题(决, 世) == "FREE " + 规.api_人名(世, 0)
