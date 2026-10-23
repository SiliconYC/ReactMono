# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/calendar.cpp；不能使用 datetime 替换原四年闰规则。
# ◑ 导入
from dataclasses import dataclass


# ◕ 功能
@dataclass(frozen=True)
class 日期_类:
    """
    Rich4 的日期域为 1998..65535；世纪年份仍按整除四闰。

    更新日志：
    2026.10.23 - 对应 calendar 模块的数值和日期运算。
    """

    年: int
    月: int
    日: int

    def __post_init__(self) -> None:
        if not 1998 <= self.年 <= 65535 or not 1 <= self.月 <= 12:
            raise ValueError("日期超出 Rich4 范围")
        if not 1 <= self.日 <= self.api_月天数(self.年, self.月):
            raise ValueError("日期超出月份范围")

    @staticmethod
    def api_月天数(arg_年: int, arg_月: int) -> int:
        if not 1 <= arg_月 <= 12:
            raise ValueError("月份必须为 1..12")
        return (
            29
            if arg_月 == 2 and arg_年 % 4 == 0
            else (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)[arg_月 - 1]
        )

    @staticmethod
    def _年前天数(arg_年: int) -> int:
        return (arg_年 - 1998) * 365 + (arg_年 - 1) // 4 - 1997 // 4

    def api_天数(self) -> int:
        return (
            self._年前天数(self.年)
            + sum(self.api_月天数(self.年, 月) for 月 in range(1, self.月))
            + self.日
            - 1
        )

    @classmethod
    def api_从天数(cls, arg_天: int) -> "日期_类":
        if not 0 <= arg_天 < cls._年前天数(65536):
            raise ValueError("天数超出 Rich4 范围")
        年 = 1998 + arg_天 // 1461 * 4
        余 = arg_天 % 1461
        while 余 >= (366 if 年 % 4 == 0 else 365):
            余 -= 366 if 年 % 4 == 0 else 365
            年 += 1
        月 = 1
        while 余 >= cls.api_月天数(年, 月):
            余 -= cls.api_月天数(年, 月)
            月 += 1
        return cls(年, 月, 余 + 1)

    def api_星期(self) -> int:
        return (self.api_天数() + 4) % 7

    def api_下一天(self) -> tuple["日期_类", bool]:
        新日 = self.api_加天数(1)
        return 新日, 新日.月 != self.月

    def api_加天数(self, arg_天: int) -> "日期_类":
        return self.api_从天数(self.api_天数() + arg_天)

    def api_日期差(self, arg_另日: "日期_类") -> int:
        return arg_另日.api_天数() - self.api_天数()

    @staticmethod
    def api_打包间隔(arg_日期: int, arg_间隔: int) -> int:
        结果 = (arg_日期 + arg_间隔) & 0xFFFFFFFF
        if arg_间隔 & 0xFF00 and 结果 & 0xFF00 > 0xC00:
            结果 = (结果 + 0xF400) & 0xFFFFFFFF
        return 结果
