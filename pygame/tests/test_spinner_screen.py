# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from copy import deepcopy

from test_original_text import _程序

from rich4.game_types import 效果_类, 效果种类_类, 转盘状态_类
from rich4.original_text import 原版文字_类, 原版程序_类
from rich4.spinner_screen import _转播_类, 转盘声音_类, 转盘屏幕_类


# ◕ 功能
def _屏(arg_调用: list) -> 转盘屏幕_类:
    return 转盘屏幕_类(
        转盘声音_类(
            lambda n: arg_调用.append(("play", n)),
            lambda n: arg_调用.append(("loop", n)),
            lambda: arg_调用.append(("stop", 0)),
        ),
        原版文字_类(原版程序_类(_程序(b"\0"))),
    )


def test_金额按原三四数位判定且半数字取整() -> None:
    s = 转盘状态_类(类型=1, 数位=[18, 19, 17, 15])
    assert 转盘屏幕_类.api_金额(s) == 987
    s.类型 = 2
    assert 转盘屏幕_类.api_金额(s) == 9987
    s.类型 = 5
    assert 转盘屏幕_类.api_金额(s) == 987


def test_按值入队只按原spinner存在判断且跳过不追溯清已有队列() -> None:
    屏 = _屏([])
    e = 效果_类(效果种类_类.轮盘, 转盘=转盘状态_类(类型=2))
    屏.api_入队(e)
    e.转盘.类型 = 3
    assert 屏._队列[0].转盘.类型 == 2
    屏.api_跳过(True)
    屏.api_入队(e)
    屏.api_入队(效果_类(效果种类_类.轮盘))
    assert len(屏._队列) == 1 and 屏.api_活跃()


def test_循环音效仅在变更时替换且清空依原延至收帧停止() -> None:
    调 = []
    屏 = _屏(调)
    屏._待循环 = 51
    屏.api_收帧()
    屏._待循环 = 51
    屏.api_收帧()
    屏._待循环 = 52
    屏.api_收帧()
    assert 调 == [("loop", 51), ("loop", 52)]
    屏._决策阶段 = 7
    屏.api_清空()
    assert 屏._正在循环 == 52 and 屏._决策阶段 == 7
    屏.api_收帧()
    assert 调[-1] == ("stop", 0) and 屏._正在循环 == 0


def test_电脑轮盘第40帧射箭并逐级减速停在非空格后保留40帧() -> None:
    调 = []
    屏 = _屏(调)
    e = 效果_类(效果种类_类.轮盘, 转盘=转盘状态_类(类型=1, 游标=0))
    p = _转播_类(e, deepcopy(e.转盘))
    for _ in range(39):
        assert 屏._步轮(p)
    assert p.轮状态 == 1 and p.帧数 == 39 and not 调
    assert 屏._步轮(p) and p.轮状态 == 3 and 调 == [("play", 1)]
    for _ in range(100):
        assert 屏._步轮(p)
        if p.轮状态 == 5:
            break
    else:
        raise AssertionError("原轮盘没有停止")
    assert 屏.轮值[1][p.状态.游标] >= 0 and p.帧数 == 0
    for _ in range(39):
        assert 屏._步轮(p)
    assert not 屏._步轮(p)


def test_人类已停止轮盘可点击结束结果而清空不重置播放策略() -> None:
    屏 = _屏([])
    e = 效果_类(效果种类_类.轮盘, 转盘=转盘状态_类(类型=0, 阶段=2))
    p = _转播_类(e, deepcopy(e.转盘), 轮状态=5, 跳过=True)
    assert not 屏._步轮(p)
    屏.api_跳过(True)
    屏.api_清空()
    assert 屏._跳过
