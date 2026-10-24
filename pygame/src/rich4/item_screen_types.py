# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from collections.abc import Callable
from dataclasses import dataclass


# ◕ 功能
@dataclass
class 物品宿主_类:
    """
    原items::Host，动作必须由真实会话与主应用提供。

    更新日志：
    2026.10.24 - 不提供伪成功或固定决策回调。
    """

    关闭: Callable[[], None]
    通知: Callable[[bool, str], None]
    回答: Callable[[int], bool]


@dataclass
class 卡图等待_类:
    """
    卡图截止时钟与显示之后才运行的真实动作。

    更新日志：
    2026.10.24 - 超时排到下一帧，按钮跳过立即运行，遵循原区别。
    """

    卡片: int
    截止: int = 0
    之后: Callable[[], None] | None = None


@dataclass
class 物品按住_类:
    """
    原Press的所有者、半开区域、动作及帮助索引。

    更新日志：
    2026.10.24 - 放开前不消耗物品，滑离或换屏撤销。
    """

    所有者: str
    区域: tuple[int, int, int, int]
    动作: Callable[[], None]
    物品: int = 0
