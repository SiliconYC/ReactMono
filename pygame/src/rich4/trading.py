# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/trading.cpp；出售表为原七槽值记录，不预留资产。
# ◑ 导入
import math
import struct
from dataclasses import dataclass, replace
from enum import IntEnum

from rich4.inventory import 库存_类
from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.services import 服务_类
from rich4.stocks import 股市_类
from rich4.world import 世界_类
from rich4.world_stocks import 出售项_类


# ◕ 功能
class 货类_类(IntEnum):
    """
    原出售表种类字节，股票从零编号，其余沿原编号。

    更新日志：
    2026.10.23 - 对应 OfferKind。
    """

    空 = 0
    股票 = 1
    地产 = 2
    道具 = 3
    卡片 = 4


@dataclass
class 可售项目_类:
    """
    玩家拥有的可挂牌项目及最大股数。

    更新日志：
    2026.10.23 - 对应 trading::Item。
    """

    种类: int = 0
    编号: int = 0
    最大数量: int = 1


@dataclass
class 挂牌限价_类:
    """
    参考价格与原十倍上限，均为有符号32位数值。

    更新日志：
    2026.10.23 - 对应 ListingLimits。
    """

    参考价: int
    最高价: int


@dataclass
class 挂单_类:
    """
    请求挂牌；数量仅对股票必填。

    更新日志：
    2026.10.23 - 对应 Listing。
    """

    种类: int = 0
    项目: int = 0
    价格: int = 0
    数量: int = 0


@dataclass
class 报价_类:
    """
    卖家和索引附带出售项的值快照，不随原表压紧改变。

    更新日志：
    2026.10.23 - 对应 Quote。
    """

    卖家: int
    索引: int
    出售项: 出售项_类


@dataclass
class 交易结果_类:
    """
    原规则处理结果；消息来自公开重制源码的英文状态文本。

    更新日志：
    2026.10.23 - 对应 Result，不附加商业UI文案。
    """

    已应用: bool = False
    消息: str = ""
    公司易主: bool = False


@dataclass
class 电脑交易结果_类:
    """
    一次电脑交易回合的清理、挂牌、改价和首次购买记录。

    更新日志：
    2026.10.23 - 对应 AiResult。
    """

    移除: int = 0
    挂牌: int = 0
    改价: int = 0
    购买: 报价_类 | None = None


