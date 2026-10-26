# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from copy import deepcopy
from pathlib import Path

import pytest
from test_game import 会话样本
from test_original_text import _程序

from rich4.artwork import 美术_类
from rich4.game_types import 游戏事件_类, 游戏事件种类_类
from rich4.graphics import 图像_类
from rich4.loan_notice import 贷款提醒_类
from rich4.message_overlay import 消息声音_类, 消息层_类, 消息种类_类
from rich4.message_rules import 消息规则_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.original_text import 原版文字_类, 原版程序_类


# ◕ 功能
@pytest.mark.parametrize("arg_天数", [15, 7, 3, 2, 1])
@pytest.mark.parametrize("arg_状态", ["医院天数", "监狱天数", "消失天数", "酒店天数"])
def test_贷款预警实际转换为需确认消息且不因缺席漏掉(
    arg_天数: int,
    arg_状态: str,
) -> None:
    会 = 会话样本()
    世 = 会.世界
    世.头.日期 = (1, 1, 2000)
    人 = 世.玩家[0]
    人.记录.贷款, 人.记录.现金, 人.记录.银行 = 50000, 1000, 2000
    人.状态.贷款到期 = (2000 << 16) | (1 << 8) | (arg_天数 + 1)
    setattr(人.状态, arg_状态, 5)
    类 = 游戏事件种类_类.回合开始 if arg_天数 > 3 else 游戏事件种类_类.提示
    事 = 游戏事件_类(类, 0, 消息=f"贷款将在{arg_天数}天后到期")
    原 = 世.api_导出(), 会.随机.状态, deepcopy(事)
    规 = 消息规则_类(原版文字_类(原版程序_类(_程序(b"\0"))))
    显 = 规.api_从事件(事, 世)
    assert 显 is not None
    assert 显.种类 == 消息种类_类.对话框 and 显.需确认
    assert "50,000" in 显.文字 and f"{arg_天数} 天" in 显.文字
    assert "3,000" in 显.文字 and "2000/01/" in 显.文字
    assert ("破产风险" in 显.文字) == (arg_天数 <= 7)
    if arg_天数 <= 7:
        assert "47,000" in 显.文字
    assert (世.api_导出(), 会.随机.状态, 事) == 原


def test_已还清的旧到期日不会产生空贷款提醒() -> None:
    会 = 会话样本()
    会.世界.头.日期 = (1, 1, 2000)
    会.世界.玩家[0].记录.贷款 = 0
    会.世界.玩家[0].状态.贷款到期 = 0x07D00102
    规 = 消息规则_类(原版文字_类(原版程序_类(_程序(b"\0"))))
    assert 规.api_从事件(
        游戏事件_类(游戏事件种类_类.提示, 0, 消息="贷款将在1天后到期"), 会.世界
    ) is None


def test_到期收款消息显示已结算金额而非已清零贷款() -> None:
    会 = 会话样本()
    会.世界.头.日期 = (1, 1, 2000)
    人 = 会.世界.玩家[0]
    人.记录.贷款, 人.记录.现金, 人.记录.银行 = 50000, 30000, 30000
    人.状态.贷款到期 = 0x07D00101
    会._收到期贷款()
    事 = next(e for e in 会.api_取事件() if e.消息 == "贷款到期，银行收回贷款")
    规 = 消息规则_类(原版文字_类(原版程序_类(_程序(b"\0"))))
    显 = 规.api_从事件(事, 会.世界)
    assert 显 is not None and 显.需确认
    assert "50,000" in 显.文字 and "10,000" in 显.文字
    assert 人.记录.贷款 == 人.状态.贷款到期 == 0


@pytest.mark.parametrize("arg_控制", [2, 6])
@pytest.mark.parametrize("arg_资金", [30000, 1000])
def test_电脑到期收款或破产都不要求真人确认(arg_控制: int, arg_资金: int) -> None:
    会 = 会话样本()
    会.世界.头.日期 = (1, 1, 2000)
    人 = 会.世界.玩家[0]
    人.记录.控制标志, 人.记录.贷款 = arg_控制, 50000
    人.记录.现金 = 人.记录.银行 = arg_资金
    人.状态.贷款到期 = 0x07D00101
    会._收到期贷款()
    事 = next(e for e in 会.api_取事件() if e.消息 == "贷款到期，银行收回贷款")
    规 = 消息规则_类(原版文字_类(原版程序_类(_程序(b"\0"))))
    assert 规.api_从事件(事, 会.世界) is None


def test_记住会话人类归属以在破产控制归零后仍报告结算() -> None:
    会 = 会话样本()
    会.世界.头.日期 = (1, 1, 2000)
    人 = 会.世界.玩家[0]
    人.记录.贷款, 人.记录.现金, 人.记录.银行 = 50000, 1000, 2000
    人.状态.贷款到期 = 0x07D00101
    规 = 消息规则_类(原版文字_类(原版程序_类(_程序(b"\0"))))
    规.api_重置贷款提醒(会.世界)
    会._收到期贷款()
    assert 人.记录.控制标志 == 0
    事 = next(e for e in 会.api_取事件() if e.消息 == "贷款到期，银行收回贷款")
    显 = 规.api_从事件(事, 会.世界)
    assert 显 is not None and 显.需确认 and "资金不足，已破产" in 显.文字


