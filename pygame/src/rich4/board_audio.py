# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/board_audio.hpp，纯表现策略，不消费游戏随机数或修改世界。
# ◑ 导入
from rich4.audio_types import 循环通道_类, 音乐_类, 音频策略宿主_基类
from rich4.calendar import 日期_类
from rich4.game_types import 决策_类, 决策种类_类
from rich4.holidays import 节日_类
from rich4.world import 世界_类


# ◕ 功能
class 主板声音_类:
    """
    原步行/交通/炸弹及决策/节日音乐资源选择。

    更新日志：
    2026.10.24 - 水面优先交通、机器人特例、原农历表边界保留。
    """

    @staticmethod
    def api_步行(arg_世界: 世界_类, arg_槽: int) -> int | None:
        if arg_槽 < 0:
            raise ValueError("槽位不是无符号整数")
        w = arg_世界

        def 水上(arg_节点: int) -> bool:
            return arg_节点 < len(w.节点) and bool(w.节点[arg_节点].标志 & 0x80000000)

        if arg_槽 < 4:
            if arg_槽 >= len(w.玩家):
                return None
            p = w.玩家[arg_槽].记录
            return 47 if 水上(p.节点) else (44, 45, 46, 53)[p.交通 & 3]
        if arg_槽 == 8:
            return 38
        if arg_槽 - 4 < len(w.特殊角色):
            return 47 if 水上(w.特殊角色[arg_槽 - 4].节点) else 44
        return None

    @staticmethod
    def api_炸弹(arg_世界: 世界_类, arg_槽: int) -> int | None:
        if arg_槽 < 0:
            raise ValueError("槽位不是无符号整数")
        if arg_槽 < 4 and arg_槽 < len(arg_世界.玩家) and arg_世界.玩家[arg_槽].状态.附身炸弹:
            return 32
        return None

    @staticmethod
    def api_决策音乐(arg_决策: 决策_类) -> 音乐_类 | None:
        kind, K = arg_决策.种类, 决策种类_类
        if kind == K.银行:
            return 音乐_类.银行
        if kind == K.拍卖:
            return 音乐_类.拍卖
        if kind in (K.商店, K.彩票):
            return 音乐_类.商店
        if kind in (K.魔法类别, K.魔法效果):
            return 音乐_类.魔法
        if kind == K.救援:
            return 音乐_类.医院 if "住院" in arg_决策.提示 else 音乐_类.监狱
        return None

    @staticmethod
    def api_节庆音乐(arg_世界: 世界_类) -> 音乐_类 | None:
        h = arg_世界.头
        if h.阶段 != 0:
            return None
        day, month, year = h.日期
        date = 日期_类(year, month, day)
        if month == 12 and day == 25:
            return 音乐_类.圣诞
        if h.地图 <= 1:
            lunar = 节日_类.api_农历(date)
            if lunar is not None and lunar[1] == 1 and 1 <= lunar[2] <= 3:
                return 音乐_类.新年
        return None


class 音乐导演_类:
    """
    原上下文公共前缀/单层替换与只退栈300毫秒延迟。

    更新日志：
    2026.10.24 - 延迟使用uint64回绕，需求恢复则撤销待退栈。
    """

    def __init__(self) -> None:
        self._已推: list[音乐_类] = []
        self._待退, self._退起 = False, 0

    def api_更新(self, arg_音频: 音频策略宿主_基类, arg_需求: list[音乐_类], arg_时: int) -> None:
        if arg_需求 == self._已推:
            self._待退 = False
            return
        common = 0
        while (
            common < len(arg_需求)
            and common < len(self._已推)
            and arg_需求[common] == self._已推[common]
        ):
            common += 1
        if common == len(arg_需求):
            if not self._待退:
                self._待退, self._退起 = True, arg_时
            if (arg_时 - self._退起) & 0xFFFFFFFFFFFFFFFF < 300:
                return
        self._待退 = False
        if len(self._已推) == len(arg_需求) and common + 1 == len(arg_需求):
            arg_音频.api_换音乐(arg_需求[-1])
            self._已推[-1] = arg_需求[-1]
            return
        while len(self._已推) > common:
            arg_音频.api_弹音乐()
            self._已推.pop()
        for wanted in arg_需求[common:]:
            arg_音频.api_推音乐(wanted)
            self._已推.append(wanted)

    def api_忘记(self) -> None:
        self._已推.clear()
        self._待退 = False


class 步行声音_类:
    """
    原走路与附身炸弹循环，在最后可见移动后延迟150毫秒停止。

    更新日志：
    2026.10.24 - 同步播放只作用于各自通道，不碰转盘通道。
    """

    def __init__(self) -> None:
        self._上走 = 0

    def api_更新(
        self,
        arg_音频: 音频策略宿主_基类,
        arg_步行: int | None,
        arg_炸弹: int | None,
        arg_时: int,
    ) -> None:
        if arg_步行 is not None:
            self._上走 = arg_时
            arg_音频.api_播循环(arg_步行, 循环通道_类.步行)
            if arg_炸弹 is not None:
                arg_音频.api_播循环(arg_炸弹, 循环通道_类.炸弹)
            else:
                arg_音频.api_停循环(循环通道_类.炸弹)
            return
        if (arg_时 - self._上走) & 0xFFFFFFFFFFFFFFFF >= 150:
            self.api_停止(arg_音频)

    def api_停止(self, arg_音频: 音频策略宿主_基类) -> None:
        arg_音频.api_停循环(循环通道_类.步行)
        arg_音频.api_停循环(循环通道_类.炸弹)
