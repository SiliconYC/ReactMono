# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/holidays.cpp；原农历表之外不推测现代节日。
# ◑ 导入
from bisect import bisect_right
from dataclasses import dataclass

from rich4.calendar import 日期_类
from rich4.holiday_tables import 节日表_类


# ◕ 功能
@dataclass(frozen=True)
class 庆祝_类:
    """
    原节日影片、音效和音乐编号，零值表示无此项。

    更新日志：
    2026.10.23 - 对应 holidays::Celebration。
    """

    影片: int = 0
    音效: int = 0
    音乐: int = 0


class 节日_类:
    """
    原八图休市/节日/庆祝表和九十天贷款到期顺延。

    更新日志：
    2026.10.23 - 保留比较日期寄存值与第几周规则的原行为。
    """

    农历起点 = tuple(项[0] for 项 in 节日表_类.农历)
    首图 = (4, 28, 47, 67, 87, 108, 95, 118)

    @staticmethod
    def _地图(arg_图: int, arg_阶段: int) -> int:
        if not 0 <= arg_图 <= 3 or not 0 <= arg_阶段 <= 1:
            raise ValueError("节日只支持原八图")
        return arg_阶段 * 4 + arg_图

    @classmethod
    def api_农历(cls, arg_日期: 日期_类) -> tuple[int, int, int] | None:
        天 = arg_日期.api_天数()
        if 天 > 8400:
            return None
        起点, 首日 = 节日表_类.农历[bisect_right(cls.农历起点, 天) - 1]
        编码 = 首日 + 天 - 起点
        # 首项为农历1997年，不能套用要求公历历元>=1998的日期构造验证。
        return 编码 >> 16 & 0xFFFF, 编码 >> 8 & 255, 编码 & 255

    @classmethod
    def api_节日行(cls, arg_日期: 日期_类, arg_图: int, arg_阶段: int) -> int | None:
        表 = cls._地图(arg_图, arg_阶段)
        农历 = cls.api_农历(arg_日期)
        比较 = arg_日期.月 << 8 | arg_日期.日
        for 行, (标志, 历法, 月, 日或周, 星期) in enumerate(节日表_类.规则[表]):
            目标 = 0
            if 历法 == 0:
                目标 = 月 << 8 | 日或周
            elif 历法 == 1:
                if 农历 is None:
                    continue
                比较 = 农历[1] << 8 | 农历[2]
                目标 = 月 << 8 | 日或周
            else:
                if 农历 is None:
                    continue
                首周 = 日期_类(arg_日期.年, 月, 1).api_星期()
                基值 = 7 if 星期 < 首周 else 星期
                日 = 基值 - 首周 + 1 + (日或周 - 1) * 7
                if 日 <= 日期_类.api_月天数(arg_日期.年, 月):
                    目标 = 月 << 8 | 日
            if 比较 == 目标 and 标志 & 0x80 == 0:
                return 行
        return None

    @classmethod
    def api_休市(cls, arg_日期: 日期_类, arg_图: int, arg_阶段: int) -> bool:
        表 = cls._地图(arg_图, arg_阶段)
        if arg_日期.api_星期() == 0:
            return True
        行 = cls.api_节日行(arg_日期, arg_图, arg_阶段)
        return 行 is not None and 节日表_类.规则[表][行][0] != 0

    @classmethod
    def api_节日图片(cls, arg_日期: 日期_类, arg_图: int, arg_阶段: int) -> int | None:
        行 = cls.api_节日行(arg_日期, arg_图, arg_阶段)
        return None if 行 is None else cls.首图[arg_阶段 * 4 + arg_图] + 行

    @classmethod
    def api_庆祝(cls, arg_日期: 日期_类, arg_图: int, arg_阶段: int) -> 庆祝_类 | None:
        表 = cls._地图(arg_图, arg_阶段)
        行 = cls.api_节日行(arg_日期, arg_图, arg_阶段)
        if 行 is None:
            return None
        for 图, 号, 标志, 影片, 音效, 音乐 in 节日表_类.庆祝:
            if 图 == 表 and 号 == 行 and 标志 & 5:
                return 庆祝_类(
                    影片 if 标志 & 1 else 0, 音效 if 标志 & 1 else 0, 音乐 if 标志 & 4 else 0
                )
        return None

    @classmethod
    def api_贷款到期(cls, arg_日期: 日期_类, arg_图: int, arg_阶段: int) -> 日期_类:
        日期 = arg_日期.api_加天数(90)
        while cls.api_休市(日期, arg_图, arg_阶段):
            日期 = 日期.api_下一天()[0]
        return 日期