def test_贷款提醒不会自动消失且确认后才放行() -> None:
    from rich4.message_overlay import 消息_类

    时 = [0]
    层 = 消息层_类(消息声音_类(), lambda: 时[0])
    项 = 消息_类(消息种类_类.对话框, 文字="贷款提醒", 需确认=True)
    层.api_入队(项)
    层._开始(0)
    时[0] = 60000
    层.api_退休()
    assert 层.api_活跃()
    层.api_跳过()
    assert not 层.api_活跃()
    层.api_即时(True)
    层.api_入队(项)
    层._开始(60000)
    层.api_退休()
    assert not 层.api_活跃()


@pytest.mark.parametrize("arg_控制", [0, 2, 6])
def test_电脑与已出局贷款不打断人类(arg_控制: int) -> None:
    世 = 会话样本().世界
    世.头.日期 = (1, 1, 2000)
    人 = 世.玩家[0]
    人.记录.控制标志, 人.记录.贷款 = arg_控制, 1000
    人.状态.贷款到期 = 0x07D00108
    assert 贷款提醒_类.api_读取(世, 0) is None
    assert 贷款提醒_类.api_从事件(游戏事件_类(游戏事件种类_类.回合开始, 0), 世) is None


@pytest.mark.parametrize("arg_现金,arg_存款", [(30000, 20000), (60000, 0), (0, 50001)])
def test_现金存款合计足够就不误报破产(arg_现金: int, arg_存款: int) -> None:
    世 = 会话样本().世界
    世.头.日期 = (1, 1, 2000)
    人 = 世.玩家[0]
    人.记录.控制标志 = 5
    人.记录.贷款, 人.记录.现金, 人.记录.银行 = 50000, arg_现金, arg_存款
    人.状态.贷款到期 = 0x07D00102
    项 = 贷款提醒_类.api_读取(世, 0)
    assert 项 is not None and 项.api_缺口() == 0 and not 项.api_风险()


@pytest.mark.parametrize(
    "arg_日期,arg_到期,arg_天数",
    [((25, 12, 1999), 0x07D00101, 7), ((27, 2, 2000), 0x07D00301, 3)],
)
def test_贷款显示保留原跨年闰日历(
    arg_日期: tuple[int, int, int],
    arg_到期: int,
    arg_天数: int,
) -> None:
    世 = 会话样本().世界
    世.头.日期 = arg_日期
    世.玩家[0].记录.贷款 = 1000
    世.玩家[0].状态.贷款到期 = arg_到期
    assert 贷款提醒_类.api_读取(世, 0).剩余 == arg_天数


def test_异常日期与旧过期存档只展示而不修改() -> None:
    世 = 会话样本().世界
    世.头.日期 = (5, 1, 2000)
    人 = 世.玩家[0]
    人.记录.贷款 = 1000
    人.状态.贷款到期 = 0x07D00D01
    原 = 世.api_导出()
    项 = 贷款提醒_类.api_读取(世, 0)
    assert 项.api_天数() == "到期日异常" and not 项.api_风险()
    assert 世.api_导出() == 原
    人.状态.贷款到期 = 0x07D00101
    assert 贷款提醒_类.api_读取(世, 0).api_天数() == "已过期 4 天"


@pytest.mark.parametrize("arg_天数", [16, 14, 8, 6, 4])
def test_回合开始不会重复三天预警或每天额外弹窗(arg_天数: int) -> None:
    世 = 会话样本().世界
    世.头.日期 = (1, 1, 2000)
    世.玩家[0].记录.贷款 = 1000
    世.玩家[0].状态.贷款到期 = (2000 << 16) | (1 << 8) | (arg_天数 + 1)
    assert 贷款提醒_类.api_从事件(游戏事件_类(游戏事件种类_类.回合开始, 0), 世) is None


def test_读档当天三天提醒不漏报且同回合原预警不重复() -> None:
    世 = 会话样本().世界
    世.头.日期 = (1, 1, 2000)
    世.玩家[0].记录.贷款 = 50000
    世.玩家[0].状态.贷款到期 = 0x07D00104
    规 = 消息规则_类(原版文字_类(原版程序_类(_程序(b"\0"))))
    回合 = 游戏事件_类(游戏事件种类_类.回合开始, 0)
    预警 = 游戏事件_类(游戏事件种类_类.提示, 0, 消息="贷款将在3天后到期")
    assert 规.api_从事件(回合, 世) is not None
    assert 规.api_从事件(预警, 世) is None
    规.api_重置贷款提醒()
    assert 规.api_从事件(预警, 世) is not None
    assert 规.api_从事件(回合, 世) is None


def test_常驻显示所有人类贷款并在还清后消失且绘制不修改规则(字体: 字体_类) -> None:
    会 = 会话样本()
    世 = 会.世界
    世.头.日期 = (1, 1, 2000)
    for 槽, 人 in enumerate(世.玩家):
        人.记录.控制标志 = 5 if 槽 < 2 else 2
        人.记录.贷款, 人.记录.现金, 人.记录.银行 = 50000, 1000, 2000
        人.状态.贷款到期 = 0x07D00108
    世.头.当前玩家 = 2
    图 = 图像_类(640, 480, [0] * 307200)
    框 = 画框_类(图, 美术_类(Path("unused")), 字体, [])
    原 = 世.api_导出(), 会.随机.状态
    贷款提醒_类.api_绘常驻(框, 世)
    assert any(图.像素[46 * 640:90 * 640])
    assert any(图.像素[93 * 640:137 * 640])
    assert not any(图.像素[140 * 640:])
    assert (世.api_导出(), 会.随机.状态) == 原
    for 人 in 世.玩家:
        人.记录.贷款 = 0
    图.像素[:] = [0] * 307200
    贷款提醒_类.api_绘常驻(框, 世)
    assert not any(图.像素)
