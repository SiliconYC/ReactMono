# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定finance.hpp::TradingActions/TradingBoard::View及market.cpp::PropertyRow。
# ◑ 导入
from collections.abc import Callable
from dataclasses import dataclass
from enum import IntEnum

from rich4.trading import 挂单_类


# ◕ 功能
class 交易视图_类(IntEnum):
    """
    原公告栏六个视图编号，不能将详情或挑选页当成另一套规则。

    更新日志：
    2026.10.24 - 保留原View顺序。
    """

    公告栏, 菜单, 股票, 地产, 物品, 详情 = range(6)


@dataclass(frozen=True)
class 交易动作_类:
    """
    原挂牌/撤件/购买/关闭的强制真实回调。

    更新日志：
    2026.10.24 - 不提供假成功默认值。
    """

    挂牌: Callable[[挂单_类], bool]
    撤件: Callable[[int], bool]
    购买: Callable[[int, int], bool]
    关闭: Callable[[], None]


@dataclass
class 交易地产行_类:
    """
    原PropertyRow的显示值与五分类标志。

    更新日志：
    2026.10.24 - 无效代码依原返回空行，不改写世界。
    """

    地点: str = ""
    开发: str = ""
    价格: int = 0
    收费: int = 0
    到期: int = 0
    连锁: bool = False
    设施: bool = False
    已建: bool = False
