# SPDX-License-Identifier: GPL-3.0-or-later
# 固定 C++ board_renderer_tests.cpp 的原查表/小数舍入和角色姿态。
# ◑ 导入
import pytest

from rich4.board_models import 玩家精灵_类, 相机_类
from rich4.board_projection import 棋盘投影_类


# ◕ 功能
@pytest.mark.parametrize(
    "arg_点,arg_预期",
    [
        ((0, 0), (220, 260)),
        ((32, 0), (254, 249)),
        ((0, 32), (234, 285)),
        ((-32, 0), (183, 269)),
        ((1, 0), (222, 260)),
        ((31, 0), (253, 250)),
        ((-448, -448), (-494, 49)),
        ((480, 0), None),
        ((0, -480), None),
        ((2147483647, 0), None),
    ],
)
def test_原投影锚点分数和裁除(arg_点: tuple[int, int], arg_预期: tuple[int, int] | None) -> None:
    assert 棋盘投影_类.api_投影(arg_点, 相机_类((0, 0))) == arg_预期


def test_八视角小数相机中心不漂移及极值差值() -> None:
    for 视角 in range(8):
        for 小数 in range(32):
            中心 = (1024 + 小数, 1055 - 小数)
            assert 棋盘投影_类.api_投影(中心, 相机_类(中心, 视角)) == (220, 260)
    中心 = (-2147483648, 2147483647)
    assert 棋盘投影_类.api_投影(中心, 相机_类(中心)) == (220, 260)


def test_反投影返回最近瓦片中心而非矩阵逆解() -> None:
    for 视角 in range(8):
        相机 = 相机_类((1000, 2010), 视角)
        for 差x, 差y in [(0, 0), (-2, 1), (2, -1), (1, 1)]:
            世界点 = ((1000 // 32 + 差x) * 32 + 16, (2010 // 32 + 差y) * 32 + 16)
            屏幕 = 棋盘投影_类.api_投影(世界点, 相机)
            assert 屏幕 is not None and 棋盘投影_类.api_反投影(屏幕, 相机) == 世界点
    assert 棋盘投影_类.api_反投影((440, 200), 相机) is None
    assert 棋盘投影_类.api_反投影((100, 39), 相机) is None


def test_相机错误和角色姿态优先级() -> None:
    with pytest.raises(ValueError):
        棋盘投影_类.api_投影((0, 0), 相机_类((0, 0), 8))
    with pytest.raises(ValueError):
        棋盘投影_类.api_投影((0, 0), 相机_类((0, 0), 0, (0, 40, 0, 480)))
    玩家 = 玩家精灵_类(角色=2, 交通=2, 走动=True)
    assert 棋盘投影_类.api_角色资源(玩家) == 128 + 42 + 7
    玩家.踩水 = True
    assert 棋盘投影_类.api_角色资源(玩家) == 128 + 42 + 14
    玩家.梦游 = True
    assert 棋盘投影_类.api_角色资源(玩家) == 128 + 42 + 17
    玩家.投骰 = True
    assert 棋盘投影_类.api_角色资源(玩家) == 128 + 42 + 2
    玩家.特殊姿态 = 20
    assert 棋盘投影_类.api_角色资源(玩家) == 128 + 42 + 2
    玩家.投骰 = False
    assert 棋盘投影_类.api_角色资源(玩家) == 128 + 42 + 20
