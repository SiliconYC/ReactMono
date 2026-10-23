# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/cards_ai.cpp；保留原UI遍历参数与跨次调用记忆。
# ◑ 导入
import math

from rich4.cards import 卡片回调_类, 卡片用法_类, 卡片目标_类, 电脑卡片记忆_类, 目标种类_类
from rich4.events import 事件_类
from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.services import 服务_类
from rich4.stocks import 股市_类, 走势_类
from rich4.tools_ai import 道具电脑_类
from rich4.world import 世界_类
from rich4.world_stocks import 持仓_类


# ◕ 功能
class 卡片电脑_类:
    """
    原三十卡谓词与八槽访问，参数未赋值时保留之前调用的记忆。

    更新日志：
    2026.10.23 - 不替换原目标省略、遍历索引或重复实例行为。
    """

    攻击性 = (
        2,
        2,
        1,
        0,
        0,
        0,
        0,
        1,
        0,
        2,
        2,
        1,
        2,
        0,
        2,
        1,
        2,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1,
        1,
        0,
        1,
        0,
        0,
    )
    _地码 = staticmethod(道具电脑_类._地码)
    _设施码 = staticmethod(道具电脑_类._设施码)
    _业主 = staticmethod(道具电脑_类._业主)
    _层 = staticmethod(道具电脑_类._层)
    _通行费 = staticmethod(道具电脑_类._通行费)
    _自己码 = staticmethod(道具电脑_类._自己码)
    _回绕 = staticmethod(股市_类._回绕)

    @staticmethod
    def _名(arg_名: bytes) -> bytes:
        return arg_名.split(b"\0", 1)[0]

    @staticmethod
    def _公司码(arg_世: 世界_类, arg_码: int) -> bool:
        return 6000 < arg_码 < 8000 and arg_码 - 6000 < len(arg_世.公司)

    @staticmethod
    def _节点码(arg_世: 世界_类, arg_节: int) -> int:
        return arg_世.节点[arg_节].类型索引 if 0 <= arg_节 < len(arg_世.节点) else 0

    @classmethod
    def _脚下(cls, arg_世: 世界_类, arg_槽: int) -> int:
        return cls._节点码(arg_世, arg_世.玩家[arg_槽].记录.节点)

    @classmethod
    def _基价(cls, arg_世: 世界_类, arg_码: int) -> int:
        return (
            arg_世.地产[arg_码 - 2000].地价
            if cls._地码(arg_世, arg_码)
            else arg_世.设施[arg_码 - 4000].地价
        )

    @classmethod
    def _敌手(cls, arg_世: 世界_类, arg_槽: int) -> int:
        选, 最 = -1, 0
        for i, 人 in enumerate(arg_世.玩家):
            if i != arg_槽 and 人.记录.控制标志:
                值 = cls._回绕(arg_世.玩家[arg_槽].状态.敌意[i])
                if 值 > 最:
                    选, 最 = i, 值
        return 选

    @staticmethod
    def _扫描玩家(arg_世: 世界_类, arg_槽: int, arg_扫: list[int]) -> list[int]:
        return [
            i
            for 码 in arg_扫
            if 码 & 0x8000
            for i, 人 in enumerate(arg_世.玩家)
            if i != arg_槽 and 码 & (1 << i) and 人.记录.控制标志
        ]

    @classmethod
    def _想要(cls, arg_世: 世界_类, arg_槽: int, arg_敌: int, arg_码: int) -> bool:
        if arg_敌 < 0:
            return False
        if cls._地码(arg_世, arg_码):
            p = arg_世.地产[arg_码 - 2000].经济
            if p.业主 and p.业主 != arg_槽 + 1 and p.等级:
                if any(
                    cls._名(另.经济.街道名) == cls._名(p.街道名) and 另.经济.业主 == arg_槽 + 1
                    for 另 in arg_世.地产[1:]
                ):
                    return True
            return p.业主 == arg_敌 + 1 and p.等级 >= 2
        return (
            cls._设施码(arg_世, arg_码)
            and bool(cls._业主(arg_世, arg_码))
            and cls._业主(arg_世, arg_码) != arg_槽 + 1
            and bool(cls._层(arg_世, arg_码))
        )

    @classmethod
    def _购价(cls, arg_世: 世界_类, arg_码: int) -> int:
        p = arg_世.地产[arg_码 - 2000] if cls._地码(arg_世, arg_码) else arg_世.设施[arg_码 - 4000]
        return cls._回绕(
            cls._回绕(cls._基价(arg_世, arg_码) + cls._回绕(cls._层(arg_世, arg_码) * p.每级造价))
            * arg_世.头.物价
        )

    @classmethod
    def _怪兽(cls, arg_世: 世界_类, arg_槽: int, arg_扫: list[int]) -> int:
        最 = [[0] * 4 for _ in range(2)]

        def 更好(arg_码: int, arg_旧: int) -> bool:
            return (
                not arg_旧
                or cls._层(arg_世, arg_码) > cls._层(arg_世, arg_旧)
                or (
                    cls._层(arg_世, arg_码) == cls._层(arg_世, arg_旧)
                    and cls._基价(arg_世, arg_码) > cls._基价(arg_世, arg_旧)
                )
            )

        for 码 in arg_扫:
            设 = cls._设施码(arg_世, 码)
            if not 设 and not cls._地码(arg_世, 码):
                continue
            主 = cls._业主(arg_世, 码)
            if not 主 or 主 == arg_槽 + 1 or 主 > 4 or cls._层(arg_世, 码) < 3:
                continue
            if 更好(码, 最[int(设)][主 - 1]):
                最[int(设)][主 - 1] = 码
        敌 = cls._敌手(arg_世, arg_槽)
        if 敌 >= 0 and (最[1][敌] or 最[0][敌]):
            return 最[1][敌] or 最[0][敌]
        选 = [0, 0]
        for i, 人 in enumerate(arg_世.玩家):
            if i == arg_槽 or not 人.记录.控制标志:
                continue
            for 类 in range(2):
                码 = 最[类][i]
                if 码 and (类 or cls._层(arg_世, 码) >= 4) and 更好(码, 选[类]):
                    选[类] = 码
        return 选[1] or 选[0]

    @classmethod
    def _最近神(cls, arg_世: 世界_类, arg_槽: int, arg_扫: list[int]) -> int | None:
        最, 选 = 10000.0, None
        for 码 in arg_扫:
            号 = 码 >> 8 & 127
            if not 码 & 0x8000 or not 0 < 号 <= len(arg_世.物件):
                continue
            物 = arg_世.物件[号 - 1]
            if (
                not 0 < 物.节点 < len(arg_世.节点)
                or 物.附身玩家
                or not ((物.种类 <= 12 and 物.种类 != 11) or 物.种类 == 15)
            ):
                continue
            节, 人 = arg_世.节点[物.节点], arg_世.玩家[arg_槽].记录
            dx, dy = 节.x - 人.x, 节.y - 人.y
            方 = cls._回绕(cls._回绕(dx * dx) + cls._回绕(dy * dy))
            距 = 股市_类._浮点(股市_类._位(math.sqrt(方))) if 方 >= 0 else math.nan
            if 距 < 最:
                最, 选 = 距, 号
        return 选

    @staticmethod
    def _友善号(arg_号: int) -> bool:
        return arg_号 in (1, 2, 3, 4, 12)

    @staticmethod
    def _持仓成本(arg_持: 持仓_类) -> int:
        return (
            扩展数_类.api_从值(arg_持.数量) * 扩展数_类.api_从值(股市_类._浮点(arg_持.成本位))
        ).api_整数()

    @classmethod
    def _谓词(
        cls,
        arg_世: 世界_类,
        arg_随: 随机数_类,
        arg_槽: int,
        arg_卡: int,
        arg_钩: 卡片回调_类,
        arg_记: 电脑卡片记忆_类,
        arg_遍历末: int,
    ) -> bool:
        世, 随, 槽, 卡, 钩, 记 = arg_世, arg_随, arg_槽, arg_卡, arg_钩, arg_记
        人, 当前, 敌, 指 = 世.玩家[槽], cls._脚下(世, 槽), cls._敌手(世, 槽), 世.头.物价
        自, 钱, 状 = 槽 + 1, 人.记录.现金, 人.状态

        def 扫描() -> list[int]:
            表 = 钩.附近实例(槽) if 钩.附近实例 else []
            记.参数2 = len(表) & 0xFFFFFFFF
            return 表

        def 目标(arg_码: int) -> bool:
            记.参数0 = arg_码 & 0xFFFFFFFF
            return True

        def 同街(arg_地: int, arg_另: int) -> bool:
            return cls._名(世.地产[arg_地].经济.街道名) == cls._名(世.地产[arg_另].经济.街道名)

        地码, 设施码 = cls._地码, cls._设施码
        if 卡 == 1:
            总, 数 = 0, 0
            for p in 世.玩家:
                if p.记录.控制标志:
                    总, 数 = cls._回绕(总 + p.记录.现金), 数 + 1
            return (
                bool(数) and 事件_类._除(总, 数) > cls._回绕(钱 * 10) and 钱 < cls._回绕(指 * 3000)
            )
        if 卡 in (2, 26):
            候 = cls._扫描玩家(世, 槽, 扫描())

            def 合格(arg_i: int, arg_阈: int, arg_倍: int) -> bool:
                额 = 世.玩家[arg_i].记录.现金
                return 额 > cls._回绕(指 * arg_阈) and (卡 == 26 or 额 > cls._回绕(钱 * arg_倍))

            if 敌 >= 0 and 敌 in 候 and 合格(敌, 30000, 2):
                return 目标(cls._自己码(敌))
            有 = False
            for i in range(len(世.玩家)):
                if i in 候 and 合格(i, 50000, 3):
                    有 = 目标(cls._自己码(i))
            return 有
        if 卡 == 3:
            return cls._想要(世, 槽, 敌, 当前) and cls._购价(世, 当前) < 钱
        if 卡 == 4:
            if (
                (not 地码(世, 当前) and not 设施码(世, 当前))
                or cls._业主(世, 当前) != 自
                or cls._层(世, 当前) > 1
            ):
                return False
            if 地码(世, 当前) and any(
                i != 当前 - 2000 and 同街(i, 当前 - 2000) and p.经济.业主 == 自
                for i, p in enumerate(世.地产[1:], 1)
            ):
                return False
            for 码 in 扫描():
                if not (地码(世, 码) if 地码(世, 当前) else 设施码(世, 码)):
                    continue
                if 地码(世, 当前) and 同街(码 - 2000, 当前 - 2000):
                    continue
                if (
                    cls._基价(世, 码) > cls._基价(世, 当前)
                    and cls._层(世, 码) > cls._层(世, 当前)
                    and cls._想要(世, 槽, 敌, 码)
                ):
                    return 目标(码)
            return False
        if 卡 in (5, 6, 18, 19, 20, 21):
            return False
        if 卡 == 7:
            if 地码(世, 当前):
                p = 世.地产[当前 - 2000].经济
                if p.业主 != 自:
                    return False
                if p.连锁:
                    return any(
                        i != 当前 - 2000 and 同街(i, 当前 - 2000) and q.经济.业主 == 自
                        for i, q in enumerate(世.地产[1:], 1)
                    )
                if p.等级 != 1:
                    return False
                if not 状.救援策略:
                    return True
                return not any(
                    i != 当前 - 2000 and 同街(i, 当前 - 2000) and q.经济.业主 in (0, 自)
                    for i, q in enumerate(世.地产[1:], 1)
                )
            if not 设施码(世, 当前):
                return False
            p = 世.设施[当前 - 4000]
            if p.业主 == 自 and not p.类型 and p.等级 == 1:
                记.参数0 = 随.api_下一个() % 4 + 1
                return True
            if (
                p.业主
                and p.业主 != 自
                and p.类型
                and (p.等级 >= 3 or (p.业主 == 敌 + 1 and p.等级 >= 2))
            ):
                return 目标(0)
            return False
        if 卡 == 8:
            return (
                (地码(世, 当前) or 设施码(世, 当前))
                and bool(cls._业主(世, 当前))
                and (
                    (cls._业主(世, 当前) != 自 and cls._层(世, 当前) >= 3)
                    or (cls._业主(世, 当前) == 敌 + 1 and cls._层(世, 当前) >= 2)
                )
            )
        if 卡 == 9:
            街: dict[bytes, list[int]] = {}
            for 码 in 扫描():
                if 地码(世, 码):
                    p = 世.地产[码 - 2000].经济
                    if p.业主 == 自 and not p.连锁 and p.等级 < 5:
                        名 = cls._名(p.街道名)
                        if 名 not in 街:
                            街[名] = [码, 1]
                        else:
                            街[名][1] = (街[名][1] + 1) & 65535
            候 = [码 for 码, 数 in 街.values() if 数 >= 3]
            return bool(候) and 目标(候[随.api_下一个() % len(候)])
        if 卡 == 10:
            街 = {}
            for 码 in 扫描():
                if not 地码(世, 码):
                    continue
                p = 世.地产[码 - 2000].经济
                if p.连锁 or not 1 <= p.业主 <= 4:
                    continue
                名 = cls._名(p.街道名)
                if 名 not in 街:
                    街[名] = [码, [0] * 4, [0] * 4]
                _, 层, 数 = 街[名]
                层[p.业主 - 1] = (层[p.业主 - 1] + p.等级) & 255
                数[p.业主 - 1] = (数[p.业主 - 1] + 1) & 255
            for 码, 层, 数 in 街.values():
                if 敌 >= 0:
                    if 数[敌] >= 2 and 层[敌] >= 7 and 层[槽] <= 1:
                        return 目标(码)
                elif not 层[槽]:
                    活 = [i for i, p in enumerate(世.玩家) if i != 槽 and p.记录.控制标志]
                    if sum(数[i] for i in 活) >= 3 and sum(层[i] for i in 活) >= 9:
                        return 目标(码)
            return False
        if 卡 in (11, 12):
            表 = 扫描()
            兽 = cls._怪兽(世, 槽, 表)
            if 兽:
                return 目标(兽)
            if 卡 == 11:
                return False
            for 码 in 表:
                if 地码(世, 码):
                    p = 世.地产[码 - 2000].经济
                    if 状.救援策略 and p.业主 and p.业主 != 自 and p.连锁:
                        if (
                            sum(q.经济.业主 == p.业主 and bool(q.经济.连锁) for q in 世.地产[1:])
                            >= 4
                        ):
                            return 目标(码)
                elif 设施码(世, 码):
                    p = 世.设施[码 - 4000]
                    if 人.记录.交通 & 3 and p.类型 == 3 and p.等级 == 1 and p.业主 != 自:
                        return 目标(码)
                elif 码 & 0x8000:
                    号 = 码 >> 8 & 63
                    if not 0 < 号 <= len(世.物件):
                        continue
                    p = 世.物件[号 - 1]
                    地 = cls._节点码(世, p.节点)
                    if not 地码(世, 地) and not 设施码(世, 地):
                        continue
                    主 = cls._业主(世, 地)
                    if (p.种类 == 16 and 主 and 主 != 自) or (p.种类 == 17 and 主 == 自):
                        return 目标(码)
            return False
        if 卡 == 13:
            候 = cls._扫描玩家(世, 槽, 扫描())

            def 最佳(arg_人: int, arg_低: int, arg_精确: bool) -> int:
                选, 价 = 0, 0
                for 号 in 世.玩家[arg_人].记录.卡片:
                    if (
                        号
                        and (
                            cls.攻击性[号 - 1] == arg_低
                            if arg_精确
                            else cls.攻击性[号 - 1] >= arg_低
                        )
                        and 服务_类.卡价[号 - 1] > 价
                    ):
                        选, 价 = 号, 服务_类.卡价[号 - 1]
                return 选

            if 敌 >= 0 and 敌 in 候:
                号 = 最佳(敌, 1, False)
                if 号:
                    记.参数1 = 号
                    return 目标(cls._自己码(敌))
            最高, 有 = 0, False
            for i in range(len(世.玩家)):
                if i in 候:
                    号 = 最佳(i, 2, True)
                    if 号 and 服务_类.卡价[号 - 1] > 最高:
                        最高, 记.参数1 = 服务_类.卡价[号 - 1], 号
                        有 = 目标(cls._自己码(i))
            return 有
        if 卡 == 14:
            if not 状.龟行天数:
                if 地码(世, 当前):
                    p = 世.地产[当前 - 2000]
                    if (
                        p.经济.业主 == 自
                        and not p.经济.连锁
                        and p.经济.等级 < 5
                        and cls._回绕(p.每级造价 * 指) < 钱
                        and cls._回绕(钱 + 人.记录.银行) > 10000
                        and 状.财运修正 >= 0
                    ):
                        if any(
                            i != 当前 - 2000 and 同街(i, 当前 - 2000) and q.经济.业主 == 自
                            for i, q in enumerate(世.地产[1:], 1)
                        ):
                            return 目标(cls._自己码(槽))
                        if p.经济.等级 >= 2:
                            return True
                elif 设施码(世, 当前):
                    p = 世.设施[当前 - 4000]
                    if (
                        p.业主 == 自
                        and cls._回绕(p.每级造价 * 指) < 钱
                        and 钱 > 10000
                        and p.类型
                        and p.类型 != 3
                        and p.等级 < 5
                        and 状.财运修正 >= 0
                    ):
                        return 目标(cls._自己码(槽))
            候 = cls._扫描玩家(世, 槽, 扫描())
            for i in range(len(世.玩家)):
                if i not in 候:
                    continue
                码 = cls._脚下(世, i)
                if 设施码(世, 码):
                    p = 世.设施[码 - 4000]
                    if p.业主 == 自 and p.类型 and p.等级 >= 2:
                        return 目标(cls._自己码(i))
                elif cls._公司码(世, 码) and 世.公司[码 - 6000].业主 == 自:
                    return 目标(cls._自己码(i))
            return False
        if 卡 == 15:
            return 随.api_下一个() % 4 == 0
        if 卡 in (16, 17):
            候, 最敌 = [], None
            for i in cls._扫描玩家(世, 槽, 扫描()):
                if not 世.玩家[i].状态.睡眠天数 and 18 not in 世.玩家[i].记录.卡片:
                    if i == 敌:
                        最敌 = len(候)
                    候.append(i)
            if not 候:
                return False
            位 = 最敌 if 最敌 is not None else 随.api_下一个() % len(候)
            return 目标(cls._自己码(候[位]))
        if 卡 == 22:
            号 = 状.神明信息
            if 0 < 号 <= len(世.物件):
                return 世.物件[号 - 1].种类 in (5, 6, 7, 8, 10, 15)
            号 = 状.附身炸弹
            return 0 < 号 <= len(世.物件) and 世.物件[号 - 1].剩余天数 < 13
        if 卡 == 23:
            if cls._友善号(状.神明信息):
                return False
            表 = 钩.附近实例(槽) if 钩.附近实例 else []
            号 = cls._最近神(世, 槽, 表)
            return 号 is not None and cls._友善号(号) and 目标(号)
        if 卡 in (24, 25):
            if not 钩.休市 or 钩.休市():
                return False

            def 最佳股(arg_持有人: int, arg_需公司: bool) -> int:
                价, 选 = 0, -1
                for i, 股 in enumerate(世.股票):
                    额 = cls._持仓成本(世.玩家[arg_持有人].持仓[i])
                    if (
                        额 <= 价
                        or 股.停牌天数
                        or (arg_需公司 and not 股.标志4)
                        or (卡 == 25 and 人.持仓[i].数量)
                    ):
                        continue
                    势 = 股市_类.api_走势(世, i)
                    if (卡 == 24 and 势 == 走势_类.涨停) or (卡 == 25 and 势 == 走势_类.跌停):
                        continue
                    价, 选 = 额, i
                return 选

            if 卡 == 24:
                股 = 最佳股(槽, False)
                return 股 >= 0 and 目标(股)
            公司数 = [0] * 4
            for 司 in 世.公司[1:]:
                if 0 < 司.业主 <= 4:
                    公司数[司.业主 - 1] = (公司数[司.业主 - 1] + 1) & 255
            司主, 最多 = -1, 0
            for i in range(4):
                if i != 槽 and 公司数[i] > 最多:
                    司主, 最多 = i, 公司数[i]
            司股 = 最佳股(司主, True) if 0 <= 司主 < len(世.玩家) else -1
            敌股 = 最佳股(敌, False) if 敌 >= 0 else -1
            股 = 敌股 if 敌股 >= 0 else 司股
            return 股 >= 0 and 目标(股)
        if 卡 == 27:
            前名, 有前, 设施分, 地游标 = b"", False, 0, arg_遍历末
            for 码 in 扫描():
                if 地码(世, 码):
                    名 = cls._名(世.地产[码 - 2000].经济.街道名)
                    if 有前 and 名 == 前名:
                        continue
                    总, 己, 己层, 他层, 有敌 = 0, 0, 0, 0, False
                    地游标 = 1
                    while 地游标 < len(世.地产):
                        p = 世.地产[地游标].经济
                        if cls._名(p.街道名) == 名:
                            总 += 1
                            if p.业主 == 自:
                                己, 己层 = 己 + 1, (己层 + p.等级) & 0xFFFFFFFF
                            elif p.业主:
                                他层 = (他层 + p.等级) & 0xFFFFFFFF
                            if 敌 >= 0 and p.业主 == 敌 + 1:
                                有敌 = True
                                break
                        地游标 += 1
                    比 = 股市_类._浮点(股市_类._位(float(己) / 总)) if 总 else math.nan
                    if not 有敌 and 己层 >= 7 and 他层 <= 3 and 比 >= 0.66:
                        return 目标(码)
                    前名, 有前 = 名, True
                elif 设施码(世, 码):
                    p = 世.设施[码 - 4000]
                    if p.业主 == 自 and p.类型 and p.类型 != 4 and p.等级 >= 3 and p.等级 > 设施分:
                        设施分 = 地游标 & 0xFFFFFFFF
                        目标(码)
            return 设施分 != 0
        if 卡 == 28:
            if not 钩.前瞻节点:
                return False
            路 = 钩.前瞻节点(槽, 6)
            前名, 有前 = b"", False
            for 节 in 路.节点:
                码 = cls._节点码(世, 节)
                if 地码(世, 码):
                    名 = cls._名(世.地产[码 - 2000].经济.街道名)
                    if 有前 and 名 == 前名:
                        continue
                    他层, 有己 = 0, False
                    for p in 世.地产[1:]:
                        if cls._名(p.经济.街道名) != 名:
                            continue
                        if p.经济.业主 == 自:
                            有己 = True
                            break
                        if p.经济.业主:
                            他层 = (他层 + p.经济.等级) & 0xFFFFFFFF
                    if not 有己 and 他层 >= 7:
                        return 目标(码)
                    前名, 有前 = 名, True
                elif 设施码(世, 码) and 敌 >= 0:
                    p = 世.设施[码 - 4000]
                    if p.业主 == 敌 + 1 and p.类型 and p.等级 >= 3:
                        return 目标(码)
            return False
        if 卡 == 29:
            候 = cls._扫描玩家(世, 槽, 扫描())
            胜, 最多 = len(世.玩家), 0
            for i, p in enumerate(世.玩家):
                if i == 槽 or not p.记录.控制标志:
                    continue
                数 = sum(q.经济.业主 == i + 1 for q in 世.地产[1:]) + sum(
                    q.业主 == i + 1 for q in 世.设施[1:]
                )
                if 数 > 最多:
                    胜, 最多 = i, 数
            return (
                胜 < len(世.玩家)
                and 胜 != 敌
                and 世.玩家[胜].状态.盟友 != 自
                and 胜 in 候
                and 目标(cls._自己码(胜))
            )
        if 卡 == 30:
            if not 钩.前瞻节点:
                return False
            路 = 钩.前瞻节点(槽, 3)
            危, 总, 机 = 路.经过路口, 0, 0
            if not 危:
                for 节 in 路.节点:
                    码 = cls._节点码(世, 节)
                    if 地码(世, 码):
                        p = 世.地产[码 - 2000]
                        if not p.经济.业主 or (
                            p.经济.业主 == 自 and not p.经济.连锁 and p.经济.等级 < 5
                        ):
                            总, 机 = cls._回绕(总 + (p.每级造价 if p.经济.业主 else p.地价)), 机 + 1
                        if (
                            p.经济.业主
                            and p.经济.业主 != 自
                            and cls._通行费(世, 码) > cls._回绕(指 * 1000)
                        ):
                            危 = True
                            break
                    elif 设施码(世, 码):
                        p = 世.设施[码 - 4000]
                        if not p.业主 or (p.业主 == 自 and p.类型 and p.类型 != 3 and p.等级 < 5):
                            总, 机 = cls._回绕(总 + (p.每级造价 if p.业主 else p.地价)), 机 + 1
                        if p.业主 and p.业主 != 自 and p.类型 and p.类型 != 4 and p.等级:
                            危 = True
                            break
                    elif (
                        cls._公司码(世, 码)
                        and 世.公司[码 - 6000].业主
                        and 世.公司[码 - 6000].业主 != 自
                    ):
                        危 = True
                        break
            if (
                not 危
                and float(总) * 1.5 < 钱
                and 机 >= 2
                and cls._回绕(钱 + 人.记录.银行) > 10000
                and 状.财运修正 >= 0
            ):
                return 目标(cls._自己码(槽))
            for 敌人 in cls._扫描玩家(世, 槽, 扫描()):
                后 = 钩.前瞻节点(敌人, 3)
                if 后.经过路口:
                    continue
                总, 机, 拒 = 0, 0, False
                for 节 in 后.节点:
                    码 = cls._节点码(世, 节)
                    if 地码(世, 码):
                        p = 世.地产[码 - 2000].经济
                        if p.业主 == 自:
                            总, 机 = cls._回绕(总 + cls._通行费(世, 码)), 机 + 1
                        主 = p.业主
                    elif 设施码(世, 码):
                        p = 世.设施[码 - 4000]
                        if p.业主 == 自 and p.类型 and p.类型 != 4 and p.等级:
                            总, 机 = cls._回绕(总 + 事件_类._取(p.各级租金, p.等级)), 机 + 1
                        主 = p.业主
                    elif cls._公司码(世, 码):
                        p = 世.公司[码 - 6000]
                        if p.业主 == 自:
                            总, 机 = cls._回绕(总 + p.通行费), 机 + 1
                        主 = p.业主
                    else:
                        continue
                    if not 主 or 主 == 敌人 + 1:
                        拒 = True
                        break
                if not 拒 and 总 >= cls._回绕(指 * 10000) and 机 >= 2:
                    return 目标(cls._自己码(敌人))
            return False
        return False

    @staticmethod
    def _解码(arg_码: int) -> 卡片目标_类 | None:
        if arg_码 & 0x8000:
            位 = arg_码 & 255
            if 位:
                return 卡片目标_类(目标种类_类.角色, (位 & -位).bit_length() - 1)
            if arg_码 & 0x7F00:
                return 卡片目标_类(目标种类_类.物件, arg_码 >> 8 & 127)
            return None
        return 卡片目标_类(目标种类_类.地产, arg_码 & 65535) if 2000 < arg_码 < 6000 else None

    @classmethod
    def api_选择(
        cls,
        arg_世: 世界_类,
        arg_随: 随机数_类,
        arg_槽: int,
        arg_钩: 卡片回调_类,
        arg_记: 电脑卡片记忆_类 | None = None,
    ) -> 卡片用法_类 | None:
        if not 0 <= arg_槽 < len(arg_世.玩家):
            return None
        人 = arg_世.玩家[arg_槽]
        if not 人.记录.控制标志 & 6 or not 人.状态.卡片策略 & 1:
            return None
        数 = 服务_类._库存(arg_世, arg_槽).api_卡数()
        if not 数:
            return None
        位, 候 = arg_随.api_下一个() % 数 if 数 > 8 else 0, []
        for _ in range(8):
            候.append(人.记录.卡片[位])
            位 += 1
            if 数 > 8 and 位 == 数:
                位 = 0
        记 = arg_记 if arg_记 is not None else 电脑卡片记忆_类()
        for 卡 in 候:
            if not 卡:
                break
            if 卡 > 30:
                continue
            偏 = cls.攻击性[卡 - 1] - 人.状态.救援策略
            if 偏 >= 2 or (偏 == 1 and arg_随.api_下一个() % 3 != 0):
                continue
            if not cls._谓词(arg_世, arg_随, arg_槽, 卡, arg_钩, 记, 位):
                continue
            果 = 卡片用法_类(卡)
            if 卡 in (24, 25):
                果.目标 = 卡片目标_类(目标种类_类.股票, 记.参数0 & 65535)
            elif 卡 == 7:
                果.选择 = 卡片目标_类(目标种类_类.地产, 记.参数0 & 65535)
            elif 卡 not in (1, 3, 8, 15, 22, 23):
                果.目标 = cls._解码(记.参数0)
            if 卡 == 13:
                果.选择 = 卡片目标_类(目标种类_类.卡片, 记.参数1 & 65535)
            return 果
        return None
