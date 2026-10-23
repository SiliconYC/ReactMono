# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/stocks_ai.cpp，原0x42bf03/0x42c79f；禁止调用者额外抽概率。
# ◑ 导入
import math
from dataclasses import dataclass

from rich4.calendar import 日期_类
from rich4.events import 事件_类
from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.stocks import 股市_类, 走势_类
from rich4.world import 世界_类
from rich4.world_map import 公司_类
from rich4.world_player import 世界玩家_类
from rich4.world_stocks import 股票状态_类


# ◕ 功能
@dataclass(frozen=True)
class 电脑成交_类:
    """
    原电脑股票买卖记录，金额由实际股票结算返回而非估算。

    更新日志：
    2026.10.23 - 对应stocks_ai::Trade。
    """

    股票: int = 0
    数量: int = 0
    金额: int = 0
    公司易主: bool = False


class 股票电脑_类:
    """
    原公司/普通股票评分、概率门控、贷款紧急卖出及Watcom排序。

    更新日志：
    2026.10.23 - 移植stocks_ai全部分支，使用已差分的软件x87和真实股票结算。
    """

    @staticmethod
    def _小(arg_a: 扩展数_类, arg_b: 扩展数_类) -> bool:
        if not arg_a.有效数 and not arg_b.有效数:
            return False
        if arg_a.负 != arg_b.负:
            return arg_a.负
        小 = not arg_a.有效数 or bool(
            arg_b.有效数
            and (
                arg_a.指数 < arg_b.指数
                or (arg_a.指数 == arg_b.指数 and arg_a.有效数 < arg_b.有效数)
            )
        )
        等 = arg_a.有效数 == arg_b.有效数 and arg_a.指数 == arg_b.指数
        return not 小 and not 等 if arg_a.负 else 小

    @staticmethod
    def _标量(arg_股: 股票状态_类, arg_号: int) -> float:
        return 股市_类._浮点(arg_股.浮点位[arg_号])

    @staticmethod
    def _流动(arg_人: 世界玩家_类) -> int:
        return 股市_类._回绕(arg_人.记录.现金 + arg_人.记录.银行)

    @staticmethod
    def _原日序(arg_打包: int) -> int:
        if arg_打包 == 0:
            return -1
        日, 月, 年 = arg_打包 & 255, arg_打包 >> 8 & 255, arg_打包 >> 16
        return 股市_类._回绕(日期_类(年, 月, 1).api_天数() + 日 - 1)

    @classmethod
    def _贷款余日(cls, arg_世: 世界_类, arg_人: 世界玩家_类) -> int:
        日, 月, 年 = arg_世.头.日期
        今 = 日期_类(年, 月, 日).api_天数()
        return 股市_类._回绕(cls._原日序(arg_人.状态.贷款到期) - 今)

    @staticmethod
    def _历史均值(arg_世: 世界_类, arg_股: int, arg_期: int) -> float:
        游 = arg_世.股史游标 - arg_期
        if 游 < 0:
            游 += 144
        总, 数 = 0.0, 0
        E = 扩展数_类.api_从值
        for _ in range(arg_期):
            if 游 == 144:
                游 = 0
            位 = 事件_类._取(arg_世.股史[arg_股], 游)
            游 += 1
            if 位 & 0x7FFFFFFF:
                总 = (E(总) + E(股市_类._浮点(位))).api_单精度()
                数 += 1
        return (E(总) / E(数)).api_单精度() if 数 else 总

    @staticmethod
    def _公司均利(arg_世: 世界_类, arg_司: 公司_类) -> float:
        值 = 事件_类._除(arg_司.资金变化, arg_世.月数) if arg_世.月数 else arg_司.资金变化
        return 扩展数_类.api_从值(值).api_单精度()

    @staticmethod
    def _单位估值(arg_司: 公司_类) -> float:
        return 扩展数_类.api_从值(事件_类._除(arg_司.估值, 10000)).api_单精度()

    @staticmethod
    def _公司(arg_世: 世界_类, arg_股: 股票状态_类) -> 公司_类:
        if not 0 < arg_股.标志4 < len(arg_世.公司):
            raise ValueError("股票电脑引用缺失公司")
        return arg_世.公司[arg_股.标志4]

    @classmethod
    def _持仓值(cls, arg_世: 世界_类, arg_槽: int) -> int:
        总 = 0
        E = 扩展数_类.api_从值
        for i, 股 in enumerate(arg_世.股票):
            量 = arg_世.玩家[arg_槽].持仓[i].数量
            if 量:
                总 = (E(量) * E(cls._标量(股, 2)) + E(E(总).api_单精度())).api_整数()
        return 总

    @classmethod
    def _公司买分(cls, arg_世: 世界_类, arg_槽: int, arg_i: int) -> int:
        股 = arg_世.股票[arg_i]
        司 = cls._公司(arg_世, 股)
        持 = arg_世.玩家[arg_槽].持仓[arg_i]
        E = 扩展数_类.api_从值
        价, 估, 利 = E(cls._标量(股, 2)), E(cls._单位估值(司)), E(cls._公司均利(arg_世, 司))
        低, 高 = E(股市_类._回绕(5000 * arg_世.头.物价)), E(股市_类._回绕(10000 * arg_世.头.物价))
        分 = 0
        if cls._小(E(0), 利) and cls._小(利, 低):
            分 += 1
        if not cls._小(利, 低) and cls._小(利, 高):
            分 += 2
        if not cls._小(利, 高):
            分 += 3
        if 司.资金 > 0 and 持.数量 < 5000 and not cls._小(估 * E(1.2), 价):
            分 += 1
            if 司.业主 and 司.业主 != arg_槽 + 1:
                主量 = 事件_类._取(arg_世.玩家, 司.业主 - 1).持仓[arg_i].数量
                if 股市_类._回绕(股市_类._回绕(股.可购股数 + 持.数量) + 司.剩余股份) > 主量:
                    分 += 1
                if 股市_类._回绕(股.标志10 + 持.数量) > 主量:
                    分 += 2
        if cls._小(价, 估 * E(0.85)):
            分 += 3
        if cls._小(价, 估 * E(0.7)):
            分 += 5
        return 分

    @classmethod
    def _市场买分(cls, arg_世: 世界_类, arg_i: int) -> int:
        股 = arg_世.股票[arg_i]
        E = 扩展数_类.api_从值
        价, 基 = E(cls._标量(股, 2)), E(cls._标量(股, 0))
        长, 短 = E(cls._历史均值(arg_世, arg_i, 24)), E(cls._历史均值(arg_世, arg_i, 6))
        分 = 0
        if (
            cls._小(价, 基 * E(2.5))
            and 股市_类._回绕(股.浮点位[4]) > 0x40000000
            and cls._小(长, 短)
        ):
            分 += 2
        if cls._小(价, 基 * E(0.6)) and cls._小(长, 短):
            分 += 4
        if cls._小(短, 长 * E(0.5)):
            分 += 2
        return 分

    @staticmethod
    def _原排序(arg_项: list[tuple[int, int]]) -> None:
        for 间 in (3, 1):
            for i in range(间, len(arg_项), 间):
                j = i
                while j >= 间 and arg_项[j - 间][1] < arg_项[j][1]:
                    arg_项[j - 间], arg_项[j] = arg_项[j], arg_项[j - 间]
                    j -= 间

    @classmethod
    def _公司卖分(cls, arg_世: 世界_类, arg_槽: int, arg_i: int, arg_紧急: bool) -> int:
        股 = arg_世.股票[arg_i]
        司 = cls._公司(arg_世, 股)
        持 = arg_世.玩家[arg_槽].持仓[arg_i]
        E = 扩展数_类.api_从值
        价, 本 = E(cls._标量(股, 2)), E(股市_类._浮点(持.成本位))
        估, 利 = E(cls._单位估值(司)), E(cls._公司均利(arg_世, 司))
        总 = 0
        for 人 in arg_世.玩家:
            总 = 股市_类._回绕(总 + 人.持仓[arg_i].数量)
        份 = (E(总) / E(持.数量)).api_单精度()
        拥有 = 司.业主 == arg_槽 + 1
        日 = arg_世.头.日期[0]
        分 = 0
        if (
            司.资金 <= 股市_类._回绕(-10000 * arg_世.头.物价)
            and cls._小(E(0.6), E(份))
            and 10 < 日 < 15
        ):
            分 += 3
        if (
            司.资金 <= 股市_类._回绕(-6000 * arg_世.头.物价)
            and cls._小(本 * E(1.2), 价)
            and not 拥有
            and 8 < 日 < 15
        ):
            分 += 2
        if (
            not cls._小(E(股市_类._回绕(10000 * arg_世.头.物价)), 利)
            and not cls._小(价, 估 * E(2))
            and cls._小(本 * E(1.3), 价)
            and cls._小(E(份), E(0.4))
        ):
            分 += 1
        if 司.业主 and not 拥有:
            主量 = 事件_类._取(arg_世.玩家, 司.业主 - 1).持仓[arg_i].数量
            if (
                股市_类._回绕(股市_类._回绕(持.数量 + 股.可购股数) + 司.剩余股份) < 主量
                and 司.资金 <= 0
                and not cls._小(价, 本 * E(1.5))
            ):
                分 += 1
        if (
            cls._小(估 * E(2), 价)
            and cls._小(本 * E(2), 价)
            and cls._标量(股, 2) < cls._标量(股, 1)
            and not 拥有
        ):
            分 += 2
        if (
            cls._小(估 * E(3), 价)
            and cls._小(本 * E(3), 价)
            and cls._标量(股, 2) < cls._标量(股, 1)
            and 拥有
        ):
            分 += 2
        return 分 + int(arg_紧急)

    @staticmethod
    def _比率分(arg_比: float, arg_偏: float) -> int:
        if not math.isfinite(arg_比):
            return -2147483648
        E = 扩展数_类.api_从值
        return ((E(arg_比) + E(arg_偏)) / E(0.5) + E(1)).api_整数()

    @classmethod
    def _市场卖分(cls, arg_世: 世界_类, arg_槽: int, arg_i: int, arg_紧急: bool) -> int:
        股, 持 = arg_世.股票[arg_i], arg_世.玩家[arg_槽].持仓[arg_i]
        价, 本 = cls._标量(股, 2), 股市_类._浮点(持.成本位)
        E = 扩展数_类.api_从值
        比 = math.inf if 本 == 0 else (E(价) / E(本)).api_单精度()
        最低 = 10000.0
        for 位 in arg_世.股史[arg_i]:
            值 = 股市_类._浮点(位)
            if 位 & 0x7FFFFFFF and 最低 > 值:
                最低 = 值
        长, 短 = cls._历史均值(arg_世, arg_i, 24), cls._历史均值(arg_世, arg_i, 6)
        分 = 0
        if float(比) > 1.6 and 股市_类._回绕(股.浮点位[4]) < 0x3F800000:
            分 += 2
        阈 = (E(最低) * E(8)).api_单精度()
        if 价 > 阈 and cls._小(E(本) * E(1.25), E(阈)):
            分 += 2
        if 长 > 短 and 价 < cls._标量(股, 1):
            分 += 2
        if 比 >= 2:
            分 = 股市_类._回绕(分 + cls._比率分(比, -2))
        可用 = cls._流动(arg_世.玩家[arg_槽])
        if 可用 < 股市_类._回绕(30000 * arg_世.头.物价) and 比 > 0:
            分 = 股市_类._回绕(分 + cls._比率分(比, 0))
        if 可用 < 股市_类._回绕(16000 * arg_世.头.物价) and 比 > 0:
            分 = 股市_类._回绕(分 + cls._比率分(比, 0))
        return 股市_类._回绕(分 + 分) if arg_紧急 else 分

    @staticmethod
    def _验证(arg_世: 世界_类, arg_槽: int) -> None:
        if not 0 <= arg_槽 < len(arg_世.玩家) or not 0 <= arg_世.股史游标 < 144:
            raise ValueError("股票电脑玩家或历史游标越界")

    @classmethod
    def api_买入(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int, arg_休市: bool
    ) -> list[电脑成交_类]:
        cls._验证(arg_世, arg_槽)
        人 = arg_世.玩家[arg_槽]
        if arg_随机.api_下一个() % 3 != 0 or not 人.状态.股票投资比例 or arg_休市:
            return []
        if 人.状态.贷款到期 and cls._贷款余日(arg_世, 人) < 15:
            return []
        值 = cls._持仓值(arg_世, arg_槽)
        预算 = 事件_类._除(
            股市_类._回绕(股市_类._回绕(值 + cls._流动(人)) * 人.状态.股票投资比例), 100
        )
        if 值 >= 预算:
            return []
        预算 = min(股市_类._回绕(预算 - 值), 人.记录.银行)
        候 = []
        for i in range(12):
            股 = arg_世.股票[i]
            分 = 0
            if not 股.停牌天数 and 股市_类.api_走势(arg_世, i) != 走势_类.涨停 and 股.标志10:
                if 股.标志4:
                    if 人.记录.银行 > 股市_类._回绕(20000 * arg_世.头.物价):
                        分 = cls._公司买分(arg_世, arg_槽, i)
                elif 人.记录.银行 > 股市_类._回绕(30000 * arg_世.头.物价):
                    分 = cls._市场买分(arg_世, i)
            候.append((i, 分))
        cls._原排序(候)
        for 排, (i, 分) in enumerate(候):
            if not 分 or arg_随机.api_下一个() % 24 > 12 - 排:
                continue
            股 = arg_世.股票[i]
            量 = min(
                (扩展数_类.api_从值(预算) / 扩展数_类.api_从值(cls._标量(股, 2))).api_整数(),
                股.标志10,
            )
            if not 量:
                return []
            果 = 股市_类.api_买入(arg_世, arg_槽, i, 量, True)
            return [电脑成交_类(i, 量, 果.费用, 果.公司易主)]
        return []

    @classmethod
    def api_卖出(
        cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int, arg_休市: bool
    ) -> list[电脑成交_类]:
        cls._验证(arg_世, arg_槽)
        人 = arg_世.玩家[arg_槽]
        急 = cls._贷款余日(arg_世, 人) <= 6 and cls._流动(人) < 人.记录.贷款
        if (not 急 and arg_随机.api_下一个() % 3 != 0) or arg_休市:
            return []
        E = 扩展数_类.api_从值
        成交 = []
        while True:
            高, 选 = 0, len(arg_世.股票)
            for i, 股 in enumerate(arg_世.股票):
                if (
                    not 人.持仓[i].数量
                    or 股.停牌天数
                    or 股市_类.api_走势(arg_世, i) == 走势_类.跌停
                ):
                    continue
                分 = (
                    cls._公司卖分(arg_世, arg_槽, i, 急)
                    if 股.标志4
                    else cls._市场卖分(arg_世, arg_槽, i, 急)
                )
                if 分 > 高:
                    高, 选 = 分, i
            if 选 == len(arg_世.股票):
                break
            量 = 人.持仓[选].数量
            果 = 股市_类.api_卖出(arg_世, arg_槽, 选, 量, True)
            成交.append(电脑成交_类(选, 量, 果.收入, 果.公司易主))
            if not 急 or not cls._小(E(cls._流动(人)), E(人.记录.贷款) * E(1.1)):
                break
        return 成交
