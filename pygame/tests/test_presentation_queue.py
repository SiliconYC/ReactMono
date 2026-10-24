# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_game import 会话样本

from rich4.game_types import (
    效果_类,
    效果种类_类,
    月报_类,
    游戏事件_类,
    游戏事件种类_类,
    转盘状态_类,
)
from rich4.presentation_queue import 呈现宿主_类, 呈现队列_类


# ◕ 功能
def _样本() -> tuple[呈现队列_类, list, list[bool]]:
    调, 忙 = [], [False]
    宿 = 呈现宿主_类(
        lambda: 忙[0],
        lambda e: 调.append(("observe", int(e.种类))),
        lambda e: 调.append(("event", int(e.种类))),
        lambda e: 调.append(("spinner", int(e.种类))),
        lambda e: 调.append(("monthly", int(e.种类))),
        lambda es, owner: 调.extend(("movie", int(e.种类)) for e in es),
    )
    return 呈现队列_类(宿), 调, 忙


def test_效果按原after_events头部顺序交错且入队按值复制() -> None:
    q, _, _ = _样本()
    es = [效果_类(效果种类_类.爆炸, 事件位=i) for i in (0, 2, 1)]
    events = [游戏事件_类(k, 0) for k in (游戏事件种类_类.回合开始, 游戏事件种类_类.已移动)]
    q.api_入队(es, events)
    es[0].物件种类 = 99
    assert [
        ("E" if x.事件 else "F", int(x.事件.种类 if x.事件 else x.效果.种类)) for x in q.步骤
    ] == [("F", 6), ("E", 0), ("E", 2), ("F", 6), ("F", 6)]
    assert q.步骤[0].效果.物件种类 == 0


def test_暂停按80毫秒计且忙碌或队列非空不能推进核心() -> None:
    q, 调, 忙 = _样本()
    会 = 会话样本()
    q.api_入队([效果_类(效果种类_类.暂停, 物件种类=5)], [游戏事件_类(游戏事件种类_类.已移动, 0)])
    q.api_泵(会)
    assert q.等待毫秒 == 400 and not q.api_可推进()
    q.api_消费等待(399)
    q.api_泵(会)
    assert not any(x[0] == "event" for x in 调)
    q.api_消费等待(1)
    q.api_泵(会)
    assert q.api_可推进()
    忙[0] = True
    assert not q.api_可推进()


def test_专属转盘月报必须带数据才路由且破产标志与显示回合保持() -> None:
    q, 调, _ = _样本()
    es = [
        效果_类(效果种类_类.金额转盘),
        效果_类(效果种类_类.金额转盘, 转盘=转盘状态_类()),
        效果_类(效果种类_类.月报, 月报=月报_类()),
        效果_类(效果种类_类.破产),
    ]
    q.api_入队(es, [游戏事件_类(游戏事件种类_类.回合开始, 0)])
    q.api_泵(会话样本())
    assert [x for x in 调 if x[0] != "observe"] == [
        ("movie", 12),
        ("spinner", 12),
        ("monthly", 16),
        ("movie", 11),
        ("event", 0),
    ]
    assert q.破产音乐 and q.呈现玩家 == 0


def test_仅托管开发重放且关闭效果时略过暂停() -> None:
    for 托管, 效果, 预期 in ((False, False, 160), (True, True, 160), (True, False, 0)):
        q, _, _ = _样本()
        q.api_入队([效果_类(效果种类_类.暂停, 物件种类=2)], [])
        q.api_泵(会话样本(), 托管, 效果)
        assert q.等待毫秒 == 预期


def test_真实会话按效果先事件后提取且观察末尾立即泵队列() -> None:
    q, 调, _ = _样本()
    会 = 会话样本()
    随, 原 = 会.随机.状态, 会.世界.api_导出()
    q.api_观察会话(会)
    assert 调 and not 会.事件队列 and not 会.效果队列
    assert q.api_可推进() and 会.随机.状态 == 随 and 会.世界.api_导出() == 原
