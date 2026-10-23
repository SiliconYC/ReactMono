# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/cards.cpp；电脑访问策略由独立cards_ai模块处理。
# ◑ 导入
import math
import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Callable

from rich4.calendar import 日期_类
from rich4.events import 事件_类, 事件回调_类
from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.services import 服务_类
from rich4.world import 世界_类
from rich4.world_actors import 地图物件_类


# ◕ 功能
class 目标种类_类(IntEnum):
    """
    原目标种类编号，角色/股票从0起，其它保留原代码。

    更新日志：
    2026.10.23 - 对应CardTargetKind。
    """

    角色, 地产, 股票, 物件, 卡片, 道具 = range(6)


class 卡片状态_类(IntEnum):
    """
    原使用、取消、非法和缺依赖四类结果。

    更新日志：
    2026.10.23 - 对应CardUseStatus。
    """

    已用, 取消, 非法, 缺回调 = range(4)


@dataclass(frozen=True)
class 卡片目标_类:
    """
    原类型/数值目标，可作为人类回调或电脑参数的值快照。

    更新日志：
    2026.10.23 - 对应CardTarget。
    """

    种类: 目标种类_类 = 目标种类_类.角色
    数值: int = 0


@dataclass
class 卡片用法_类:
    """
    卡片编号、主目标及可选抢夺库存/设施类型选择。

    更新日志：
    2026.10.23 - 对应CardUse，None与数值0区别保留。
    """

    卡片: int = 0
    目标: 卡片目标_类 | None = None
    选择: 卡片目标_类 | None = None


@dataclass
class 卡片结果_类:
    """
    原卡片结果，取消或已消费后的非法结果均不假定回滚。

    更新日志：
    2026.10.23 - 对应CardResult。
    """

    状态: 卡片状态_类 = 卡片状态_类.非法
    消息: str = ""

    @property
    def 已使用(self) -> bool:
        return self.状态 == 卡片状态_类.已用


@dataclass
class 卡片前瞻_类:
    """
    原前瞻节点与路口标志，不以几何最短路代替原扫描。

    更新日志：
    2026.10.23 - 对应CardLookahead。
    """

    节点: list[int] = field(default_factory=list)
    经过路口: bool = False


@dataclass
class 电脑卡片记忆_类:
    """
    原电脑卡片选择的三个参数槽，由cards_ai跨次调用保留。

    更新日志：
    2026.10.23 - 对应CardAiMemory。
    """

    参数0: int = 0
    参数1: int = 0
    参数2: int = 0


@dataclass
class 卡片回调_类(事件回调_类):
    """
    继承原事件回调并增加卡片防御、选择、附近扫描和原表现接口。

    更新日志：
    2026.10.23 - 对应CardCallbacks，表现不得消费规则随机流。
    """

    敌意: Callable[[int, int, int], None] | None = None
    转身: Callable[[int], None] | None = None
    改建筑: Callable[[int, bool], None] | None = None
    释放酒店: Callable[[int], None] | None = None
    拍卖地产: Callable[[int, int], bool] | None = None
    选择目标: Callable[[int, list[卡片目标_类]], 卡片目标_类 | None] | None = None
    选择库存: Callable[[int, int], 卡片目标_类 | None] | None = None
    抢得: Callable[[int, int, 卡片目标_类, bool], None] | None = None
    选择设施: Callable[[int], int | None] | None = None
    免付: Callable[[int, int, int], bool] | None = None
    嫁祸: Callable[[int, int], int] | None = None
    移除物件: Callable[[int], None] | None = None
    神明脱离: Callable[[int], None] | None = None
    神明附身: Callable[[int, int], None] | None = None
    休市: Callable[[], bool] | None = None
    前瞻节点: Callable[[int, int], 卡片前瞻_类] | None = None
    附近实例: Callable[[int], list[int]] | None = None
    卡片语音: Callable[[int, int, int, int], None] | None = None
    被动卡: Callable[[int, int], None] | None = None


