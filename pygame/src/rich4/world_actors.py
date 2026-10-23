# SPDX-License-Identifier: GPL-3.0-or-later
# 对应固定 C++ world.hpp 的特殊角色和地图物件。
# ◑ 导入
from dataclasses import dataclass, field


# ◕ 功能
@dataclass
class 特殊角色_类:
    """
    原槽位 4..8 的特殊移动角色，保留原不活跃状态。

    更新日志：
    2026.10.23 - 对应 SpecialActor。
    """

    x: int = 0
    y: int = 0
    节点: int = 0
    上次节点: int = 0
    业主: int = 0
    方向: int = 0
    不活跃状态: int = 0
    标志: int = 0
    睡眠天数: int = 0
    梦游天数: int = 0
    停留天数: int = 0
    龟行天数: int = 0


@dataclass
class 地图物件_类:
    """
    物件运动浮点字段以位模式保存，解读与动画阶段分离。

    更新日志：
    2026.10.23 - 对应 MapObject。
    """

    种类: int = 0
    方向: int = 0
    节点: int = 0
    剩余天数: int = 0
    附身玩家: int = 0
    动画剩余: int = 0
    动画步: int = 0
    运动位: list[int] = field(default_factory=lambda: [0] * 4)
