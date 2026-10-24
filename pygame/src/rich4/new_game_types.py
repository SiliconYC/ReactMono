# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定menus.cpp/.hpp的新局数值表和NewGameChoice。
# ◑ 导入
from dataclasses import dataclass, field

from rich4.world_options import 新玩家_类


# ◕ 功能
@dataclass
class 新局选择_类:
    """
    原新局界面已经选定的参数，未支持的时间/胜利设置不制造新规则。

    更新日志：
    2026.10.24 - 首几位为实际选择的人类，其余由私有MT补电脑。
    """

    阶段: int = 0
    地图: int = 0
    资金: int = 200000
    租期: int = 0
    玩家: list[新玩家_类] = field(default_factory=list)