class 卡片产权_类:
    """
    原Property引用代理；产权/楼层字段实时写世界，造价/基价在创建时取值。

    更新日志：
    2026.10.23 - 保留C++引用成员在回调前后的可见性。
    """

    def __init__(self, arg_世: 世界_类, arg_码: int) -> None:
        self.普通 = 2000 < arg_码 < 4000 and arg_码 - 2000 < len(arg_世.地产)
        self.地 = 事件_类._取(
            arg_世.地产 if self.普通 else arg_世.设施, arg_码 - (2000 if self.普通 else 4000)
        )
        self.经济 = self.地.经济 if self.普通 else self.地
        self.基价, self.造价 = self.地.地价, self.地.每级造价

    @property
    def 业主(self) -> int:
        return self.经济.业主

    @业主.setter
    def 业主(self, arg_值: int) -> None:
        self.经济.业主 = arg_值 & 255

    @property
    def 等级(self) -> int:
        return self.经济.等级

    @等级.setter
    def 等级(self, arg_值: int) -> None:
        self.经济.等级 = arg_值 & 255

    @property
    def 类型(self) -> int:
        return self.经济.连锁 if self.普通 else self.地.类型

    @类型.setter
    def 类型(self, arg_值: int) -> None:
        if self.普通:
            self.经济.连锁 = arg_值 & 255
        else:
            self.地.类型 = arg_值 & 255

    @property
    def 临时(self) -> int:
        return self.地.临时状态

    @临时.setter
    def 临时(self, arg_值: int) -> None:
        self.地.临时状态 = arg_值 & 255

    @property
    def 到期(self) -> int:
        return self.地.到期日

    @到期.setter
    def 到期(self, arg_值: int) -> None:
        self.地.到期日 = arg_值 & 0xFFFFFFFF


