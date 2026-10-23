# ◑ 导入
import pytest

from rich4.calendar import 日期_类
from rich4.direction import 方向_类
from rich4.random import 随机数_类


# ◕ 功能
def test_Watcom_随机序列和状态恢复() -> None:
    随机 = 随机数_类(1)
    assert [随机.api_下一个() for _ in range(5)] == [16838, 5758, 10113, 17515, 31051]
    恢复 = 随机数_类(随机.状态)
    assert [随机.api_下一个() for _ in range(100)] == [恢复.api_下一个() for _ in range(100)]


def test_日期遵循四年闰而不是公历世纪例外() -> None:
    assert 日期_类(2100, 2, 28).api_加天数(1) == 日期_类(2100, 2, 29)
    assert 日期_类(1998, 1, 1).api_星期() == 4
    assert 日期_类.api_从天数(0) == 日期_类(1998, 1, 1)
    assert 日期_类(2000, 2, 29).api_天数() == 789
    assert 日期_类.api_打包间隔(0x07CE0C01, 0x100) == 0x07CF0101
    with pytest.raises(ValueError):
        日期_类(1998, 1, 1).api_加天数(-1)


@pytest.mark.parametrize(
    "arg_dx,arg_dy,arg_期望",
    [
        (0, 0, 2),
        (1, 0, 2),
        (0, -1, 4),
        (-1, 0, 6),
        (0, 1, 0),
        (2048, -848, 2),
        (2048, -849, 3),
        (2048, -850, 3),
        (-2147483648, -2147483648, 7),
    ],
)
def test_方向的整数角度边界(arg_dx: int, arg_dy: int, arg_期望: int) -> None:
    assert 方向_类.api_计算(arg_dx, arg_dy) == arg_期望
