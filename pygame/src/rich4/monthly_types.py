# SPDX-License-Identifier: GPL-3.0-or-later
# 对应固定tools/screens/monthly.hpp的Bubble/Movie/Playing值状态。
# ◑ 导入
from dataclasses import dataclass, field

from rich4.flc import 动画_类
from rich4.game_types import 效果_类, 月报_类
from rich4.graphics import 图像_类


# ◕ 功能
@dataclass
class 月泡_类:
    """
    原主持人气泡位置、原文与实际语音等待。

    更新日志：
    2026.10.24 - 与消息层不同，这里的点击处理由各月结状态机决定。
    """

    条帧: int = 0
    x: int = 0
    y: int = 0
    dx: int = 0
    dy: int = 0
    文字: str = ""
    剩余毫秒: int = 0
    显示: bool = False


@dataclass
class 月片_类:
    """
    原开奖笼/中奖与月报人物反应影片，保留最终解码帧。

    更新日志：
    2026.10.24 - 运行与叠加标志分开；循环时依原倒带。
    """

    解码: 动画_类 | None = None
    静帧: 图像_类 = field(default_factory=lambda: 图像_类(0, 0, []))
    x: int = 0
    y: int = 0
    次数: int = 1
    已过: int = 0
    运行: bool = False
    叠加: bool = True


@dataclass
class 月播_类:
    """
    原Playing的已结算月数据、窗口计时、主持人/人物/影片与独立装饰随机。

    更新日志：
    2026.10.24 - 字段独立于世界，不在显示时再次发股利或计利息。
    """

    效果: 效果_类
    数据: 月报_类 = field(default_factory=月报_类)
    状态: int = 0
    计数: int = 0
    节拍: int = 100
    已过: int = 0
    点过: bool = False
    略等待: bool = False
    画过: bool = False
    泡: 月泡_类 = field(default_factory=月泡_类)
    片: 月片_类 = field(default_factory=月片_类)
    次片: 月片_类 = field(default_factory=月片_类)
    布局: int = 0
    女士: int = 0
    聚光: int = -1
    隐藏: int = -1
    奖: int = 0
    卡片: bool = False
    列队: bool = False
    欢颜: bool = False
    排过: bool = False
    球: bool = False
    绿: bool = False
    名牌: bool = False
    眼: int = -1
    嘴: int = -1
    左: int = -1
    眨眼: int = -1
    眨步: int = 0
    嘴时: int = 0
    种子: int = 1
    关闭: bool = False