class 卡片_类:
    """
    原主动卡片筛选/执行及内部被动反制，电脑访问策略与手动动作分开。

    更新日志：
    2026.10.23 - 对应cards.cpp，随机效果交给原拥有规则的回调。
    """

    @staticmethod
    def _地码(arg_世: 世界_类, arg_码: int) -> bool:
        return 2000 < arg_码 < 4000 and arg_码 - 2000 < len(arg_世.地产)

    @staticmethod
    def _设施码(arg_世: 世界_类, arg_码: int) -> bool:
        return 4000 < arg_码 < 6000 and arg_码 - 4000 < len(arg_世.设施)

    @classmethod
    def _产权码(cls, arg_世: 世界_类, arg_码: int) -> bool:
        return cls._地码(arg_世, arg_码) or cls._设施码(arg_世, arg_码)

    @staticmethod
    def _脚下(arg_世: 世界_类, arg_槽: int) -> int:
        号 = 事件_类._取(arg_世.玩家, arg_槽).记录.节点
        return arg_世.节点[号].类型索引 if 0 <= 号 < len(arg_世.节点) else 0

    @staticmethod
    def _成本(arg_世: 世界_类, arg_码: int) -> int:
        p = 卡片产权_类(arg_世, arg_码)
        return 服务_类._整数(
            服务_类._整数(p.基价 + 服务_类._整数(p.造价 * p.等级)) * arg_世.头.物价
        )

    @staticmethod
    def _要目标(arg_号: int) -> bool:
        return arg_号 in (2, 4, 5, 6, 16, 17) or 9 <= arg_号 <= 14 or 24 <= arg_号 <= 30

    @staticmethod
    def _在场(arg_世: 世界_类, arg_槽: int) -> bool:
        if arg_槽 < 4:
            return 0 <= arg_槽 < len(arg_世.玩家) and bool(
                arg_世.玩家[arg_槽].记录.控制标志 and arg_世.玩家[arg_槽].记录.x
            )
        return (
            arg_槽 < 8
            and not arg_世.特殊角色[arg_槽 - 4].不活跃状态
            and bool(arg_世.特殊角色[arg_槽 - 4].x)
        )

    @staticmethod
    def _可见(arg_实例: list[int], arg_目: 卡片目标_类) -> bool:
        for 码 in arg_实例:
            if arg_目.种类 == 目标种类_类.角色:
                if 码 & 0x8000 and 码 & (1 << arg_目.数值):
                    return True
            elif arg_目.种类 == 目标种类_类.物件:
                if 码 & 0x8000 and (码 >> 8 & 127) == arg_目.数值:
                    return True
            elif 码 == arg_目.数值:
                return True
        return False

    @staticmethod
    def _敌意(arg_世: 世界_类, arg_钩: 卡片回调_类, arg_源: int, arg_目: int, arg_钱: int) -> None:
        if arg_钩.敌意:
            arg_钩.敌意(arg_源, arg_目, arg_钱)
            return
        if (
            arg_源 == arg_目
            or not 0 <= arg_源 < len(arg_世.玩家)
            or not 0 <= arg_目 < len(arg_世.玩家)
        ):
            return
        状 = arg_世.玩家[arg_源].状态
        if arg_钱 < 0 and 状.敌意[arg_目] == 0:
            return
        状.敌意[arg_目] = max(0, 服务_类._整数(状.敌意[arg_目] + arg_钱))
        if arg_钱 > 0 and 状.盟友 == arg_目 + 1:
            状.盟友 = 状.结盟天数 = 0
            arg_世.玩家[arg_目].状态.盟友 = arg_世.玩家[arg_目].状态.结盟天数 = 0

    @staticmethod
    def _低字(arg_值: 扩展数_类) -> int:
        return 服务_类._整数(arg_值.api_双精度位() & 0xFFFFFFFF)

    @classmethod
    def _地产敌意(cls, arg_基: int, arg_级: int) -> int:
        比 = (扩展数_类.api_从值(arg_级) + 扩展数_类.api_从值(2)) / 扩展数_类.api_从值(5)
        return cls._低字(扩展数_类.api_从值(arg_基) * 比)

    @staticmethod
    def _消费(arg_世: 世界_类, arg_槽: int, arg_号: int) -> None:
        服务_类._库存(arg_世, arg_槽).api_用卡(arg_号)

    @classmethod
    def _同街(cls, arg_世: 世界_类, arg_码: int) -> list[int]:
        if cls._设施码(arg_世, arg_码):
            return [arg_码]
        名 = 事件_类._取(arg_世.地产, arg_码 - 2000).经济.街道名.split(b"\0", 1)[0]
        return [
            2000 + i
            for i, 地 in enumerate(arg_世.地产[1:], 1)
            if 地.经济.街道名.split(b"\0", 1)[0] == 名
        ]

    @staticmethod
    def _可请(arg_物: 地图物件_类) -> bool:
        return bool(
            arg_物.种类
            and ((arg_物.种类 <= 12 and arg_物.种类 != 11) or arg_物.种类 == 15)
            and not arg_物.附身玩家
            and arg_物.节点
        )

    @classmethod
    def _最近神(cls, arg_世: 世界_类, arg_槽: int, arg_钩: 卡片回调_类) -> int | None:
        if not arg_钩.附近实例:
            return None
        最小, 选 = 10000.0, None
        for 码 in arg_钩.附近实例(arg_槽):
            号 = 码 >> 8 & 127
            if not 码 & 0x8000 or not 1 <= 号 <= len(arg_世.物件):
                continue
            物 = arg_世.物件[号 - 1]
            if not cls._可请(物) or not 0 <= 物.节点 < len(arg_世.节点):
                continue
            节, 人 = arg_世.节点[物.节点], arg_世.玩家[arg_槽].记录
            dx, dy = 节.x - 人.x, 节.y - 人.y
            平方 = 服务_类._整数(服务_类._整数(dx * dx) + 服务_类._整数(dy * dy))
            距 = struct.unpack("<f", struct.pack("<f", math.sqrt(平方) if 平方 >= 0 else math.nan))[
                0
            ]
            if 距 < 最小:
                最小, 选 = 距, 号
        return 选

    @staticmethod
    def _梦游(arg_世: 世界_类, arg_槽: int, arg_天: int, arg_累计: bool) -> None:
        人 = 事件_类._取(arg_世.玩家, arg_槽)
        人.状态.梦游天数 = arg_天
        if arg_累计:
            人.状态.冬眠总天数 = (人.状态.冬眠总天数 + 5) & 255
        人.状态.标志102, 人.状态.标志103 = 人.记录.交通, 人.记录.骰数
        if 人.记录.交通 in (1, 2):
            i = 4 if 人.记录.交通 == 1 else 5
            人.记录.道具[i] = (人.记录.道具[i] + 1) & 255
        if 人.记录.交通 or not arg_累计:
            人.记录.交通, 人.记录.骰数 = 0, 1

    @staticmethod
    def _解盟(arg_世: 世界_类, arg_槽: int) -> None:
        状 = arg_世.玩家[arg_槽].状态
        if 0 < 状.盟友 <= len(arg_世.玩家):
            另 = arg_世.玩家[状.盟友 - 1].状态
            另.盟友 = 另.结盟天数 = 0
        状.盟友 = 状.结盟天数 = 0

    @staticmethod
    def _说(arg_钩: 卡片回调_类, arg_槽: int, arg_行: int, arg_卡: int, arg_情绪: int) -> None:
        if arg_钩.卡片语音:
            arg_钩.卡片语音(arg_槽, arg_行, arg_卡, arg_情绪)

    @staticmethod
    def api_主动(arg_号: int) -> bool:
        return 1 <= arg_号 <= 30 and not 18 <= arg_号 <= 21

    @classmethod
    def api_合法目标(
        cls, arg_世: 世界_类, arg_槽: int, arg_号: int, arg_钩: 卡片回调_类
    ) -> list[卡片目标_类]:
        目 = []
        if not 0 <= arg_槽 < len(arg_世.玩家) or not cls.api_主动(arg_号):
            return 目
        if arg_号 in (24, 25):
            if arg_钩.休市 and arg_钩.休市():
                return 目
            return [卡片目标_类(目标种类_类.股票, i) for i in range(len(arg_世.股票))]
        if arg_号 in (2, 6, 13, 14, 16, 17, 26, 29, 30):
            for 槽 in range(8):
                if not cls._在场(arg_世, 槽):
                    continue
                if arg_号 in (2, 13, 26, 29) and (槽 >= 4 or 槽 == arg_槽):
                    continue
                if arg_号 in (16, 17) and 槽 == arg_槽:
                    continue
                目.append(卡片目标_类(目标种类_类.角色, 槽))
        elif arg_号 in (4, 5, 9, 10, 11, 12, 27, 28):
            脚 = cls._脚下(arg_世, arg_槽)
            for 类 in range(2):
                表 = arg_世.设施 if 类 else arg_世.地产
                for i in range(1, len(表)):
                    码 = (4000 if 类 else 2000) + i
                    if arg_号 in (4, 5) and (
                        码 == 脚 or not (cls._设施码(arg_世, 脚) if 类 else cls._地码(arg_世, 脚))
                    ):
                        continue
                    p = 卡片产权_类(arg_世, 码)
                    if arg_号 in (11, 12) and (p.业主 == arg_槽 + 1 or not p.等级):
                        continue
                    目.append(卡片目标_类(目标种类_类.地产, 码))
            if arg_号 == 12:
                目.extend(
                    卡片目标_类(目标种类_类.物件, i + 1)
                    for i, 物 in enumerate(arg_世.物件)
                    if 物.节点 and 16 <= 物.种类 <= 18
                )
        if arg_钩.附近实例:
            实 = arg_钩.附近实例(arg_槽)
            目 = [项 for 项 in 目 if cls._可见(实, 项)]
        return 目

    @classmethod
    def api_使用(
        cls,
        arg_世: 世界_类,
        arg_随机: 随机数_类,
        arg_槽: int,
        arg_用: 卡片用法_类,
        arg_钩: 卡片回调_类,
    ) -> 卡片结果_类:
        世, 槽, 用, 钩 = arg_世, arg_槽, arg_用, arg_钩
        号 = 用.卡片
        if (
            not 0 <= 槽 < len(世.玩家)
            or not 世.玩家[槽].记录.控制标志
            or not cls.api_主动(号)
            or 号 not in 世.玩家[槽].记录.卡片
        ):
            return 卡片结果_类(卡片状态_类.非法, "Card is not an active card in this hand")
        选 = 用.目标
        if 号 in (24, 25):
            if not 钩.休市:
                return 卡片结果_类(卡片状态_类.缺回调, "Stock market calendar is required")
            if 钩.休市():
                return 卡片结果_类(卡片状态_类.取消, "Stock market is closed")
        if cls._要目标(号):
            项 = cls.api_合法目标(
                世, 槽, 号, 钩 if 世.玩家[槽].记录.控制标志 == 1 else 卡片回调_类()
            )
            if not 项:
                return 卡片结果_类(卡片状态_类.取消, "No legal target")
            if 选 is None:
                if 世.玩家[槽].记录.控制标志 != 1:
                    return 卡片结果_类(卡片状态_类.取消, "Computer card parameter has no target")
                if not 钩.选择目标:
                    return 卡片结果_类(卡片状态_类.缺回调, "Target selection is required")
                选 = 钩.选择目标(号, 项)
                if 选 is None:
                    return 卡片结果_类(卡片状态_类.取消, "Target selection cancelled")
            if 选 not in 项:
                return 卡片结果_类(卡片状态_类.非法, "Illegal card target")
        目 = 选.数值 if 选 is not None else 0
        指, 脚, 人 = 世.头.物价, cls._脚下(世, 槽), 世.玩家[槽]

        def 已用() -> 卡片结果_类:
            return 卡片结果_类(卡片状态_类.已用, "Card used")

        def 缺() -> 卡片结果_类:
            return 卡片结果_类(卡片状态_类.缺回调, "Required card rule callback is unavailable")

        if 号 == 1:
            总, 数 = 0, 0
            for 另 in 世.玩家:
                if 另.记录.控制标志:
                    总 = 服务_类._整数(总 + 另.记录.现金)
                    数 += 1
            均 = 事件_类._除(总, 数)
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 3)
            for i, 另 in enumerate(世.玩家):
                if 另.记录.控制标志:
                    if 另.记录.现金 > 均:
                        cls._敌意(世, 钩, i, 槽, 事件_类._除(服务_类._整数(另.记录.现金 - 均), 100))
                    另.记录.现金 = 均
            return 已用()
        if 号 == 2:
            均 = 事件_类._除(服务_类._整数(人.记录.现金 + 世.玩家[目].记录.现金), 2)
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 3)
            if 世.玩家[目].记录.现金 > 均:
                cls._敌意(
                    世, 钩, 目, 槽, 事件_类._除(服务_类._整数(世.玩家[目].记录.现金 - 均), 100)
                )
            人.记录.现金 = 世.玩家[目].记录.现金 = 均
            cls._说(钩, 目, 2, 号, 1)
            return 已用()
        if 号 == 3:
            if not cls._产权码(世, 脚):
                return 卡片结果_类(卡片状态_类.取消, "Standing property cannot be purchased")
            p = 卡片产权_类(世, 脚)
            if not p.业主 or p.业主 == 槽 + 1 or cls._成本(世, 脚) > 人.记录.现金:
                return 卡片结果_类(卡片状态_类.取消, "Standing property cannot be purchased")
            if not 钩.付款:
                return 缺()
            卖, 价 = p.业主 - 1, cls._成本(世, 脚)
            cls._敌意(世, 钩, 卖, 槽, cls._地产敌意(服务_类._整数(p.基价 * 指), p.等级))
            cls._说(钩, 槽, 0, 号, 3)
            p.业主 = 槽 + 1
            if 0 < 世.租约模式 < 6:
                间隔 = (0, 0x20000, 0x10000, 0x600, 0x300, 0x100)[世.租约模式]
                日, 月, 年 = 世.头.日期
                p.到期 = 日期_类.api_打包间隔(年 << 16 | 月 << 8 | 日, 间隔)
            钩.付款(槽, 卖, 价, 0)
            cls._说(钩, 卖, 2, 号, 1)
            cls._消费(世, 槽, 号)
            return 已用()
        if 号 in (4, 5):
            a, b = 卡片产权_类(世, 脚), 卡片产权_类(世, 目)
            主a, 主b, 级a, 级b = a.业主, b.业主, a.等级, b.等级
            得b = 主a == 槽 + 1 and 主b != 槽 + 1 and 级b >= 级a
            得a = 主a != 槽 + 1 and 主b == 槽 + 1 and 级a >= 级b
            if 得a or 得b:
                cls._说(钩, 槽, 0, 号, 3)
            if 号 == 4:
                a.业主, b.业主 = b.业主, a.业主
            else:
                a.等级, b.等级 = b.等级, a.等级
                a.类型, b.类型 = b.类型, a.类型
            if 得b and 主b:
                cls._说(钩, 主b - 1, 2, 号, 2)
            elif 得a and 主a:
                cls._说(钩, 主a - 1, 2, 号, 2)
            cls._消费(世, 槽, 号)
            return 已用()
        if 号 == 6:
            if not 钩.转身:
                return 缺()
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 3)
            钩.转身(目)
            if 目 == 槽:
                cls._说(钩, 槽, 1, 号, 0)
            elif 目 < 4:
                cls._说(钩, 目, 2, 号, 2)
            return 已用()
        if 号 == 7:
            if not cls._产权码(世, 脚) or not 卡片产权_类(世, 脚).等级:
                return 卡片结果_类(卡片状态_类.取消, "Standing property has no building")
            cls._说(钩, 槽, 0, 号, 3)
            p = 卡片产权_类(世, 脚)
            if cls._地码(世, 脚):
                p.类型 ^= 1
                if p.类型 and p.等级 > 1:
                    p.等级 = 1
            else:
                if 用.选择 is not None:
                    类 = 用.选择.数值 & 255
                elif 钩.选择设施:
                    类 = 钩.选择设施(槽)
                else:
                    return 缺()
                if 类 is None:
                    return 卡片结果_类(卡片状态_类.取消, "Reconstruction cancelled")
                if 类 > 4:
                    return 卡片结果_类(卡片状态_类.非法, "Invalid facility type")
                p.类型 = 类
                if p.类型 in (0, 3) and p.等级 > 1:
                    p.等级 = 1
            cls._消费(世, 槽, 号)
            return 已用()
        if 号 == 8:
            if not cls._产权码(世, 脚):
                return 卡片结果_类(卡片状态_类.取消, "No standing property")
            if not 钩.拍卖地产:
                return 缺()
            p = 卡片产权_类(世, 脚)
            if p.业主:
                cls._敌意(世, 钩, p.业主 - 1, 槽, cls._地产敌意(服务_类._整数(p.基价 * 指), p.等级))
            cls._说(钩, 槽, 0, 号, 3)
            if p.业主 and p.业主 != 槽 + 1:
                cls._说(钩, p.业主 - 1, 2, 号, 1)
            if not 钩.拍卖地产(脚, 槽):
                p.业主 = p.到期 = 0
            cls._消费(世, 槽, 号)
            return 已用()
        if 号 in (9, 10, 11, 12):
            if 选.种类 == 目标种类_类.物件:
                if not 钩.移除物件:
                    return 缺()
                cls._消费(世, 槽, 号)
                cls._说(钩, 槽, 0, 号, 0)
                钩.移除物件(目)
                return 已用()
            if cls._设施码(世, 目) and 号 == 9 and not 钩.改建筑:
                return 缺()
            if cls._设施码(世, 目) and 号 != 9 and 卡片产权_类(世, 目).等级 and not 钩.释放酒店:
                return 缺()
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 3 if 号 == 9 else 0)
            受 = 卡片产权_类(世, 目).业主
            码组 = cls._同街(世, 目) if 号 in (9, 10) else [目]
            for 码 in 码组:
                p = 卡片产权_类(世, 码)
                if 号 == 9:
                    if cls._设施码(世, 码):
                        钩.改建筑(码, True)
                    elif p.等级 < 5:
                        if not p.类型:
                            p.等级 += 1
                        elif not p.等级:
                            p.等级 = 1
                else:
                    if p.业主:
                        cls._敌意(
                            世,
                            钩,
                            p.业主 - 1,
                            槽,
                            服务_类._整数((30 if 号 == 12 else 30 * p.等级) * 指),
                        )
                    旧 = p.等级
                    if 号 == 12 and (not p.类型 or cls._设施码(世, 码)):
                        p.等级 -= 1
                    else:
                        p.等级 = 0
                    if not p.等级:
                        p.类型 = 0
                    if cls._设施码(世, 码) and 旧 and not p.等级:
                        钩.释放酒店(码)
            if 号 in (11, 12) and 受:
                cls._说(钩, 受 - 1, 2, 号, 1)
            return 已用()
        if 号 == 13:
            cls._说(钩, 槽, 0, 号, 3)
            项 = 用.选择
            if 项 is None:
                if not 钩.选择库存:
                    return 缺()
                项 = 钩.选择库存(槽, 目)
            if 项 is None:
                return 卡片结果_类(卡片状态_类.取消, "Inventory selection cancelled")
            包 = 服务_类._库存(世, 目)
            if 项.种类 == 目标种类_类.卡片 and 1 <= 项.数值 <= 30 and 包.api_有卡(项.数值):
                cls._消费(世, 目, 项.数值)
                服务_类._库存(世, 槽).api_收卡(项.数值)
            elif (
                项.种类 == 目标种类_类.道具
                and 1 <= 项.数值 <= 13
                and 世.玩家[目].记录.道具[项.数值 - 1]
            ):
                包.api_用道具(项.数值)
                服务_类._库存(世, 槽).api_收道具(项.数值)
            else:
                return 卡片结果_类(卡片状态_类.非法, "Item is absent from target inventory")
            cls._敌意(世, 钩, 目, 槽, 服务_类.卡价[项.数值 - 1])
            cls._消费(世, 槽, 号)
            if 钩.抢得:
                钩.抢得(槽, 目, 项, 用.选择 is not None)
            cls._说(钩, 目, 2, 号, 1)
            return 已用()
        if 号 in (14, 30):
            cls._消费(世, 槽, 号)
            if 目 != 槽:
                cls._说(钩, 槽, 0, 号, 3)
            if 目 < 4:
                cls._说(钩, 目, 1 if 目 == 槽 else 2, 号, 3 if 目 == 槽 else 2)
            状 = 世.玩家[目].状态 if 目 < 4 else 世.特殊角色[目 - 4]
            if 号 == 14:
                状.停留天数 = (128 if 目 == 槽 else 1) if 目 < 4 else 1
            else:
                状.龟行天数 = (2 if 目 == 槽 else 3) if 目 < 4 else 3
            return 已用()
        if 号 == 15:
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 3)
            for i, 另 in enumerate(世.玩家):
                if i == 槽 or not 另.记录.控制标志 or not 另.记录.x or 另.状态.酒店天数:
                    continue
                cls._敌意(世, 钩, i, 槽, 服务_类._整数(150 * 指))
                另.状态.梦游天数, 另.状态.睡眠天数 = 0, 5
                另.状态.冬眠总天数 = (另.状态.冬眠总天数 + 5) & 255
            for 另 in 世.特殊角色[:4]:
                if not 另.不活跃状态:
                    另.梦游天数, 另.睡眠天数 = 0, 5
            return 已用()
        if 号 in (16, 17):
            if 号 == 17 and not 钩.监狱:
                return 缺()
            if (
                目 < 4
                and (19 in 世.玩家[目].记录.卡片 or 21 in 世.玩家[目].记录.卡片)
                and not 钩.防御
            ):
                return 缺()
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 3)
            if 目 >= 4:
                if 号 == 17:
                    钩.监狱(目, 5)
                elif not 世.特殊角色[目 - 4].睡眠天数:
                    世.特殊角色[目 - 4].梦游天数 = 5
                return 已用()
            if 号 == 16 and 世.玩家[目].状态.睡眠天数:
                return 已用()
            cls._敌意(世, 钩, 目, 槽, 服务_类._整数(150 * 指))
            转 = 钩.防御(目) if 钩.防御 else 目
            if 转 < 0:
                return 已用()
            if 转 >= len(世.玩家):
                return 卡片结果_类(卡片状态_类.非法, "Defense returned invalid player")
            if 号 == 16:
                if 钩.语音:
                    钩.语音(转, 21)
                cls._梦游(世, 转, 4 if 转 == 槽 else 5, True)
            else:
                钩.监狱(转, 4 if 转 == 槽 else 5)
                cls._说(钩, 转, 2, 号, 1)
            if 转 == 目 and 18 in 世.玩家[目].记录.卡片:
                if 钩.被动卡:
                    钩.被动卡(目, 18)
                cls._消费(世, 目, 18)
                cls._说(钩, 目, 0, 18, 0)
                cls._说(钩, 槽, 2, 18, 2)
                if 号 == 16:
                    cls._梦游(世, 槽, 5, False)
                else:
                    钩.监狱(槽, 5)
            return 已用()
        if 号 == 22:
            炸, 神 = 人.状态.附身炸弹, 人.状态.神明信息
            类 = 世.物件[神 - 1].种类 if 0 < 神 <= len(世.物件) else 0
            坏 = 类 in (5, 6, 7, 8, 10, 15)
            if not 炸 and not 坏:
                return 卡片结果_类(卡片状态_类.取消, "No attached bomb or removable god")
            if (炸 and not 钩.移除物件) or (坏 and not 钩.神明脱离):
                return 缺()
            if 炸:
                钩.移除物件(炸)
            if 坏:
                钩.神明脱离(槽)
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 0)
            return 已用()
        if 号 == 23:
            if not 钩.附近实例 or not 钩.神明附身:
                return 缺()
            物 = cls._最近神(世, 槽, 钩)
            if 物 is None:
                return 卡片结果_类(卡片状态_类.取消, "No nearby attachable god")
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 0)
            钩.神明附身(槽, 物)
            return 已用()
        if 号 in (24, 25):
            if not 钩.更新股票:
                return 缺()
            cls._说(钩, 槽, 0, 号, 0)
            旧 = struct.unpack("<f", struct.pack("<I", 世.股票[目].浮点位[2]))[0]
            世.股票[目].新闻走势 = 32 if 号 == 24 else 2
            钩.更新股票(目 + 1)
            if 号 == 25:
                新 = struct.unpack("<f", struct.pack("<I", 世.股票[目].浮点位[2]))[0]
                try:
                    差 = struct.unpack("<f", struct.pack("<f", 旧 - 新))[0]
                except OverflowError:
                    差 = math.copysign(math.inf, 旧 - 新)
                for i, 另 in enumerate(世.玩家):
                    数 = 另.持仓[目].数量
                    if 数:
                        值 = (
                            扩展数_类.api_从值(数)
                            * 扩展数_类.api_从值(差)
                            / 扩展数_类.api_从值(200)
                        )
                        cls._敌意(世, 钩, i, 槽, cls._低字(值))
            cls._消费(世, 槽, 号)
            return 已用()
        if 号 == 26:
            if not 钩.付款:
                return 缺()
            if 20 in 世.玩家[目].记录.卡片 and not 钩.免付:
                return 缺()
            税 = 事件_类._除(世.玩家[目].记录.现金, 5)
            if 19 in 世.玩家[目].记录.卡片 and 税 > 2000 and not 钩.嫁祸:
                return 缺()
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 0)
            cls._敌意(世, 钩, 目, 槽, 事件_类._除(税, 100))
            if 20 in 世.玩家[目].记录.卡片 and 钩.免付(目, 槽, 税):
                return 已用()
            付 = 目
            if 19 in 世.玩家[目].记录.卡片 and 税 > 2000:
                转 = 钩.嫁祸(目, 2)
                if 转 != -1:
                    付 = 转
            if 付 != 槽:
                钩.付款(付, 槽, 事件_类._除(事件_类._取(世.玩家, 付).记录.现金, 5), 0)
                cls._说(钩, 付, 2, 号, 2)
            return 已用()
        if 号 in (27, 28):
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 0)
            for 码 in cls._同街(世, 目):
                卡片产权_类(世, 码).临时 = 80 if 号 == 27 else 81
                if 号 == 28 and cls._设施码(世, 码) and 世.设施[码 - 4000].类型 == 4:
                    世.设施[码 - 4000].标志30 = 0
            return 已用()
        if 号 == 29:
            cls._消费(世, 槽, 号)
            cls._说(钩, 槽, 0, 号, 3)
            cls._解盟(世, 槽)
            cls._解盟(世, 目)
            人.状态.盟友, 人.状态.结盟天数 = 目 + 1, 7
            世.玩家[目].状态.盟友, 世.玩家[目].状态.结盟天数 = 槽 + 1, 7
            cls._说(钩, 目, 2, 号, 0)
            return 已用()
        return 卡片结果_类(卡片状态_类.非法, "Passive or unknown card")
