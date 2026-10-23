# SPDX-License-Identifier: GPL-3.0-or-later
# 对应固定 C++ include/rich4/save.hpp 的值类型；不含任何主机指针。
# ◑ 导入
from dataclasses import dataclass
from typing import Literal


# ◕ 功能
@dataclass
class 存档头_类:
    """
    日期字段保留原始日/月/年，不在无损编解码阶段强制解释有效性。

    更新日志：
    2026.10.23 - 对应 SaveHeader。
    """

    签名: int
    日期: tuple[int, int, int]
    地图: int
    阶段: int
    人数: int
    人类人数: int
    当前玩家: int
    初始资金: int
    物价: int


@dataclass
class 玩家记录_类:
    """
    原玩家数组以槽位标识玩家；单独库存不叠加在 104 字节记录上。

    更新日志：
    2026.10.23 - 对应 PlayerState。
    """

    槽位: int
    颜色: int
    x: int
    y: int
    节点: int
    上次节点: int
    方向: int
    交通: int
    骰数: int
    角色: int
    性别: int
    控制标志: int
    现金: int
    银行: int
    贷款: int
    特殊融资: int
    点券: int
    卡片: list[int]
    道具: list[int]


@dataclass(frozen=True)
class 地图表_类:
    """
    数量排除零号记录；偏移相对地图块而非整个 DAT。

    更新日志：
    2026.10.23 - 对应 MapTableSummary。
    """

    数量: int
    偏移: int
    步长: int


@dataclass(frozen=True)
class 地图摘要_类:
    """
    五表顺序为节点、地产、设施、公司与保留景物。

    更新日志：
    2026.10.23 - 对应 MapSummary。
    """

    字节数: int
    表: tuple[地图表_类, 地图表_类, 地图表_类, 地图表_类, 地图表_类]


@dataclass(frozen=True)
class 存档区域_类:
    """
    连续覆盖全部原始字节，明确区分已解读和保留区域。

    更新日志：
    2026.10.23 - 对应 SaveRegion。
    """

    名称: str
    偏移: int
    长度: int
    类别: Literal["decoded", "partially_decoded", "raw_reserved"]
