# SPDX-License-Identifier: GPL-3.0-or-later
# 固定 C++ holidays_tests.cpp 的历史表边界与原规则异常。
# ◑ 导入
import pytest

from rich4.calendar import 日期_类
from rich4.holidays import 庆祝_类, 节日_类


# ◕ 功能
def test_农历表仅限原区间且首日农历在日历历元之前() -> None:
    assert 节日_类.api_农历(日期_类(1998, 1, 1)) == (1997, 12, 3)
    assert 节日_类.api_农历(日期_类(1998, 1, 28)) == (1998, 1, 1)
    assert 节日_类.api_农历(日期_类(2020, 12, 31)) == (2020, 11, 17)
    assert 节日_类.api_农历(日期_类(2021, 1, 1)) is None
    assert 节日_类.api_农历(日期_类(2026, 10, 5)) is None


def test_周六开市周日休市超表只用固定公历() -> None:
    assert not 节日_类.api_休市(日期_类(1998, 1, 3), 0, 0)
    assert 节日_类.api_休市(日期_类(1998, 1, 4), 0, 0)
    assert 节日_类.api_休市(日期_类(1998, 1, 28), 0, 0)
    assert 节日_类.api_休市(日期_类(2026, 10, 10), 0, 0)
    assert not 节日_类.api_休市(日期_类(2026, 2, 17), 0, 0)
    assert not 节日_类.api_休市(日期_类(2026, 11, 26), 3, 0)
    with pytest.raises(ValueError):
        节日_类.api_休市(日期_类(2026, 10, 5), 4, 0)


def test_节日跳过高位行并选原素材编号() -> None:
    assert 节日_类.api_节日行(日期_类(2026, 10, 31), 0, 0) == 13
    assert 节日_类.api_节日图片(日期_类(2026, 10, 31), 0, 0) == 17
    assert 节日_类.api_节日图片(日期_类(2026, 6, 10), 2, 1) == 98
    assert 节日_类.api_节日图片(日期_类(2026, 12, 25), 3, 1) == 127
    assert 节日_类.api_节日图片(日期_类(2026, 10, 11), 0, 0) is None
    assert 节日_类.api_庆祝(日期_类(2026, 1, 1), 0, 0) == 庆祝_类(523, 90, 0)
    assert 节日_类.api_庆祝(日期_类(2026, 12, 25), 3, 0) == 庆祝_类(554, 114, 13)
    assert 节日_类.api_庆祝(日期_类(2026, 12, 25), 0, 1) is None
    assert 节日_类.api_庆祝(日期_类(2020, 1, 25), 0, 0) == 庆祝_类(0, 0, 14)


def test_贷款到期九十天后顺延休市() -> None:
    assert 节日_类.api_贷款到期(日期_类(2026, 10, 5), 0, 0) == 日期_类(2027, 1, 4)
    assert 节日_类.api_贷款到期(日期_类(2026, 7, 12), 0, 0) == 日期_类(2026, 10, 12)
