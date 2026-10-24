# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/effects.cpp的SceneData及人物/物件/待播覆盖辅助。
# ◑ 导入
from collections.abc import Callable
from dataclasses import dataclass, replace

from rich4.board_models import (
    业主外观_类,
    地产外观_类,
    场景_类,
    物件精灵_类,
    特殊人物精灵_类,
    玩家精灵_类,
)
from rich4.effect_spec import 演出规格_类, 演员模式_类
from rich4.game_types import 效果_类
from rich4.native_ui import 原生界面_类
from rich4.world import 世界_类


# ◕ 功能
@dataclass
class 待播人物_类:
    """
    已结算世界与尚未播放的运输电影之间的旧人物位置；None表示隐藏。

    更新日志：
    2026.10.24 - 首个待播电影决定同一玩家的覆盖，保持原队列顺序。
    """

    槽: int = 0
    位置: tuple[int, int] | None = None
    受伤: bool = False


class 演出场景_类:
    """
    原静止板面快照、附身物件跟随和待播电影演员覆盖，不执行游戏规则。

    更新日志：
    2026.10.24 - Scene持有独立数值列表，覆盖复制精灵而不修改World或外部旧精灵。
    """

    @staticmethod
    def api_在棋盘(arg_世: 世界_类, arg_槽: int) -> bool:
        if not 0 <= arg_槽 < len(arg_世.玩家):
            return False
        记, 状 = arg_世.玩家[arg_槽].记录, arg_世.玩家[arg_槽].状态
        return bool(
            记.控制标志
            and (记.x or 记.y)
            and (not (状.酒店天数 | 状.消失天数 | 状.监狱天数 | 状.医院天数) or 记.控制标志 & 0x20)
        )

    @staticmethod
    def _人物(arg_世: 世界_类, arg_槽: int, arg_帧: int, arg_服装: int) -> 玩家精灵_类:
        记, 状 = arg_世.玩家[arg_槽].记录, arg_世.玩家[arg_槽].状态
        return 玩家精灵_类(
            (记.x, 记.y),
            记.角色,
            记.方向,
            arg_帧 & 255,
            记.交通 & 3,
            原生界面_类.api_玩家色(记.颜色),
            记.槽位,
            记.槽位 == arg_世.头.当前玩家,
            False,
            记.节点 < len(arg_世.节点) and bool(arg_世.节点[记.节点].标志 & 0x80000000),
            状.梦游天数 != 0,
            bool(记.控制标志 & 0x40),
            特殊姿态=arg_服装,
        )

    @staticmethod
    def api_物件(arg_世: 世界_类, arg_人: list[玩家精灵_类], arg_帧: int) -> list[物件精灵_类]:
        组 = []
        for 物 in arg_世.物件:
            if 物.附身玩家:
                槽 = 物.附身玩家 - 1
                for 人 in arg_人:
                    if 人.槽位 == 槽:
                        远 = (
                            物.种类 == 18
                            and 槽 < len(arg_世.玩家)
                            and arg_世.玩家[槽].状态.神明信息
                        )
                        组.append(
                            物件精灵_类(人.位置, 物.种类, 人.方向, arg_帧 & 255, 2 if 远 else 1)
                        )
            elif 物.节点 and 物.节点 < len(arg_世.节点):
                点 = arg_世.节点[物.节点]
                组.append(物件精灵_类((点.x, 点.y), 物.种类, 物.方向, arg_帧 & 255))
        return 组

    @staticmethod
    def api_隐藏物件(
        arg_物件: list[物件精灵_类],
        arg_隐藏: Callable[[tuple[int, int], int], bool],
    ) -> None:
        arg_物件[:] = [物 for 物 in arg_物件 if 物.跟随 or not arg_隐藏(物.位置, 物.种类)]

    @staticmethod
    def api_业主(arg_世: 世界_类) -> list[业主外观_类]:
        return [
            业主外观_类(原生界面_类.api_玩家色(人.记录.颜色), 人.记录.角色) for 人 in arg_世.玩家
        ]

    @classmethod
    def api_静止快照(
        cls,
        arg_世: 世界_类,
        arg_时钟: int,
        arg_服装: tuple[int, int, int, int] = (0, 0, 0, 0),
    ) -> 场景_类:
        场, 帧 = 场景_类(), ((arg_时钟 & 0xFFFFFFFFFFFFFFFF) // 120) % 6
        场.业主 = cls.api_业主(arg_世)
        场.玩家 = [
            cls._人物(arg_世, i, 帧, arg_服装[i] if i < 4 else 0)
            for i in range(len(arg_世.玩家))
            if cls.api_在棋盘(arg_世, i)
        ]
        场.地产 = [
            地产外观_类(地.编号, 地.经济.业主, 地.经济.等级, 地.经济.连锁, 地.临时状态)
            for 地 in arg_世.地产[1:]
        ]
        场.设施 = [
            地产外观_类(地.编号, 地.业主, 地.等级, 地.类型, 地.临时状态) for 地 in arg_世.设施[1:]
        ]
        场.物件 = cls.api_物件(arg_世, 场.玩家, 帧)
        for i, 人 in enumerate(arg_世.特殊角色):
            if 人.不活跃状态 or not 人.节点 or 人.节点 >= len(arg_世.节点):
                continue
            场.特殊人物.append(
                特殊人物精灵_类(
                    (人.x, 人.y),
                    i + 4,
                    人.方向,
                    帧,
                    False,
                    False,
                    bool(arg_世.节点[人.节点].标志 & 0x80000000),
                    人.梦游天数 != 0,
                )
            )
        场.公司 = [地产外观_类(商.编号, 商.业主) for 商 in arg_世.公司 if 商.编号]
        return 场

    @staticmethod
    def api_加入待播(arg_待播: list[待播人物_类], arg_效果: 效果_类) -> None:
        规 = 演出规格_类.api_查询(arg_效果)
        if any(项.槽 == arg_效果.玩家 for 项 in arg_待播):
            return
        if 规.演员 in (演员模式_类.离开, 演员模式_类.停留) and arg_效果.起点 is not None:
            arg_待播.append(待播人物_类(arg_效果.玩家, (arg_效果.起点.x, arg_效果.起点.y), 规.受伤))
        elif 规.演员 in (演员模式_类.到达, 演员模式_类.隐藏):
            arg_待播.append(待播人物_类(arg_效果.玩家))

    @classmethod
    def api_应用待播(
        cls,
        arg_玩家: list[玩家精灵_类],
        arg_世: 世界_类,
        arg_待播: list[待播人物_类],
        arg_帧: int,
        arg_服装: tuple[int, int, int, int],
    ) -> None:
        for 项 in arg_待播:
            if not 0 <= 项.槽 < len(arg_世.玩家):
                continue
            精灵 = None
            for 人 in arg_玩家:
                if 人.槽位 == 项.槽:
                    精灵 = replace(人)
            arg_玩家[:] = [人 for 人 in arg_玩家 if 人.槽位 != 项.槽]
            if 项.位置 is None:
                continue
            if 精灵 is None:
                精灵 = cls._人物(arg_世, 项.槽, arg_帧, arg_服装[项.槽] if 项.槽 < 4 else 0)
            精灵.位置, 精灵.走动, 精灵.投骰, 精灵.踩水 = 项.位置, False, False, False
            精灵.受伤 = 精灵.受伤 or 项.受伤
            arg_玩家.append(精灵)