class 交易_类:
    """
    玩家私下出售与电脑市场策略；融资对账由游戏会话另行执行。

    更新日志：
    2026.10.23 - 移植 trading.cpp，保留清理游标与不使用的记录字段。
    """

    @staticmethod
    def _整数(arg_值: int) -> int:
        return ((arg_值 + 0x80000000) & 0xFFFFFFFF) - 0x80000000

    @staticmethod
    def _浮点(arg_位: int) -> float:
        return struct.unpack("<f", struct.pack("<I", arg_位))[0]

    @staticmethod
    def _库存(arg_世: 世界_类, arg_槽: int) -> 库存_类:
        记录 = arg_世.玩家[arg_槽].记录
        return 库存_类(
            记录.卡片, arg_世.卡供应, 服务_类.卡价, 记录.道具, arg_世.道具供应, 服务_类.道具价
        )

    @staticmethod
    def _活跃(arg_世: 世界_类, arg_槽: int) -> bool:
        return (
            0 <= arg_槽 < min(len(arg_世.玩家), len(arg_世.出售表))
            and arg_世.玩家[arg_槽].记录.控制标志 != 0
        )

    @staticmethod
    def _普通地(arg_世: 世界_类, arg_号: int) -> bool:
        return 2000 < arg_号 < 4000 and arg_号 - 2000 < len(arg_世.地产)

    @staticmethod
    def _设施(arg_世: 世界_类, arg_号: int) -> bool:
        return 4000 < arg_号 < 6000 and arg_号 - 4000 < len(arg_世.设施)

    @classmethod
    def _地产(cls, arg_世: 世界_类, arg_号: int) -> tuple[int, int, int, int] | None:
        if cls._普通地(arg_世, arg_号):
            地 = arg_世.地产[arg_号 - 2000]
            主, 型, 级 = 地.经济.业主, 地.经济.连锁, 地.经济.等级
        elif cls._设施(arg_世, arg_号):
            地 = arg_世.设施[arg_号 - 4000]
            主, 型, 级 = 地.业主, 地.类型, 地.等级
        else:
            return None
        值 = cls._整数(cls._整数(地.地价 + cls._整数(地.每级造价 * 级)) * arg_世.头.物价)
        return 主, 型, 级, 值

    @classmethod
    def _库存价(cls, arg_世: 世界_类, arg_类: int, arg_号: int) -> int | None:
        if arg_类 == 3 and 1 <= arg_号 <= 13:
            return cls._整数(cls._整数(服务_类.道具价[arg_号 - 1] * 100) * arg_世.头.物价)
        if arg_类 == 4 and 1 <= arg_号 <= 30:
            return cls._整数(cls._整数(服务_类.卡价[arg_号 - 1] * 100) * arg_世.头.物价)
        return None

    @classmethod
    def _有效(cls, arg_世: 世界_类, arg_卖家: int, arg_项: 出售项_类) -> bool:
        if not 0 <= arg_卖家 < len(arg_世.玩家):
            return False
        玩家 = arg_世.玩家[arg_卖家]
        号 = arg_项.项目
        if arg_项.种类 == 1:
            return 0 <= 号 < len(玩家.持仓) and arg_项.数量 <= 玩家.持仓[号].数量
        if arg_项.种类 == 2:
            地 = cls._地产(arg_世, 号)
            return 地 is not None and 地[:3] == (arg_卖家 + 1, arg_项.地产类型, arg_项.地产等级)
        if arg_项.种类 == 3:
            return 1 <= 号 <= 13 and 玩家.记录.道具[号 - 1] != 0
        if arg_项.种类 == 4:
            return 1 <= 号 <= 30 and 号 in 玩家.记录.卡片
        return True

    @classmethod
    def api_可售项目(cls, arg_世: 世界_类, arg_卖家: int) -> list[可售项目_类]:
        if not cls._活跃(arg_世, arg_卖家):
            return []
        玩家 = arg_世.玩家[arg_卖家]
        结果 = [
            可售项目_类(1, i, min(股.数量, 65535)) for i, 股 in enumerate(玩家.持仓) if 股.数量 > 0
        ]
        结果 += [
            可售项目_类(2, 2000 + i)
            for i in range(1, min(len(arg_世.地产), 2000))
            if arg_世.地产[i].经济.业主 == arg_卖家 + 1
        ]
        结果 += [
            可售项目_类(2, 4000 + i)
            for i in range(1, min(len(arg_世.设施), 2000))
            if arg_世.设施[i].业主 == arg_卖家 + 1
        ]
        结果 += [可售项目_类(3, i + 1) for i in range(13) if 玩家.记录.道具[i]]
        结果 += [可售项目_类(4, i) for i in range(1, 31) if i in 玩家.记录.卡片]
        return 结果

    @classmethod
    def api_限价(
        cls, arg_世: 世界_类, arg_卖家: int, arg_类: int, arg_号: int, arg_数量: int = 0
    ) -> 挂牌限价_类 | None:
        if not cls._活跃(arg_世, arg_卖家):
            return None
        玩家 = arg_世.玩家[arg_卖家]
        if arg_类 == 1:
            if (
                not 0 <= arg_号 < len(玩家.持仓)
                or arg_数量 == 0
                or arg_数量 > 玩家.持仓[arg_号].数量
            ):
                return None
            报价 = cls._浮点(arg_世.股票[arg_号].浮点位[2])
            if not math.isfinite(报价) or 报价 <= 0:
                return None
            参考 = (扩展数_类.api_从值(arg_数量) * 扩展数_类.api_从值(报价)).api_整数()
        elif arg_类 == 2:
            地 = cls._地产(arg_世, arg_号)
            if 地 is None or 地[0] != arg_卖家 + 1:
                return None
            参考 = 地[3]
        elif arg_类 in (3, 4):
            if not cls._有效(arg_世, arg_卖家, 出售项_类(种类=arg_类, 项目=arg_号)):
                return None
            参考 = cls._库存价(arg_世, arg_类, arg_号)
        else:
            return None
        上限 = cls._整数(参考 * 10)
        if 参考 <= 0 or 上限 <= 0:
            return None
        return 挂牌限价_类(参考, 上限)

    @classmethod
    def api_报价(cls, arg_世: 世界_类) -> list[报价_类]:
        结果 = []
        for 卖家 in range(min(len(arg_世.玩家), len(arg_世.出售表))):
            if not cls._活跃(arg_世, 卖家):
                continue
            for i, 项 in enumerate(arg_世.出售表[卖家]):
                if 1 <= 项.种类 <= 4 and cls._有效(arg_世, 卖家, 项):
                    结果.append(报价_类(卖家, i, replace(项)))
        return 结果

    @classmethod
    def api_挂牌(cls, arg_世: 世界_类, arg_卖家: int, arg_单: 挂单_类) -> 交易结果_类:
        限价 = cls.api_限价(arg_世, arg_卖家, arg_单.种类, arg_单.项目, arg_单.数量)
        if 限价 is None or not 1 <= arg_单.价格 <= 限价.最高价:
            return 交易结果_类(消息="Invalid listing or price")
        项 = next(
            (
                项
                for 项 in arg_世.出售表[arg_卖家]
                if 项.种类 == 0 or (项.种类 == arg_单.种类 and 项.项目 == arg_单.项目)
            ),
            None,
        )
        if 项 is None:
            return 交易结果_类(消息="All seven listing slots are occupied")
        项.种类, 项.标志, 项.项目, 项.价格 = arg_单.种类, 0, arg_单.项目, arg_单.价格
        if arg_单.种类 == 1:
            项.数量 = arg_单.数量
        elif arg_单.种类 == 2:
            地 = cls._地产(arg_世, arg_单.项目)
            项.地产类型, 项.地产等级 = 地[1:3]
        return 交易结果_类(True, "Listed")

    @staticmethod
    def api_取消(arg_世: 世界_类, arg_卖家: int, arg_索引: int) -> bool:
        if (
            not 0 <= arg_卖家 < len(arg_世.出售表)
            or not 0 <= arg_索引 < 7
            or arg_世.出售表[arg_卖家][arg_索引].种类 == 0
        ):
            return False
        列 = arg_世.出售表[arg_卖家]
        列[arg_索引:] = 列[arg_索引 + 1 :] + [出售项_类()]
        return True

    @classmethod
    def api_清理(cls, arg_世: 世界_类) -> int:
        移除 = 0
        for 卖家 in range(min(len(arg_世.玩家), len(arg_世.出售表))):
            已删除, 索引 = False, 0
            # 原0x42483e不重置删除标志，之后七次检查停在压紧后的当前项。
            for _ in range(7):
                if not cls._有效(arg_世, 卖家, arg_世.出售表[卖家][索引]):
                    移除 += int(cls.api_取消(arg_世, 卖家, 索引))
                    已删除 = True
                if not 已删除:
                    索引 += 1
        return 移除

    @classmethod
    def api_购买(cls, arg_世: 世界_类, arg_买家: int, arg_卖家: int, arg_索引: int) -> 交易结果_类:
        if (
            not cls._活跃(arg_世, arg_买家)
            or not cls._活跃(arg_世, arg_卖家)
            or arg_买家 == arg_卖家
            or not 0 <= arg_索引 < 7
        ):
            return 交易结果_类(消息="Invalid buyer or seller")
        项 = replace(arg_世.出售表[arg_卖家][arg_索引])
        if 项.价格 <= 0 or not cls._有效(arg_世, arg_卖家, 项):
            return 交易结果_类(消息="Listing is no longer available")
        买, 卖 = arg_世.玩家[arg_买家], arg_世.玩家[arg_卖家]
        if 买.记录.现金 < 项.价格:
            return 交易结果_类(消息="Not enough cash")
        易主 = False
        if 项.种类 == 1:
            if 项.数量 == 0:
                return 交易结果_类(消息="Invalid stock quantity")
            购股, 售股 = 买.持仓[项.项目], 卖.持仓[项.项目]
            旧成本 = cls._浮点(购股.成本位)
            if not math.isfinite(旧成本) or not 0 <= 购股.数量 <= 2147483647 - 项.数量:
                return 交易结果_类(消息="Invalid stock holding")
            E = 扩展数_类.api_从值
            原成本 = (E(购股.数量) * E(旧成本)).api_整数()
            购股.数量 = cls._整数(购股.数量 + 项.数量)
            售股.数量 -= 项.数量
            if 售股.数量 == 0:
                售股.成本位 = 0
            购股.成本位 = (E(cls._整数(原成本 + 项.价格)) / E(购股.数量)).api_单精度位()
            易主 = 股市_类.api_更新业主(arg_世, arg_买家, 项.项目)
        elif 项.种类 == 2:
            if cls._普通地(arg_世, 项.项目):
                arg_世.地产[项.项目 - 2000].经济.业主 = arg_买家 + 1
            else:
                arg_世.设施[项.项目 - 4000].业主 = arg_买家 + 1
        elif 项.种类 == 3:
            if 买.记录.道具[项.项目 - 1] >= 9:
                return 交易结果_类(消息="Tool inventory is full")
            cls._库存(arg_世, arg_卖家).api_用道具(项.项目)
            cls._库存(arg_世, arg_买家).api_收道具(项.项目)
        elif 项.种类 == 4:
            if cls._库存(arg_世, arg_买家).api_卡数() >= 15:
                return 交易结果_类(消息="Card inventory is full")
            cls._库存(arg_世, arg_卖家).api_用卡(项.项目)
            cls._库存(arg_世, arg_买家).api_收卡(项.项目)
        else:
            return 交易结果_类(消息="Unknown listing type")
        买.记录.现金 -= 项.价格
        卖.记录.银行 = cls._整数(卖.记录.银行 + 项.价格)
        买.状态.累计支出 = (买.状态.累计支出 + 项.价格) & 0xFFFFFFFF
        卖.状态.累计收入 = (卖.状态.累计收入 + 项.价格) & 0xFFFFFFFF
        cls.api_取消(arg_世, arg_卖家, arg_索引)
        return 交易结果_类(True, "Purchased", 易主)

    @classmethod
    def api_电脑回合(cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_演员: int) -> 电脑交易结果_类:
        结果 = 电脑交易结果_类()
        if not cls._活跃(arg_世, arg_演员):
            return 结果
        结果.移除 = cls.api_清理(arg_世)
        玩家 = arg_世.玩家[arg_演员]
        if arg_随机.api_下一个() % 15 == 0:
            数量 = cls._库存(arg_世, arg_演员).api_卡数()
            类 = 4
            候选 = []
            if 数量 > 12:
                候选 = [
                    玩家.记录.卡片[i]
                    for i in range(数量)
                    for j in range(数量)
                    if i != j and 玩家.记录.卡片[i] == 玩家.记录.卡片[j]
                ]
            if not 候选:
                类 = 3
                候选 = [
                    i + 1
                    for i in range(13)
                    if 玩家.记录.道具[i] >= 3
                    or (玩家.记录.道具[i] and 服务_类.道具偏好[i] - 玩家.状态.救援策略 == 2)
                ]
            if 候选:
                号 = 候选[arg_随机.api_下一个() % len(候选)]
                if arg_世.出售表[arg_演员][-1].种类 != 0:
                    cls.api_取消(arg_世, arg_演员, 0)
                    结果.移除 += 1
                价 = cls._库存价(arg_世, 类, 号)
                if 价 is not None and cls.api_挂牌(arg_世, arg_演员, 挂单_类(类, 号, 价)).已应用:
                    结果.挂牌 += 1
        if arg_随机.api_下一个() % 3 == 0:
            for 项 in arg_世.出售表[arg_演员]:
                价 = cls._库存价(arg_世, 项.种类, 项.项目)
                if 价 is not None and 价 != 项.价格:
                    项.价格 = 价
                    结果.改价 += 1
        if arg_随机.api_下一个() % 4 == 0:
            for 卖家 in range(min(len(arg_世.玩家), len(arg_世.出售表))):
                if 卖家 == arg_演员 or not cls._活跃(arg_世, 卖家):
                    continue
                for i in range(7):
                    项 = replace(arg_世.出售表[卖家][i])
                    划算 = False
                    if 项.种类 == 1 and 项.项目 < 12 and 项.数量:
                        E = 扩展数_类.api_从值
                        每股 = (E(项.价格) / E(项.数量)).api_整数()
                        划算 = 每股 < cls._浮点(arg_世.股票[项.项目].浮点位[2])
                    elif 项.种类 == 2:
                        地 = cls._地产(arg_世, 项.项目)
                        if 地:
                            划算 = (
                                cls._整数(3 * 地[3]) > 项.价格
                                and cls._整数(2 * 项.价格) < 玩家.记录.现金
                            )
                    if 划算 and cls.api_购买(arg_世, arg_演员, 卖家, i).已应用:
                        结果.购买 = 报价_类(卖家, i, 项)
                        return 结果
        return 结果
