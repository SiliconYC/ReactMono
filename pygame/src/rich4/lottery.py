# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/lottery.cpp；开奖动画的消费不混入规则随机流。
# ◑ 导入
from dataclasses import dataclass
from enum import IntEnum

from rich4.random import 随机数_类
from rich4.world import 世界_类
from rich4.world_player import 世界玩家_类


# ◕ 功能
class 彩票状态错误_类(ValueError):
    """
    对应彩票模块 SaveError，非法所有者不能进入开奖索引。

    更新日志：
    2026.10.23 - 区分状态损坏与参数越界。
    """


class 购票结果_类(IntEnum):
    """
    原 Purchase 的状态编号。

    更新日志：
    2026.10.23 - 对应四种购票结果。
    """

    成功 = 0
    已售出 = 1
    现金不足 = 2
    玩家未活跃 = 3


@dataclass
class 开奖结果_类:
    """
    一次规则开奖结果，不包含定时器和显示动画。

    更新日志：
    2026.10.23 - 对应 lottery::Draw。
    """

    已开奖: bool = False
    号码: int = 0
    赢家: int | None = None
    奖金: int = 0
    仅售出票: bool = False


class 彩票_类:
    """
    三十六号票的交易、电脑选择、流奖和奖金结算。

    更新日志：
    2026.10.23 - 移植全部 lottery.cpp，保留现金和累计收入回绕。
    """

    票价 = 1000

    @staticmethod
    def _整数(arg_值: int) -> int:
        return ((arg_值 + 0x80000000) & 0xFFFFFFFF) - 0x80000000

    @staticmethod
    def _玩家(arg_世: 世界_类, arg_槽: int) -> 世界玩家_类:
        if not 0 <= arg_槽 < len(arg_世.玩家):
            raise IndexError("彩票玩家越界")
        return arg_世.玩家[arg_槽]

    @staticmethod
    def _验证(arg_世: 世界_类) -> None:
        if len(arg_世.玩家) > 4 or len(arg_世.彩票) != 36:
            raise 彩票状态错误_类("彩票要求原四槽玩家与三十六张票")
        if any(not 0 <= 业主 <= len(arg_世.玩家) for 业主 in arg_世.彩票):
            raise 彩票状态错误_类("彩票所有者超出玩家槽")

    @classmethod
    def api_可售号码(cls, arg_世: 世界_类) -> list[int]:
        cls._验证(arg_世)
        return [i + 1 for i, 业主 in enumerate(arg_世.彩票) if 业主 == 0]

    @classmethod
    def api_购票(cls, arg_世: 世界_类, arg_槽: int, arg_号: int) -> 购票结果_类:
        if not 1 <= arg_号 <= len(arg_世.彩票):
            raise IndexError("彩票号码必须为1..36")
        cls._验证(arg_世)
        玩家 = cls._玩家(arg_世, arg_槽)
        if 玩家.记录.控制标志 == 0:
            return 购票结果_类.玩家未活跃
        if arg_世.彩票[arg_号 - 1] != 0:
            return 购票结果_类.已售出
        if 玩家.记录.现金 < cls.票价:
            return 购票结果_类.现金不足
        arg_世.彩票[arg_号 - 1] = arg_槽 + 1
        玩家.记录.现金 -= cls.票价
        arg_世.公共基金 = cls._整数(arg_世.公共基金 + cls.票价)
        return 购票结果_类.成功

    @classmethod
    def api_随机购票(cls, arg_世: 世界_类, arg_随机: 随机数_类, arg_槽: int) -> int | None:
        玩家 = cls._玩家(arg_世, arg_槽)
        if 玩家.记录.控制标志 == 0 or 玩家.记录.现金 <= cls.票价:
            return None
        号码 = cls.api_可售号码(arg_世)
        if not 号码:
            return None
        号 = 号码[arg_随机.api_下一个() % len(号码)]
        if cls.api_购票(arg_世, arg_槽, 号) != 购票结果_类.成功:
            raise 彩票状态错误_类("选择期间彩票状态改变")
        return 号

    @classmethod
    def api_退票(cls, arg_世: 世界_类, arg_槽: int) -> None:
        cls._玩家(arg_世, arg_槽)
        for i, 业主 in enumerate(arg_世.彩票):
            if 业主 == arg_槽 + 1:
                arg_世.彩票[i] = 0

    @classmethod
    def api_开奖(cls, arg_世: 世界_类, arg_随机: 随机数_类) -> 开奖结果_类:
        cls._验证(arg_世)
        持有 = [0] * 4
        已售: list[int] = []
        for i, 业主 in enumerate(arg_世.彩票):
            if 业主:
                持有[业主 - 1] += 1
                已售.append(i + 1)
        if not 已售:
            return 开奖结果_类()
        结果 = 开奖结果_类(已开奖=True, 仅售出票=any(数 > 10 for 数 in 持有))
        值 = arg_随机.api_下一个()
        结果.号码 = 已售[值 % len(已售)] if 结果.仅售出票 else 值 % 36 + 1
        业主 = arg_世.彩票[结果.号码 - 1]
        if 业主:
            结果.赢家 = 业主 - 1
            结果.奖金 = arg_世.公共基金
            玩家 = arg_世.玩家[结果.赢家]
            玩家.记录.现金 = cls._整数(玩家.记录.现金 + 结果.奖金)
            玩家.状态.累计收入 = (玩家.状态.累计收入 + 结果.奖金) & 0xFFFFFFFF
            arg_世.公共基金 = 0
            arg_世.彩票[:] = [0] * 36
        return 结果

    @staticmethod
    def api_开奖日(arg_日期: tuple[int, int, int]) -> bool:
        return arg_日期[0] == 15
