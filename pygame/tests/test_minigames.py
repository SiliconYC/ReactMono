# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from collections import Counter

import pytest

from rich4.minigames import 企鹅_类, 图框_类, 天降_类, 小游戏种类_类, 小游戏阶段_类, 气球_类
from rich4.random import 随机数_类


# ◕ 功能
def 开始(arg_游戏) -> None:
    for _ in range(10):
        arg_游戏.api_帧()
    assert arg_游戏.阶段 == 小游戏阶段_类.准备
    前 = arg_游戏.剩余帧
    arg_游戏.api_帧()
    assert arg_游戏.阶段 == 小游戏阶段_类.准备 and arg_游戏.剩余帧 == 前
    arg_游戏.api_开始()


def 图框() -> list[图框_类]:
    return [图框_类(66, 72, 33, 71)] * 5 + [图框_类(76, 74, 38, 72)] * 20


def test_原节点映射与每帧间隔() -> None:
    assert [小游戏种类_类.api_节点游戏(i).api_间隔() for i in (6, 7, 8, 999)] == [100, 100, 50, 50]


def test_企鹅原宝物数量仅放置抽样28次() -> None:
    for 种 in (1, 7, 12345, 0xDEADBEEF):
        戏, 随 = 企鹅_类(种), 随机数_类(种)
        数 = Counter(格.标志 & 15 for 行 in 戏.格子 for 格 in 行)
        assert [数[i] for i in range(1, 6)] == [3, 12, 3, 9, 1]
        assert len(戏.场景) == 戏.随机.次数 == 28
        assert sum(企鹅_类.api_有效(x, y) for x in range(9) for y in range(9)) == 64
        for _ in range(28):
            随.api_下一个()
        assert 戏.随机.随机.状态 == 随.状态


def test_企鹅准备片阻塞与挖宝不再抽随机() -> None:
    戏 = 企鹅_类(1)
    开始(戏)
    assert not 戏.场景 and 戏.空闲
    assert not 戏.api_点击(4, 4) and not 戏.api_点击(2, 6)
    assert 戏.api_点击(6, 2)
    for _ in range(200):
        戏.api_帧()
        x, y = 戏.位置
        assert 企鹅_类.api_有效(x, y)
        if 戏.空闲 or 戏.阶段 != 小游戏阶段_类.游玩:
            break
    assert 戏.随机.次数 == 28


def test_企鹅安全挖掘及真实结束计分() -> None:
    戏 = 企鹅_类(99)
    目标 = [(x, y) for y, 行 in enumerate(戏.格子) for x, 格 in enumerate(行) if 格.标志 & 15 > 1]
    for _ in range(600):
        if 戏.阶段 == 小游戏阶段_类.准备:
            戏.api_开始()
        if 戏.空闲 and 目标:
            戏.api_点击(*目标.pop(0))
        戏.api_帧()
        if 戏.阶段 == 小游戏阶段_类.完成:
            break
    assert 戏.阶段 == 小游戏阶段_类.完成 and 戏.分数显示 and 戏.api_得分() > 0
    assert 戏.api_得分() == 戏.发现[5] * 20 + 戏.发现[3] * 12 + 戏.发现[4] * 8 + 戏.发现[2] * 5


def test_企鹅炸弹提前结束且点击缩短结束停留() -> None:
    戏 = 企鹅_类(5)
    目标 = next(
        (x, y)
        for y, 行 in enumerate(戏.格子)
        for x, 格 in enumerate(行)
        if 格.标志 & 15 == 1 and (x, y) != (2, 6)
    )
    开始(戏)
    assert 戏.api_点击(*目标)
    声 = []
    for _ in range(120):
        戏.api_帧()
        声 += 戏.api_取声音()
        if 戏.阶段 == 小游戏阶段_类.结算:
            break
    assert any(项.操作 == 0 and 项.音效 == 15 for 项 in 声)
    戏.api_任意点击()
    戏.api_帧()
    assert 戏.阶段 == 小游戏阶段_类.完成 and 戏.api_得分() == 0


def test_气球真实生成点击与随机调用可重放() -> None:
    戏, 弹 = 气球_类(42), 0
    开始(戏)
    戏.api_帧()
    assert 戏.随机.次数 >= 16
    for _ in range(500):
        for 槽 in 戏.槽:
            if 槽.x and not 槽.种类 & 0xF0 and 槽.y < 380:
                弹 += 戏.api_点击(槽.x, 槽.y)
        戏.api_帧()
        if 戏.阶段 == 小游戏阶段_类.完成:
            break
    assert 弹 > 5 and 戏.阶段 == 小游戏阶段_类.完成
    随 = 随机数_类(42)
    for _ in range(戏.随机.次数):
        随.api_下一个()
    assert 随.状态 == 戏.随机.随机.状态


def test_气球每个未命中活动槽单独发出错音() -> None:
    戏 = 气球_类(42)
    开始(戏)
    for _ in range(30):
        戏.api_帧()
    戏.api_取声音()
    数 = sum(槽.x != 0 and not 槽.种类 & 0xF0 for 槽 in 戏.槽)
    assert 数 > 0 and 戏.api_点击(-500, -500) == 0
    assert len(戏.api_取声音()) == 数


def test_天降漂移原扩展精度和图框边界() -> None:
    assert [天降_类.api_漂移(x) for x in (320, 530, 110, 362, 278)] == [0, 50, -50, 10, -10]
    with pytest.raises(ValueError):
        天降_类(1, 0, [图框_类()] * 4)
    戏 = 天降_类(77, 4, 图框())
    assert 戏.财神x == 110 and 戏.场景[-1].条目 == 104


def test_天降真实移动接取与结束() -> None:
    戏 = 天降_类(77, 4, 图框())
    for _ in range(1000):
        if 戏.阶段 == 小游戏阶段_类.准备:
            戏.api_开始()
        候 = [槽 for 槽 in 戏.槽 if 槽.x and 槽.位 & 15 != 4]
        if 候:
            戏.api_目标(max(候, key=lambda s: s.y).x)
        戏.api_帧()
        if 戏.阶段 == 小游戏阶段_类.完成:
            break
    assert 戏.阶段 == 小游戏阶段_类.完成 and 戏.随机.次数 > 10
    assert 戏.api_得分() == 戏.接到[0] * 10 + 戏.接到[1] * 5 + 戏.接到[2] * 3 + 戏.接到[3]
