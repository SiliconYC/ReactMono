# SPDX-License-Identifier: GPL-3.0-or-later
# 对应固定 C++ world.hpp 地图记录；零号项与原编号均保留。
# ◑ 导入
from dataclasses import dataclass, field

from rich4.economy import 地产经济_类


# ◕ 功能
@dataclass
class 节点_类:
    """
    原事件/地产复合编码保留整数，不猜测未知类型。

    更新日志：
    2026.10.23 - 对应 MapNode。
    """

    编号: int = 0
    x: int = 0
    y: int = 0
    邻居: list[int] = field(default_factory=lambda: [0] * 4)
    类型索引: int = 0
    地面精灵: int = 0
    标志: int = 0
    名字: bytes = b""


@dataclass
class 地产_类:
    """
    地产经济信息与原始临时状态、租约字段。

    更新日志：
    2026.10.23 - 对应 Land。
    """

    编号: int = 0
    x: int = 0
    y: int = 0
    经济: 地产经济_类 = field(default_factory=lambda: 地产经济_类(b"", 0, 0, 0, (0,) * 6))
    临时状态: int = 0
    方向: int = 0
    每级造价: int = 0
    地价: int = 0
    已移除建筑: int = 0
    到期日: int = 0


@dataclass
class 设施_类:
    """
    特殊设施首档租金同时作为每级建设价格。

    更新日志：
    2026.10.23 - 对应 Facility。
    """

    编号: int = 0
    x: int = 0
    y: int = 0
    名字: bytes = b""
    类型: int = 0
    业主: int = 0
    等级: int = 0
    方向: int = 0
    临时状态: int = 0
    标志30: int = 0
    地价: int = 0
    各级租金: list[int] = field(default_factory=lambda: [0] * 6)
    已移除建筑: int = 0
    到期日: int = 0

    @property
    def 每级造价(self) -> int:
        return self.各级租金[0]

    @每级造价.setter
    def 每级造价(self, arg_金额: int) -> None:
        self.各级租金[0] = arg_金额


@dataclass
class 公司_类:
    """
    公司资金/股权与原始排名；名字为只读渲染资料。

    更新日志：
    2026.10.23 - 对应 Commercial。
    """

    编号: int = 0
    x: int = 0
    y: int = 0
    业主: int = 0
    类型: int = 0
    方向: int = 0
    精灵: int = 0
    通行费: int = 0
    股票索引: int = 0
    资金: int = 0
    资金变化: int = 0
    剩余股份: int = 0
    股东排名: list[int] = field(default_factory=lambda: [0] * 4)
    估值: int = 0
    名字: bytes = b""


@dataclass
class 景物_类:
    """
    第五表只解释已知渲染字段，未知字节不赋予虚构玩法。

    更新日志：
    2026.10.23 - 对应 Landscape。
    """

    编号: int = 0
    x: int = 0
    y: int = 0
    方向: int = 0
    精灵: int = 0
    名字: bytes = b""
