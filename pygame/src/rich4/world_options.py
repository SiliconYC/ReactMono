# SPDX-License-Identifier: GPL-3.0-or-later
# 固定 C++ world.hpp 的开局参数；核心不读取宿主时钟。
# ◑ 导入
from dataclasses import dataclass, field


# ◕ 功能
@dataclass
class 新玩家_类:
    """
    起点零表示由首次回合生成，不能提前假设出生位置。

    更新日志：
    2026.10.23 - 对应 NewGamePlayer。
    """

    角色: int = 10
    控制: int = 1
    交通: int = 0
    起点: int = 0


@dataclass
class 新局设置_类:
    """
    日期采用参考核心默认原字段，图形宿主将显式传入当前日期。

    更新日志：
    2026.10.23 - 对应 NewGameOptions。
    """

    日期: tuple[int, int, int] = (5, 10, 2026)
    地图: int = 0
    阶段: int = 0
    初始资金: int = 200000
    租约模式: int = 0
    随机种子: int = 1
    玩家: list[新玩家_类] = field(
        default_factory=lambda: [
            新玩家_类(10, 1),
            新玩家_类(3, 2),
            新玩家_类(0, 2),
            新玩家_类(6, 2),
        ]
    )
