# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
from dataclasses import dataclass, field

from rich4.flc import 动画_类
from rich4.graphics import 图像_类


# ◕ 功能
@dataclass
class 商店屏幕状态_类:
    """
    原Shop逐次访问状态，售出标记与货架初始顺序独立保留。

    更新日志：
    2026.10.24 - 二次确认保留种类/行/实际值，不以值去重原货架。
    """

    活跃: bool = False
    模式: int = 0
    卡片: list[int] = field(default_factory=list)
    道具: list[int] = field(default_factory=list)
    卡已买: list[bool] = field(default_factory=list)
    道具已买: list[bool] = field(default_factory=list)
    打开: int = 0
    气泡止: int = 0
    气泡: str = ""
    离开中: bool = False
    离开时: int = 0
    选择类: int = -1
    选择行: int = 0
    选择值: int = 0


@dataclass
class 施法电影_类:
    """
    原Panel20渐进FLC与首次声音标记。

    更新日志：
    2026.10.24 - 与共享屏幕状态分开，保留电影末白帧。
    """

    解码: 动画_类
    图像: 图像_类 = field(default_factory=lambda: 图像_类(0, 0, []))
    已响: bool = False


@dataclass
class 魔法屏幕状态_类:
    """
    原Magic人类选组、效果、施法时钟与下一帧响应。

    更新日志：
    2026.10.24 - scheduled阻止电影末帧重复安排真实效果。
    """

    活跃: bool = False
    打开: int = 0
    类别: int = -1
    选中: int = -1
    施法时: int = 0
    已安排: bool = False
    电影: 施法电影_类 | None = None


@dataclass
class 救援屏幕状态_类:
    """
    原Rescue选中/点数不足与NPC感谢演出。

    更新日志：
    2026.10.24 - 感谢只在演出结束或跳过后才回答原决策。
    """

    活跃: bool = False
    选中: int = -1
    不足止: int = 0
    打开: int = 0
    感谢: int = -1
    感谢止: int = 0
    感谢已安排: bool = False


@dataclass
class 电脑施法_类:
    """
    原MagicCast的类别、效果、起始哨兵和渐进电影。

    更新日志：
    2026.10.24 - 仅表现核心已经执行的结果，不重复施法。
    """

    类别: int = 0
    效果: int = 0
    开始: int = 0
    电影: 施法电影_类 | None = None
