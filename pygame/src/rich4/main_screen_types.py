# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/main_screen.hpp::main_ids/MainScreenActions。
# ◑ 导入
from collections.abc import Callable
from dataclasses import dataclass


# ◕ 功能
class 主屏编号_类:
    """
    原重放依赖的稳定命中编号，不按Python界面重新编号。

    更新日志：
    2026.10.24 - 原71..102稀疏编号逐项保留。
    """

    保存, 载入, 左转, 右转, 查询, 设置, 卡片, 道具, 股票, 交易, 帮助, 托管 = range(71, 83)
    全图, 关全图, 页签首, 太阳, 月亮, 小图, 掷骰, 骰数, GO框 = 83, 84, 85, 89, 90, 91, 100, 101, 102


@dataclass
class 主屏动作_类:
    """
    由真实应用接线的原主屏操作，声音可关闭，按钮状态独立传入。

    更新日志：
    2026.10.24 - 必须显式提供功能回调，避免未实现功能退化为无声空操作。
    """

    帮助: Callable[[], None]
    设置: Callable[[], None]
    托管: Callable[[], None]
    载入: Callable[[], None]
    保存: Callable[[], None]
    查询: Callable[[], None]
    道具: Callable[[], None]
    卡片: Callable[[], None]
    交易: Callable[[], None]
    股票: Callable[[], None]
    旋转: Callable[[int], None]
    掷骰: Callable[[], None]
    骰数: Callable[[int], None]
    声音: Callable[[int], None] | None = None
    可保存: bool = False
    可载入: bool = False
