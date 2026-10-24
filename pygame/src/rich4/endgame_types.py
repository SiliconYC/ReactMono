# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/endgame.hpp的原编号/资料/回调契约。
# ◑ 导入
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum


# ◕ 功能
class 结局种类_类(IntEnum):
    """
    原Kind顺序。

    更新日志：
    2026.10.24 - 原none/play_again/stage_clear编号保留。
    """

    无 = 0
    再玩 = 1
    过关 = 2


class 再玩步骤_类(IntEnum):
    """
    原倒数、等待台词、倒闭电影、完成四步。

    更新日志：
    2026.10.24 - 同意回调不提前代替影片结束回应。
    """

    倒数 = 0
    台词 = 1
    电影 = 2
    完成 = 3


@dataclass
class 过关资料_类:
    """
    原StageClear，全部由宿主提供而非界面推断胜负。

    更新日志：
    2026.10.24 - 种子只控制表现追逐高度，不消费游戏Watcom流。
    """

    阶段: int = 0
    地图: int = 0
    角色: int = 0
    已清: int = 0
    单人: bool = True
    种子: int = 1


@dataclass
class 结局动作_类:
    """
    原EndgameActions，宿主负责实际菜单/存档/续图操作。

    更新日志：
    2026.10.24 - 可空回调沿用原屏幕契约。
    """

    同意: Callable[[], None] | None = None
    再玩完成: Callable[[bool], None] | None = None
    下一图: Callable[[int], None] | None = None
    主菜单: Callable[[], None] | None = None
