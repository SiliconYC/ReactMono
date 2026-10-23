# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/stocks.cpp；所有中间精度和回绕由显式契约表达。
# ◑ 导入
import math
import struct
from dataclasses import dataclass
from enum import IntEnum

from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.world import 世界_类
from rich4.world_map import 公司_类


# ◕ 功能
@dataclass(frozen=True)
class 买入结果_类:
    """
    成交实际费用和公司控制权变更。

    更新日志：
    2026.10.23 - 对应 PurchaseResult。
    """

    费用: int
    公司易主: bool


@dataclass(frozen=True)
class 卖出结果_类:
    """
    卖股实际收入和公司控制权变更。

    更新日志：
    2026.10.23 - 对应 SaleResult。
    """

    收入: int
    公司易主: bool


class 走势_类(IntEnum):
    """
    与参考 PriceTrend 的原顺序对应。

    更新日志：
    2026.10.23 - 建立走势编码。
    """

    上涨 = 0
    涨停 = 1
    下跌 = 2
    跌停 = 3
    不变 = 4


class 股市_类:
    """
    股票、一级发行、公司排名、财富与日行情；随机流由会话显式提供。

    更新日志：
    2026.10.23 - 对应 stocks 模块全部规则，不读取时钟或调用 UI。
    """

    @staticmethod
    def _回绕(arg_数: int) -> int:
        位 = arg_数 & 0xFFFFFFFF
        return 位 - 0x100000000 if 位 & 0x80000000 else 位

    @staticmethod
    def _浮点(arg_位: int) -> float:
        return struct.unpack("<f", struct.pack("<I", arg_位))[0]

    @staticmethod
    def _位(arg_数: float) -> int:
        return struct.unpack("<I", struct.pack("<f", arg_数))[0]

    @classmethod
    def _单(cls, arg_数: float) -> float:
        try:
            return cls._浮点(cls._位(arg_数))
        except OverflowError as 错误:
            raise ValueError("数值超出 binary32") from 错误

    @staticmethod
    def _索引(arg_世: 世界_类, arg_玩家: int, arg_股: int) -> None:
        if (
            len(arg_世.玩家) > 4
            or not 0 <= arg_玩家 < len(arg_世.玩家)
            or not 0 <= arg_股 < len(arg_世.股票)
        ):
            raise IndexError("股票玩家或股票索引越界")

    @classmethod
    def _所得(cls, arg_价: float, arg_数量: int) -> int:
        if not math.isfinite(arg_价) or arg_价 < 0 or arg_数量 < 0:
            raise ValueError("成交要求有限非负报价和数量")
        位 = cls._位(arg_价)
        指数 = (位 >> 23) & 255
        尾数 = (位 & 0x7FFFFF) | (0 if 指数 == 0 else 0x800000)
        积 = 尾数 * arg_数量
        移位 = -149 if 指数 == 0 else 指数 - 150
        if 积 == 0:
            return 0
        if 移位 >= 0:
            if 移位 >= 31 or 积 > 0x7FFFFFFF >> 移位:
                return -2147483648
            整数 = 积 << 移位
        else:
            整数 = 0 if 移位 <= -64 else 积 >> -移位
        return -2147483648 if 整数 > 2147483647 else 整数

    @staticmethod
    def _关联(arg_世: 世界_类, arg_股: int) -> 公司_类 | None:
        编号 = arg_世.股票[arg_股].标志4
        if 编号 == 0:
            return None
        if not 0 <= 编号 < len(arg_世.公司):
            raise ValueError("股票引用不存在的公司")
        公司 = arg_世.公司[编号]
        if any(not 0 <= 主 <= len(arg_世.玩家) for 主 in 公司.股东排名):
            raise ValueError("公司排名引用不存在的股东")
        return 公司

    @staticmethod
    def _重排(
        arg_世: 世界_类,
        arg_公司: 公司_类 | None,
        arg_玩家: int,
        arg_股: int,
    ) -> bool:
        if arg_公司 is None:
            return False
        顺序 = arg_公司.股东排名
        主 = arg_玩家 + 1
        if 主 in 顺序:
            位置 = 顺序.index(主)
            顺序[位置:] = 顺序[位置 + 1 :] + [0]
        数量 = arg_世.玩家[arg_玩家].持仓[arg_股].数量
        if 数量 != 0:
            插入 = 0
            for 位置 in range(2, -1, -1):
                其他 = 顺序[位置]
                if 其他 == 0:
                    continue
                if arg_世.玩家[其他 - 1].持仓[arg_股].数量 < 数量:
                    顺序[位置 + 1] = 其他
                else:
                    插入 = 位置 + 1
                    break
            顺序[插入] = 主
        改变 = arg_公司.业主 != 顺序[0]
        arg_公司.业主 = 顺序[0]
        return 改变

    @classmethod
    def api_更新业主(cls, arg_世: 世界_类, arg_玩家: int, arg_股: int) -> bool:
        cls._索引(arg_世, arg_玩家, arg_股)
        return cls._重排(arg_世, cls._关联(arg_世, arg_股), arg_玩家, arg_股)

    @classmethod
    def api_调整股价(cls, arg_前: float, arg_幅: float) -> float:
        前, 幅 = cls._单(arg_前), cls._单(arg_幅)
        if (
            not math.isfinite(前)
            or not 0 <= 前 <= 10000
            or not math.isfinite(幅)
            or not -10 <= 幅 <= 10
        ):
            raise ValueError("股价或百分比超出原市场域")
        扩展 = 扩展数_类.api_从值
        候选 = ((扩展(100) + 扩展(幅)) / 扩展(100) * 扩展(前)).api_单精度()
        改变 = (扩展(候选) - 扩展(前) if 幅 > 0 else 扩展(前) - 扩展(候选)).api_单精度()
        档位 = (
            0.01
            if 候选 < 5
            else 0.05
            if 候选 < 15
            else 0.1
            if 候选 < 50
            else 0.5
            if 候选 < 150
            else 1.0
        )
        差, 格 = 扩展(改变), 扩展(档位)
        商 = (差 / 格).api_整数()
        余 = 差 - 格 * 扩展(商)
        舍入 = (扩展(候选) - 余 if 幅 > 0 else 扩展(候选) + 余).api_单精度()
        return min(9999.0, max(1.0, 舍入))

    @classmethod
    def api_走势(cls, arg_世: 世界_类, arg_股: int) -> 走势_类:
        if not 0 <= arg_股 < len(arg_世.股票):
            raise IndexError("股票索引越界")
        股 = arg_世.股票[arg_股]
        前, 现 = cls._浮点(股.浮点位[1]), cls._浮点(股.浮点位[2])
        if 现 > 前:
            return 走势_类.涨停 if 现 >= cls.api_调整股价(前, 10) else 走势_类.上涨
        if 现 < 前:
            return 走势_类.跌停 if 现 <= cls.api_调整股价(前, -10) else 走势_类.下跌
        return 走势_类.不变

    @classmethod
    def api_买入(
        cls,
        arg_世: 世界_类,
        arg_玩家: int,
        arg_股: int,
        arg_数量: int,
        arg_市场: bool,
    ) -> 买入结果_类:
        cls._索引(arg_世, arg_玩家, arg_股)
        玩家 = arg_世.玩家[arg_玩家]
        持仓, 股 = 玩家.持仓[arg_股], arg_世.股票[arg_股]
        公司 = cls._关联(arg_世, arg_股)
        if arg_数量 <= 0 or 持仓.数量 < 0 or arg_数量 > 2147483647 - 持仓.数量:
            raise ValueError("买股数量必须为正且不能溢出")
        if arg_市场:
            费用 = cls._所得(cls._浮点(股.浮点位[2]), arg_数量)
            if 费用 < 0 or 费用 > 玩家.记录.银行 or arg_数量 > 股.可购股数 or arg_数量 > 股.标志10:
                raise ValueError("买股超出银行余额、市场股数或交易限额")
        else:
            if 公司 is None or 公司.估值 < 0 or arg_数量 > 公司.剩余股份:
                raise ValueError("公司一级发行股数不足")
            费用 = (公司.估值 // 10000) * arg_数量
            if 费用 > 玩家.记录.现金 or 费用 > 2147483647:
                raise ValueError("一级发行超过现金余额")
        旧成本 = cls._所得(cls._浮点(持仓.成本位), 持仓.数量)
        总成本 = cls._回绕(旧成本 + 费用)
        新数量 = 持仓.数量 + arg_数量
        基准 = (扩展数_类.api_从值(总成本) / 扩展数_类.api_从值(新数量)).api_单精度()
        if arg_市场:
            股.可购股数 = (股.可购股数 - arg_数量) & 65535
            股.标志10 = (股.标志10 - arg_数量) & 65535
            玩家.记录.银行 = cls._回绕(玩家.记录.银行 - 费用)
        else:
            公司.剩余股份 -= arg_数量
            玩家.记录.现金 = cls._回绕(玩家.记录.现金 - 费用)
        持仓.数量, 持仓.成本位 = 新数量, cls._位(基准)
        return 买入结果_类(费用, cls._重排(arg_世, 公司, arg_玩家, arg_股))

    @classmethod
    def api_卖出(
        cls,
        arg_世: 世界_类,
        arg_玩家: int,
        arg_股: int,
        arg_数量: int,
        arg_入银行: bool,
    ) -> 卖出结果_类:
        cls._索引(arg_世, arg_玩家, arg_股)
        持仓 = arg_世.玩家[arg_玩家].持仓[arg_股]
        if arg_数量 < 0 or arg_数量 > 持仓.数量:
            raise ValueError("卖股数量超过持仓")
        股 = arg_世.股票[arg_股]
        收入 = cls._所得(cls._浮点(股.浮点位[2]), arg_数量)
        公司 = cls._关联(arg_世, arg_股)
        持仓.数量 -= arg_数量
        if 持仓.数量 == 0:
            持仓.成本位 = 0
        股.可购股数 = (股.可购股数 + arg_数量) & 65535
        股.标志10 = (股.标志10 + arg_数量) & 65535
        if arg_入银行:
            玩家 = arg_世.玩家[arg_玩家]
            玩家.记录.银行 = cls._回绕(玩家.记录.银行 + 收入)
        else:
            arg_世.公共基金 = cls._回绕(arg_世.公共基金 + 收入)
        return 卖出结果_类(收入, cls._重排(arg_世, 公司, arg_玩家, arg_股))

    @classmethod
    def api_强制行情(cls, arg_世: 世界_类, arg_选择: int) -> int:
        if not 0 <= arg_选择 <= len(arg_世.股票) or not 0 <= arg_世.股史游标 < 144:
            raise IndexError("强制行情选择或历史游标越界")
        前槽 = 143 if arg_世.股史游标 == 0 else arg_世.股史游标 - 1
        开始, 结束 = (0, len(arg_世.股票)) if arg_选择 == 0 else (arg_选择 - 1, arg_选择)
        更新 = 0
        for i in range(开始, 结束):
            股 = arg_世.股票[i]
            if 股.新闻走势 == 0:
                continue
            改变 = 10.0 if 股.新闻走势 & 0xF0 else -10.0
            价 = cls.api_调整股价(cls._浮点(股.浮点位[1]), 改变)
            股.浮点位[4], 股.浮点位[2] = cls._位(改变), cls._位(价)
            arg_世.股史[i][前槽] = 股.浮点位[2]
            更新 += 1
        return 更新

    @classmethod
    def api_财富(cls, arg_世: 世界_类, arg_玩家: int) -> int:
        if not 0 <= arg_玩家 < len(arg_世.玩家):
            raise IndexError("财富玩家索引越界")
        玩家 = arg_世.玩家[arg_玩家]
        总 = cls._回绕(玩家.记录.现金 + 玩家.记录.银行 - 玩家.记录.贷款)
        for i, 股 in enumerate(arg_世.股票):
            价 = cls._浮点(股.浮点位[2])
            数 = 玩家.持仓[i].数量
            if not math.isfinite(价) or not 0 <= 价 <= 10000 or 数 < 0 or (价 != 0 and 价 < 1):
                raise ValueError("财富要求有效股价和非负持仓")
            舍入总 = int(扩展数_类.api_从值(总).api_单精度())
            原位 = 股.浮点位[2]
            指数 = (原位 >> 23) & 255
            尾数 = (原位 & 0x7FFFFF) | (0 if 指数 == 0 else 0x800000)
            积 = 尾数 * 数
            小数位 = 23 if 价 == 0 else 150 - 指数
            整数 = 积 >> 小数位
            有小数 = bool(积 & ((1 << 小数位) - 1))
            和 = 舍入总 + 整数
            if 和 < 0 and 有小数:
                和 += 1
            总 = -2147483648 if not -2147483648 <= 和 <= 2147483647 else 和
        for 地 in arg_世.地产[1:]:
            if 地.经济.业主 == arg_玩家 + 1:
                级数 = 1 if 地.经济.连锁 else 地.经济.等级
                总 = cls._回绕(总 + 地.地价 + 地.每级造价 * 级数)
        for 设施 in arg_世.设施[1:]:
            if 设施.业主 == arg_玩家 + 1:
                总 = cls._回绕(总 + 设施.地价 + 设施.每级造价 * 设施.等级)
        return 总

    @classmethod
    def api_刷新限额(cls, arg_世: 世界_类, arg_随机: 随机数_类) -> None:
        扩展 = 扩展数_类.api_从值
        for 股 in arg_世.股票:
            if 股.可购股数 <= 1000:
                股.标志10 = 股.可购股数
            else:
                比例 = 扩展(arg_随机.api_下一个() % 2000 + 1000) / 扩展(10000)
                股.标志10 = (比例 * 扩展(股.可购股数)).api_整数() & 65535

    @classmethod
    def api_日更新(cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_假日: bool) -> bool:
        if arg_假日 or arg_世.新闻影响天数 != 0:
            return False
        if not 0 <= arg_世.股史游标 < 144:
            raise IndexError("日行情历史游标越界")
        扩展 = 扩展数_类.api_从值
        市场 = (扩展(arg_随机.api_下一个() - 16384) / 扩展(4097)).api_单精度()
        arg_世.股市走势位 = cls._位(市场)
        总额 = 0.0
        for i, 股 in enumerate(arg_世.股票):
            股.浮点位[1] = 股.浮点位[2]
            前 = cls._浮点(股.浮点位[1])
            if 股.停牌天数:
                走势 = 0.0
            elif 股.新闻走势:
                走势 = 10.0 if 股.新闻走势 & 0xF0 else -10.0
            else:
                冲量 = 扩展(arg_随机.api_下一个() - 16384) / 扩展(1171)
                股.原值32 = cls._位(冲量.api_单精度())
                走势 = (
                    冲量 * 扩展(cls._浮点(股.浮点位[3])) + 扩展(cls._浮点(股.浮点位[4]))
                ).api_单精度()
                走势 = (扩展(走势) + 扩展(市场)).api_单精度()
                公司 = cls._关联(arg_世, i)
                if 公司 is not None:
                    参考 = (扩展(公司.估值) / 扩展(10000)).api_单精度()
                    上倍, 下倍 = 3, 0.85
                else:
                    参考 = cls._浮点(股.浮点位[0])
                    上倍, 下倍 = 8, 0.5
                if 前 > 参考:
                    上界 = (扩展(参考) * 扩展(上倍)).api_单精度()
                    if 前 > 上界:
                        走势 = (扩展(走势) * 扩展(0.5 if 走势 > 0 else 2)).api_单精度()
                else:
                    下界 = (扩展(参考) * 扩展(下倍)).api_单精度()
                    if 前 < 下界:
                        走势 = (扩展(走势) * 扩展(2 if 走势 > 0 else 0.5)).api_单精度()
                走势 = min(10.0, max(-10.0, 走势))
            股.浮点位[4] = cls._位(走势)
            当前 = cls.api_调整股价(前, 走势)
            股.浮点位[2] = cls._位(当前)
            arg_世.股史[i][arg_世.股史游标] = 股.浮点位[2]
            总额 = (扩展(总额) + 扩展(当前)).api_单精度()
        arg_世.股史游标 = (arg_世.股史游标 + 1) % 144
        arg_世.股市指数 = (扩展(总额) * 扩展(10)).api_整数()
        return True
