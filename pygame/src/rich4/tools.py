# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/tools.cpp，保留原选择位域和消耗/回调顺序。
# ◑ 导入
from dataclasses import dataclass
from typing import Callable

from rich4.direction import 方向_类
from rich4.random import 随机数_类
from rich4.services import 服务_类
from rich4.world import 世界_类
from rich4.world_map import 节点_类


# ◕ 功能
@dataclass
class 道具结果_类:
    """
    取消/不可用与缺失真实规则依赖分开，不能把拒绝视为应用成功。

    更新日志：
    2026.10.23 - 对应tools::Result。
    """

    支持: bool = True
    已应用: bool = False
    消息: str = ""


@dataclass
class 道具回调_类:
    """
    机器人、掷骰、时光机、房屋/爆炸及原语音的真实会话接口。

    更新日志：
    2026.10.23 - 对应tools::Callbacks，表现不消费规则随机流。
    """

    机器人: Callable[[int], None] | None = None
    遥控骰: Callable[[int, int], None] | None = None
    恢复上次: Callable[[], bool] | None = None
    升级: Callable[[int], None] | None = None
    爆炸: Callable[[int, bool, int], None] | None = None
    传送前: Callable[[int], None] | None = None
    语音: Callable[[int, int], None] | None = None


class 道具_类:
    """
    原十三道具、地图/角色传送和交通工具收起，不使用C++运行后端。

    更新日志：
    2026.10.23 - 对应tools全部规则与selection_flags。
    """

    @staticmethod
    def _取(arg_表: list, arg_号: int):
        if not 0 <= arg_号 < len(arg_表):
            raise IndexError("道具引用索引越界")
        return arg_表[arg_号]

    @staticmethod
    def _略(arg_文: str) -> 道具结果_类:
        return 道具结果_类(True, False, arg_文)

    @staticmethod
    def _缺(arg_文: str) -> 道具结果_类:
        return 道具结果_类(False, False, arg_文)

    @staticmethod
    def _道路(arg_世: 世界_类, arg_号: int) -> bool:
        return 0 < arg_号 < 2000 and arg_号 < len(arg_世.节点)

    @classmethod
    def _之间(cls, arg_世: 世界_类, arg_前: int, arg_后: int) -> int:
        a, b = cls._取(arg_世.节点, arg_前), cls._取(arg_世.节点, arg_后)
        return 方向_类.api_计算(b.x - a.x, b.y - a.y)

    @staticmethod
    def _首邻居(arg_节: 节点_类) -> int:
        return next((号 for 号 in arg_节.邻居 if 号), 0)

    @classmethod
    def _装备(cls, arg_世: 世界_类, arg_槽: int, arg_物: int) -> 道具结果_类:
        人 = cls._取(arg_世.玩家, arg_槽)
        状 = 人.记录
        交 = 1 if arg_物 == 5 else 2 if arg_物 == 6 else 3
        if (状.交通 & 3 if 交 == 3 else 状.交通) == 交:
            return cls._略("已經使用這種交通工具")
        if 状.交通 in (1, 2):
            i = 4 if 状.交通 == 1 else 5
            状.道具[i] = (状.道具[i] + 1) & 255
        if arg_物 == 12:
            人.状态.标志100, 人.状态.标志101 = 状.交通, 状.骰数
            状.交通, 状.骰数 = 31, 1
        else:
            状.交通, 状.骰数 = 交, 交 + 1
        状.道具[arg_物 - 1] = (状.道具[arg_物 - 1] - 1) & 255
        return 道具结果_类(True, True)

    @classmethod
    def _放置(cls, arg_世: 世界_类, arg_槽: int, arg_物: int, arg_节: int) -> 道具结果_类:
        if not cls._道路(arg_世, arg_节):
            return cls._略("請選擇道路")
        节 = arg_世.节点[arg_节]
        if 节.标志 & 0x00FFFF00:
            return cls._略("道路已被佔用")
        首 = 16 if arg_物 == 2 else 26 if arg_物 == 3 else 36
        for i in range(首, 首 + 10):
            物 = cls._取(arg_世.物件, i)
            if 物.节点:
                continue
            物.种类, 物.节点, 物.剩余天数, 物.附身玩家 = arg_物 + 14, arg_节, 0, 0
            物.方向 = cls._之间(arg_世, cls._首邻居(节), arg_节)
            节.标志 |= (i + 1) << 16
            状 = cls._取(arg_世.玩家, arg_槽).记录
            状.道具[arg_物 - 1] = (状.道具[arg_物 - 1] - 1) & 255
            return 道具结果_类(True, True)
        return cls._略("沒有可放置的道具")

    @classmethod
    def _搬地(cls, arg_世: 世界_类, arg_源: int, arg_目: int) -> 道具结果_类:
        if arg_源 == arg_目:
            return cls._略("請選擇另一塊空地")
        if (
            2000 < arg_源 < 4000
            and 2000 < arg_目 < 4000
            and max(arg_源, arg_目) - 2000 < len(arg_世.地产)
        ):
            a, b = arg_世.地产[arg_源 - 2000], arg_世.地产[arg_目 - 2000]
            if b.经济.业主 or b.经济.等级:
                return cls._略("目的地必須是空地")
            b.经济.业主, b.经济.等级, b.经济.连锁, b.到期日 = (
                a.经济.业主,
                a.经济.等级,
                a.经济.连锁,
                a.到期日,
            )
            a.经济.业主 = a.经济.等级 = a.经济.连锁 = a.到期日 = a.已移除建筑 = 0
            return 道具结果_类(True, True)
        if (
            4000 < arg_源 < 6000
            and 4000 < arg_目 < 6000
            and max(arg_源, arg_目) - 4000 < len(arg_世.设施)
        ):
            a, b = arg_世.设施[arg_源 - 4000], arg_世.设施[arg_目 - 4000]
            if b.业主 or b.等级:
                return cls._略("目的地必須是空地")
            b.业主, b.等级, b.类型, b.到期日 = a.业主, a.等级, a.类型, a.到期日
            a.业主 = a.等级 = a.类型 = a.到期日 = a.已移除建筑 = 0
            return 道具结果_类(True, True)
        return cls._略("請選擇同類型的土地")

    @classmethod
    def _传送(
        cls, arg_世: 世界_类, arg_槽: int, arg_源: int, arg_目: int, arg_钩: 道具回调_类
    ) -> 道具结果_类:
        if 2000 < arg_源 < 6000:
            return cls._搬地(arg_世, arg_源, arg_目)
        if not arg_源 & 0x8000 or not cls._道路(arg_世, arg_目):
            return cls._略("請選擇物件和目的地")
        物号 = arg_源 >> 8 & 63
        if 0 < 物号 <= len(arg_世.物件) and arg_世.物件[物号 - 1].附身玩家:
            arg_源 = 0x8000 | (1 << (arg_世.物件[物号 - 1].附身玩家 - 1))
        节 = arg_世.节点[arg_目]
        if arg_源 & 255:
            槽 = ((arg_源 & 255) & -(arg_源 & 255)).bit_length() - 1
            if 槽 >= 8 or (
                槽 < 4 and (槽 >= len(arg_世.玩家) or not arg_世.玩家[槽].记录.控制标志)
            ):
                return cls._略("角色無法移動")
            朝 = arg_世.玩家[槽].记录.方向 if 槽 < 4 else arg_世.特殊角色[槽 - 4].方向
            邻 = [号 for i, 号 in enumerate(节.邻居) if 号 and not 节.标志 & (0x40000000 >> i)]
            if not 邻:
                return cls._略("目的地沒有通路")
            最小, 选 = 8, 0
            for i, 号 in enumerate(邻):
                候 = cls._之间(arg_世, arg_目, 号)
                差 = abs(朝 - 候)
                if 差 > 4:
                    差 = (8 - 差) & 0xFFFFFFFF
                if 差 < 最小:
                    最小, 选 = 差, i
            朝 = cls._之间(arg_世, arg_目, 邻[选])
            前 = next((号 for 号 in 邻 if 号 != 邻[选]), 邻[0])
            位 = 0x100 << 槽
            if 槽 < 4:
                if 槽 == arg_槽 and arg_钩.传送前:
                    arg_钩.传送前(槽)
                人 = arg_世.玩家[槽].记录
            else:
                人 = arg_世.特殊角色[槽 - 4]
            cls._取(arg_世.节点, 人.节点).标志 &= ~位 & 0xFFFFFFFF
            人.节点, 人.上次节点, 人.方向, 人.x, 人.y = arg_目, 前, 朝, 节.x & 65535, 节.y & 65535
            if 槽 < 4:
                for 物 in arg_世.物件:
                    if 物.附身玩家 == 槽 + 1:
                        物.节点 = 人.节点
            节.标志 |= 位
            return 道具结果_类(True, True)
        if not 0 < 物号 <= len(arg_世.物件):
            return cls._略("物件不存在")
        物 = arg_世.物件[物号 - 1]
        if not 物.节点 or 节.标志 & 0x00FF0000:
            return cls._略("目的地已有物件")
        cls._取(arg_世.节点, 物.节点).标志 &= 0xFF00FFFF
        物.节点 = arg_目
        节.标志 |= 物号 << 16
        物.方向 = cls._之间(arg_世, cls._首邻居(节), arg_目)
        return 道具结果_类(True, True)

    @staticmethod
    def api_选择位(arg_物: int, arg_源: int = 0) -> int:
        if arg_物 == 11:
            return (
                0x1200036
                if not arg_源
                else 0x2090802
                if 2000 < arg_源 < 4000
                else 0x2090804
                if 4000 < arg_源 < 6000
                else 0x2090001
            )
        return {2: 1, 3: 0x10001, 4: 0x20001, 7: 0x300C0, 9: 0x2090006, 13: 0x400C0}.get(arg_物, 0)

    @classmethod
    def api_使用(
        cls,
        arg_世: 世界_类,
        arg_随机: 随机数_类,
        arg_槽: int,
        arg_物: int,
        arg_目标: int,
        arg_目的地: int,
        arg_钩: 道具回调_类,
    ) -> 道具结果_类:
        if not 0 <= arg_槽 < len(arg_世.玩家) or not 1 <= arg_物 <= 13:
            raise ValueError("无效道具动作")
        if not arg_世.玩家[arg_槽].记录.道具[arg_物 - 1]:
            return cls._略("沒有這項道具")

        def 说() -> None:
            if arg_钩.语音:
                arg_钩.语音(arg_槽, arg_物 - 1)

        def 用(arg_槽位: int = arg_槽) -> None:
            服务_类._库存(arg_世, arg_槽位).api_用道具(arg_物)

        if arg_物 in (5, 6, 12):
            结果 = cls._装备(arg_世, arg_槽, arg_物)
            if 结果.已应用:
                说()
            return 结果
        if 2 <= arg_物 <= 4:
            结果 = cls._放置(arg_世, arg_槽, arg_物, arg_目标)
            if 结果.已应用:
                说()
            return 结果
        if arg_物 == 11:
            结果 = cls._传送(arg_世, arg_槽, arg_目标, arg_目的地, arg_钩)
            if 结果.已应用:
                用()
                说()
            return 结果
        if arg_物 == 1:
            if not arg_钩.机器人:
                return cls._缺("機器娃娃行動尚未接入")
            用()
            说()
            arg_钩.机器人(arg_槽)
            return 道具结果_类(True, True)
        if arg_物 == 8:
            if not 1 <= arg_目标 <= 6:
                return cls._略("選擇一至六點")
            if not arg_钩.遥控骰:
                return cls._缺("遙控骰子尚未接入")
            if arg_世.玩家[arg_槽].记录.控制标志 == 1:
                说()
            arg_钩.遥控骰(arg_槽, arg_目标)
            用()
            return 道具结果_类(True, True)
        if arg_物 == 10:
            if not arg_钩.恢复上次:
                return cls._缺("時光機尚未接入")
            说()
            if not arg_钩.恢复上次():
                return cls._略("沒有可恢復的回合")
            arg_世.api_活跃玩家()
            用(arg_世.头.当前玩家)
            return 道具结果_类(True, True)
        if not arg_目标:
            return cls._略("已取消")
        if arg_物 == 9:
            if not (
                (2000 < arg_目标 < 4000 and arg_目标 - 2000 < len(arg_世.地产))
                or (4000 < arg_目标 < 6000 and arg_目标 - 4000 < len(arg_世.设施))
            ):
                return cls._略("請選擇房屋")
            if not arg_钩.升级:
                return cls._缺("機器工人尚未接入")
            用()
            说()
            arg_钩.升级(arg_目标)
            return 道具结果_类(True, True)
        if arg_物 in (7, 13):
            if not arg_钩.爆炸:
                return cls._缺("飛彈區域效果尚未接入")
            用()
            说()
            arg_钩.爆炸(arg_目标, arg_物 == 13, arg_槽)
            return 道具结果_类(True, True)
        return cls._缺("未知道具")

    @classmethod
    def api_下车(cls, arg_世: 世界_类, arg_槽: int) -> bool:
        人 = cls._取(arg_世.玩家, arg_槽).记录
        if not 人.交通:
            return False
        if 人.交通 in (1, 2):
            i = 4 if 人.交通 == 1 else 5
            人.道具[i] = (人.道具[i] + 1) & 255
        人.交通, 人.骰数 = 0, 1
        return True
