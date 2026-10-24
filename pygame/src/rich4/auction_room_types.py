# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定finance.hpp::AuctionRoom的Bid/Sold。
# ◑ 导入
from dataclasses import dataclass


# ◕ 功能
@dataclass
class 拍卖出价_类:
    """
    原待播放的出价参数，核心尚未接收此选择。

    更新日志：
    2026.10.24 - 决策键改变立即弃掉旧出价，不重用其它竞买人的结果。
    """

    键: str
    索引: int = 0
    行动: int = 0
    价格: int = 0
    开始: int = 0


@dataclass
class 拍卖成交_类:
    """
    原已结算的成交演出，不再次转移资产。

    更新日志：
    2026.10.24 - 保留开始零哨兵与单次锤声。
    """

    赢家: int = 0
    价格: int = 0
    地产: int = 0
    开始: int = 0
    已响: bool = False
