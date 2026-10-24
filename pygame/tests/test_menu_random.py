# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from rich4.menu_random import 菜单随机_类


# ◕ 功能
def test_菜单MT种子一的原引擎序列不使用Python默认播种协议() -> None:
    随 = 菜单随机_类(1)
    assert [随.api_取() for _ in range(5)] == [
        1791095845,
        4282876139,
        3093770124,
        4005303368,
        491263,
    ]


def test_重新播种还原整624词块边界() -> None:
    随 = 菜单随机_类(0xFFFFFFFF)
    a = [随.api_取() for _ in range(1300)]
    随.api_播种(0xFFFFFFFF)
    assert [随.api_取() for _ in range(1300)] == a
