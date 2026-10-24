# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from test_number_pad import _宿

from rich4.main_menu import 主菜单_类, 主菜单动作_类
from rich4.native_ui import 字体_类


# ◕ 功能
def test_禁用读取仍保留原悬选声但按钮不得由正常派发调用(字体: 字体_类) -> None:
    菜单, 声, 调用 = 主菜单_类(), [], []
    宿 = _宿(字体, 声)
    动 = 主菜单动作_类(
        lambda: 调用.append(1),
        lambda: 调用.append(2),
        lambda: 调用.append(3),
        lambda: 调用.append(5),
        lambda: 调用.append(4),
        False,
    )
    宿.框.指针x, 宿.框.指针y = 328, 380
    菜单.api_绘制(宿, 动)
    assert 声 == [0] and not next(b for b in 宿.框.按钮 if b.编号 == 2).启用
    宿.框.按钮.clear()
    菜单.api_绘制(宿, 动)
    assert 声 == [0]
    next(b for b in 宿.框.按钮 if b.编号 == 1).动作()
    assert 调用 == [1] and 声 == [0, 1]


def test_退出命中区向底部扩大而原悬选只认精灵区域(字体: 字体_类) -> None:
    菜单, 宿 = 主菜单_类(), _宿(字体, [])
    动 = 主菜单动作_类(lambda: None, lambda: None, lambda: None, lambda: None, lambda: None)
    菜单.api_绘制(宿, 动)
    assert next(b for b in 宿.框.按钮 if b.编号 == 5).区域 == (316, 441, 432, 480)
