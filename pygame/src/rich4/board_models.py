# SPDX-License-Identifier: GPL-3.0-or-later
# 固定 C++ board_renderer.hpp 的只读渲染快照值类型；不执行游戏规则。
# ◑ 导入
from dataclasses import dataclass, field


# ◕ 功能
@dataclass
class 相机_类:
    """
    世界坐标32单位一瓦片，八视角及半开视口。

    更新日志：
    2026.10.23 - 对应 board::Camera，位置元组按(x,y)。
    """

    中心: tuple[int, int] = (0, 0)
    旋转: int = 0
    视口: tuple[int, int, int, int] = (0, 40, 440, 480)


@dataclass
class 玩家精灵_类:
    """
    玩家原资源选择所需姿态；不从画面反推或修改规则状态。

    更新日志：
    2026.10.23 - 对应 PlayerSprite全部字段。
    """

    位置: tuple[int, int] = (0, 0)
    角色: int = 0
    方向: int = 0
    动画帧: int = 0
    交通: int = 0
    颜色: int = 0x7C00
    槽位: int = 0
    活跃: bool = False
    走动: bool = False
    踩水: bool = False
    梦游: bool = False
    受伤: bool = False
    投骰: bool = False
    特殊姿态: int = 0


@dataclass
class 物件精灵_类:
    """
    原物件编号1..20，跟随参数选择载体后方近/远偏移。

    更新日志：
    2026.10.23 - 对应 ObjectSprite。
    """

    位置: tuple[int, int] = (0, 0)
    种类: int = 0
    方向: int = 0
    动画帧: int = 0
    跟随: int = 0


@dataclass
class 特殊人物精灵_类:
    """
    原槽4..7及机器人槽8的渲染状态。

    更新日志：
    2026.10.23 - 对应 SpecialPlayerSprite。
    """

    位置: tuple[int, int] = (0, 0)
    槽位: int = 0
    方向: int = 0
    动画帧: int = 0
    活跃: bool = False
    走动: bool = False
    踩水: bool = False
    梦游: bool = False


@dataclass
class 地产外观_类:
    """
    普通地产/设施/公司原编号的覆盖状态，缺项仍用地图原状态。

    更新日志：
    2026.10.23 - 对应 PropertyState。
    """

    编号: int = 0
    业主: int = 0
    等级: int = 0
    类型: int = 0
    临时状态: int = 0


@dataclass
class 业主外观_类:
    """
    玩家不在画面时，土地仍保留该玩家颜色与角色旗帜。

    更新日志：
    2026.10.23 - 对应 PropertyOwner。
    """

    颜色: int = 0
    角色: int = 0


@dataclass
class 场景_类:
    """
    只读渲染快照，调用方拥有各项，渲染器不更改它们。

    更新日志：
    2026.10.23 - 对应 Scene。
    """

    玩家: list[玩家精灵_类] = field(default_factory=list)
    物件: list[物件精灵_类] = field(default_factory=list)
    地产: list[地产外观_类] = field(default_factory=list)
    设施: list[地产外观_类] = field(default_factory=list)
    特殊人物: list[特殊人物精灵_类] = field(default_factory=list)
    公司: list[地产外观_类] = field(default_factory=list)
    业主: list[业主外观_类] = field(default_factory=list)


@dataclass
class 绘制统计_类:
    """
    原地面、道路和精灵计数，包含被视口裁剪的入队精灵。

    更新日志：
    2026.10.23 - 对应 RenderStats。
    """

    地面: int = 0
    道路: int = 0
    精灵: int = 0
