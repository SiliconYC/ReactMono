# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ minigames.cpp/hpp；所有场景/声效指令按原tick次序产生。
# ◑ 导入
from dataclasses import dataclass
from enum import IntEnum

from rich4.events import 事件_类
from rich4.numeric import 扩展数_类
from rich4.random import 随机数_类
from rich4.stocks import 股市_类


# ◕ 功能
class 小游戏阶段_类(IntEnum):
    """
    原开场、READY/GO、游玩、分数停留和结束五阶段。

    更新日志：
    2026.10.23 - 对应minigames::Stage。
    """

    开场, 准备, 游玩, 结算, 完成 = range(5)


class 小游戏种类_类(IntEnum):
    """
    原三游戏编号与对应原定时器间隔。

    更新日志：
    2026.10.23 - 对应Game、game_for_node_kind和tick_ms。
    """

    企鹅, 气球, 天降 = range(3)

    @classmethod
    def api_节点游戏(cls, arg_节点类: int) -> "小游戏种类_类":
        return cls.企鹅 if arg_节点类 == 6 else cls.气球 if arg_节点类 == 7 else cls.天降

    def api_间隔(self) -> int:
        return 50 if self == self.天降 else 100


@dataclass(frozen=True)
class 小游戏精灵_类:
    """
    一帧绘制命令，保留原资源锚点、16.16缩放和绘制次序。

    更新日志：
    2026.10.23 - 对应Sprite。
    """

    库: str = "p"
    条目: int = 0
    帧: int = 0
    x: int = 0
    y: int = 0
    缩放: int = 0


@dataclass(frozen=True)
class 声音请求_类:
    """
    音效操作0播放、1循环、2停止，不触及规则随机流。

    更新日志：
    2026.10.23 - 对应Cue。
    """

    操作: int
    音效: int


@dataclass(frozen=True)
class 图框_类:
    """
    原SPR帧的宽高与锚点，天降碰撞使用真实资源帧框。

    更新日志：
    2026.10.23 - 对应Box。
    """

    宽: int = 0
    高: int = 0
    原x: int = 0
    原y: int = 0


class 小游戏随机_类:
    """
    独立Watcom流及32位调用计数，供GameSession精确接回共享流。

    更新日志：
    2026.10.23 - 对应Stream。
    """

    def __init__(self, arg_种: int) -> None:
        self.随机, self.次数 = 随机数_类(arg_种), 0

    def api_下一个(self) -> int:
        self.次数 = (self.次数 + 1) & 0xFFFFFFFF
        return self.随机.api_下一个()


class 小游戏_类:
    """
    原模态准备片与结束时钟，子类仅发绘制和声音指令。

    更新日志：
    2026.10.23 - 对应Base。
    """

    def __init__(self, arg_种: int) -> None:
        self.随机 = 小游戏随机_类(arg_种)
        self.阶段 = 小游戏阶段_类.开场
        self.剩余帧 = self.倒数 = self.停留 = 0
        self.场景: list[小游戏精灵_类] = []
        self.声音: list[声音请求_类] = []

    def api_开始(self) -> None:
        if self.阶段 == 小游戏阶段_类.准备:
            self.阶段 = 小游戏阶段_类.游玩

    def api_取声音(self) -> list[声音请求_类]:
        声, self.声音 = self.声音, []
        return 声

    def _声(self, arg_效: int, arg_操作: int = 0) -> None:
        self.声音.append(声音请求_类(arg_操作, arg_效))

    def _画(self, arg_条: int, arg_帧: int, arg_x: int, arg_y: int, arg_缩: int = 0) -> None:
        self.场景.append(小游戏精灵_类("p", arg_条 & 65535, arg_帧 & 65535, arg_x, arg_y, arg_缩))

    @staticmethod
    def _短(arg_数: int) -> int:
        return ((arg_数 + 32768) & 65535) - 32768


@dataclass
class 企鹅格_类:
    """
    原九乘九格子，低四位宝物、高位冰屋遮挡，x零为无效格。

    更新日志：
    2026.10.23 - 对应Penguin::Cell。
    """

    x: int = 0
    y: int = 0
    标志: int = 0


class 企鹅_类(小游戏_类):
    """
    原企鹅挖宝DDA滑行、四帧移动/挖掘、宝物及结算动画状态机。

    更新日志：
    2026.10.23 - 对应Penguin，定时器100ms。
    """

    格表: tuple[tuple[int, int, int], ...] = (
        (0, 0, 0),
        (0, 0, 0),
        (0, 0, 0),
        (80, 153, 0),
        (128, 129, 0),
        (176, 105, 0),
        (224, 81, 0),
        (0, 0, 0),
        (0, 0, 0),
        (0, 0, 0),
        (32, 225, 0),
        (80, 201, 0),
        (128, 177, 0),
        (176, 153, 0),
        (224, 129, 0),
        (272, 105, 0),
        (320, 81, 0),
        (0, 0, 0),
        (0, 0, 0),
        (80, 249, 0),
        (128, 225, 0),
        (176, 201, 0),
        (224, 177, 0),
        (272, 153, 0),
        (320, 129, 0),
        (368, 105, 0),
        (416, 81, 0),
        (80, 297, 0),
        (128, 273, 0),
        (176, 249, 0),
        (224, 225, 16),
        (272, 201, 16),
        (320, 177, 16),
        (368, 153, 0),
        (416, 129, 0),
        (464, 105, 0),
        (128, 321, 0),
        (176, 297, 0),
        (224, 273, 0),
        (272, 249, 0),
        (0, 0, 0),
        (368, 201, 16),
        (416, 177, 0),
        (464, 153, 0),
        (512, 129, 0),
        (176, 345, 0),
        (224, 321, 0),
        (272, 297, 0),
        (320, 273, 0),
        (368, 249, 0),
        (416, 225, 16),
        (464, 201, 0),
        (512, 177, 0),
        (560, 153, 0),
        (224, 369, 0),
        (272, 345, 0),
        (320, 321, 0),
        (368, 297, 0),
        (416, 273, 0),
        (464, 249, 0),
        (512, 225, 0),
        (560, 201, 0),
        (0, 0, 0),
        (0, 0, 0),
        (320, 369, 0),
        (368, 345, 0),
        (416, 321, 0),
        (464, 297, 0),
        (512, 273, 0),
        (560, 249, 0),
        (608, 225, 0),
        (0, 0, 0),
        (0, 0, 0),
        (0, 0, 0),
        (416, 369, 0),
        (464, 345, 0),
        (512, 321, 0),
        (560, 297, 0),
        (0, 0, 0),
        (0, 0, 0),
        (0, 0, 0),
    )

    @classmethod
    def api_有效(cls, arg_列: int, arg_行: int) -> bool:
        return 0 <= arg_列 < 9 and 0 <= arg_行 < 9 and cls.格表[arg_行 * 9 + arg_列][0] != 0

    def __init__(self, arg_种: int) -> None:
        super().__init__(arg_种)
        self.格子 = [[企鹅格_类(*self.格表[y * 9 + x]) for x in range(9)] for y in range(9)]
        self.今x, self.今y = 0x20000, 0x60000
        self.后x = self.后y = self.目标x = self.目标y = self.步x = self.步y = 0
        self.滑 = False
        self.动画 = self.状态 = self.终 = self.宝 = self.宝x = self.宝y = 0
        self.发现, self.洞, self.分数显示 = [0] * 6, [], False
        空 = 64
        for 类, 数 in enumerate((3, 12, 3, 9, 1), 1):
            for _ in range(数):
                选, 已 = self.随机.api_下一个() * 空 >> 15, 0
                成 = False
                for 行 in self.格子:
                    for 格 in 行:
                        if not 格.x or 格.标志 & 15:
                            continue
                        if 已 == 选:
                            格.标志 = (格.标志 & 0xF0) | 类
                            空, 成 = 空 - 1, True
                            break
                        已 += 1
                    if 成:
                        break
        self.剩余帧, self.倒数 = 150, 10
        for 行 in self.格子:
            for 格 in 行:
                if 格.标志 & 15:
                    self._画(80, (格.标志 & 15) + 3, 格.x, 格.y)

    def api_开始(self) -> None:
        if self.阶段 == 小游戏阶段_类.准备:
            self.场景.clear()
        super().api_开始()

    def api_得分(self) -> int:
        return self.发现[5] * 20 + self.发现[3] * 12 + self.发现[4] * 8 + self.发现[2] * 5

    @property
    def 位置(self) -> tuple[int, int]:
        return self.今x >> 16, self.今y >> 16

    @property
    def 空闲(self) -> bool:
        return self.状态 == self.终 == 0 and self.阶段 == 小游戏阶段_类.游玩

    def api_任意点击(self) -> None:
        if self.终 == 2:
            self.剩余帧 = 1

    def api_点击(self, arg_列: int, arg_行: int) -> bool:
        if self.终 == 2:
            self.剩余帧 = 1
            return False
        if not self.空闲 or not self._瞄准(arg_列, arg_行):
            return False
        self._步进()
        self.状态 = 2
        self._声(11, 1)
        return True

    def _瞄准(self, arg_列: int, arg_行: int) -> bool:
        if not self.api_有效(arg_列, arg_行) or (arg_列, arg_行) == self.位置:
            return False
        self.今x, self.今y = (self.今x & 0xFFFF0000) + 0x8000, (self.今y & 0xFFFF0000) + 0x8000
        self.目标x, self.目标y = arg_列 << 16, arg_行 << 16
        dx, dy = arg_列 - (self.今x >> 16), arg_行 - (self.今y >> 16)
        大 = max(abs(dx), abs(dy))
        self.步x, self.步y = 事件_类._除(dx << 16, 大), 事件_类._除(dy << 16, 大)
        return True

    def _步进(self) -> None:
        nx, ny = (self.今x + self.步x) & 0xFFFFFFFF, (self.今y + self.步y) & 0xFFFFFFFF
        if self.api_有效(nx >> 16, ny >> 16):
            self.后x, self.后y = nx, ny
            return
        if abs(self.步x) == 0x10000:
            self.后x = nx
            if self.后y >> 16 == 股市_类._回绕(ny) >> 16:
                if not self.步y:
                    self.步y = 1
                self.后y = (self.后y + ((1 if self.步y > 0 else -1) << 16)) & 0xFFFFFFFF
        else:
            self.后y = ny
            if self.后x >> 16 == 股市_类._回绕(nx) >> 16:
                if not self.步x:
                    self.步x = 1
                self.后x = (self.后x + ((1 if self.步x > 0 else -1) << 16)) & 0xFFFFFFFF
        self.滑 = True

    def api_帧(self) -> None:
        if self.阶段 == 小游戏阶段_类.完成:
            return
        if self.终 == 2:
            self.剩余帧 -= 1
            if self.剩余帧 == 0:
                self.阶段 = 小游戏阶段_类.完成
            return
        if self.倒数:
            self.倒数 -= 1
            if not self.倒数:
                self.阶段 = 小游戏阶段_类.准备
            return
        if self.阶段 != 小游戏阶段_类.游玩:
            return
        if self.剩余帧 > 0:
            self.剩余帧 -= 1
            if not self.剩余帧:
                self._声(11, 2)
                self.动画 &= 0xF00
                分 = self.api_得分()
                self.状态 = 5 if 分 < 40 else 4 if 分 > 55 else 6
                if self.状态 in (4, 5):
                    self._声(13 if self.状态 == 4 else 14, 1)
        self._动画帧()
        if self.终 == 1:
            self.终, self.剩余帧, self.分数显示 = 2, 20, True
            self.阶段 = 小游戏阶段_类.结算

    def _动画帧(self) -> None:
        self.场景.clear()
        列, 行 = self.位置
        格 = 事件_类._取(事件_类._取(self.格子, 行), 列)
        x, y, 子 = 格.x, 格.y, self.动画 & 3
        if self.状态 == 0:
            self._画(80, 1, x, y)
        elif self.状态 == 1:
            self._画(80, 1 if self.动画 & 15 < 3 else 2, x, y)
            self.动画 += 1
            if self.动画 & 15 == 15:
                self.终 = 1
        elif self.状态 == 2:
            后列, 后行 = self.后x >> 16, self.后y >> 16
            if 子 == 0:
                dx, dy = 后列 - 列, 后行 - 行
                向 = 4 - (dy + 1) if dx > 0 else (1 if dy > 0 else 5) if dx == 0 else (dy + 7) & 7
                self.动画 = (self.动画 & 0xF0F) | (向 << 4)
            else:
                向 = self.动画 >> 4 & 15
            后 = 事件_类._取(事件_类._取(self.格子, 后行), 后列)
            x += ((后.x - 格.x) >> 2) * 子
            y += ((后.y - 格.y) >> 2) * 子
            self._画(82, 向 * 4 + 子, x, y)
            self.动画 = (self.动画 + 1) & 0xFF3
            if not self.动画 & 3:
                self.今x, self.今y = self.后x, self.后y
                if self.位置 == (self.目标x >> 16, self.目标y >> 16):
                    self._声(11, 2)
                    self._声(12)
                    self.状态 = 3
                else:
                    if self.滑:
                        self._瞄准(self.目标x >> 16, self.目标y >> 16)
                        self.滑 = False
                    self._步进()
        elif self.状态 == 3:
            if 子 == 2:
                self.洞.append((x, y))
                self._画(80, 9, x, y)
            if 子 == 3:
                self.宝 = 格.标志 & 15
                if self.宝:
                    self.动画 = (self.动画 & 255) | 0x100
                    self.宝x, self.宝y = 格.x, 格.y
                    格.标志 &= 0xF0
            self._画(83, (self.动画 >> 4 & 15) * 4 + 子, x, y)
            self.动画 = (self.动画 + 1) & 0xFF3
            if not self.动画 & 3:
                self.状态 = 1 if self.宝 == 1 else 0
                if self.宝 == 1:
                    self._声(15)
                elif self.宝:
                    self._声((0, 0, 16, 17, 17, 18)[self.宝])
                    self.发现[self.宝] += 1
        elif self.状态 in (4, 5):
            欢 = self.状态 == 4
            self._画(84 if 欢 else 85, self.动画 & 15, x, y)
            self.动画 += 1
            if self.动画 & 15 == (8 if 欢 else 6):
                self.动画 = (self.动画 & 0xF0) + 0x10
            if self.动画 & 0xF0 == 0x40:
                self._声(13 if 欢 else 14, 2)
                self.终 = 1
        elif self.状态 == 6:
            self._画(80, 1, x, y)
            self.动画 += 1
            if self.动画 & 15 == 15:
                self.终 = 1
        if self.动画 >> 8 & 15 and self.宝 > 0:
            self._画(85 + self.宝, (self.动画 >> 8 & 15) - 1, self.宝x, self.宝y)
            self.动画 += 0x100
            if self.动画 & 0xF00 == 0x700:
                self.动画 &= 255
        if 格.标志 & 0xF0:
            self._画(80, 3, 320, 225)
        if (self.状态 in (1, 6) and self.动画 & 15 == 4) or self.状态 in (4, 5):
            self.分数显示 = True


@dataclass
class 气球槽_类:
    """
    原气球坐标及低四位种类/高四位爆裂倒数。

    更新日志：
    2026.10.23 - 对应Balloon::Slot。
    """

    x: int = 0
    y: int = 0
    种类: int = 0


class 气球_类(小游戏_类):
    """
    原十六槽气球生成、包围框点击、问号特殊效果与结束清场。

    更新日志：
    2026.10.23 - 对应Balloon，定时器100ms。
    """

    速度 = (15, 15, 15, 15, 18, 18, 18, 24, 24, 24, 24, 18)
    特殊 = (9, 9, 10, 10, 10, 10, 10, 11, 11, 11)

    def __init__(self, arg_种: int) -> None:
        super().__init__(arg_种)
        self.剩余帧, self.倒数 = 150, 5
        self.槽 = [气球槽_类() for _ in range(16)]
        self.分 = self.终 = self.冻结 = self.变速 = 0

    def api_得分(self) -> int:
        return self.分

    @staticmethod
    def _框(arg_帧: int) -> 图框_类:
        return (
            图框_类(60, 122, 28, 40)
            if arg_帧 == 13
            else 图框_类(44, 141, 22, 30)
            if arg_帧 <= 6
            else 图框_类(36, 116, 18, 26)
        )

    def api_帧(self) -> None:
        if self.阶段 == 小游戏阶段_类.完成:
            return
        if self.阶段 == 小游戏阶段_类.结算:
            self.停留 -= 1
            if not self.停留:
                self.阶段 = 小游戏阶段_类.完成
            return
        if self.倒数:
            self.倒数 -= 1
            if not self.倒数:
                self.阶段 = 小游戏阶段_类.准备
            return
        if self.阶段 != 小游戏阶段_类.游玩:
            return
        if self.冻结:
            self.冻结 -= 1
        if self.剩余帧:
            self.剩余帧 -= 1
            if not self.剩余帧:
                self.终 = 1
        self._步进()
        if self.终 == 2:
            self.阶段, self.停留 = 小游戏阶段_类.结算, 20

    def _步进(self) -> None:
        self.场景.clear()
        有 = False
        for i, 槽 in enumerate(self.槽):
            if not 槽.x:
                if self.终:
                    continue
                r = self.随机.api_下一个() % 1000
                类 = (
                    r >> 2
                    if r < 20
                    else ((27 - r) >> 1) + 5
                    if r < 28
                    else self.特殊[self.随机.api_下一个() % 10]
                    if r < 30
                    else -1
                )
                if 类 < 0:
                    continue
                空 = [
                    巷
                    for 巷 in range(40, 640, 80)
                    if not any(另.x == 巷 and 另.y > 300 for 另 in self.槽)
                ]
                if not 空:
                    continue
                self._声(19)
                槽.x, 槽.y, 槽.种类 = 空[self.随机.api_下一个() % len(空)], 420, 类
                continue
            if 槽.种类 & 0xF0:
                槽.种类 = (槽.种类 - 0x10) & 65535
                if not 槽.种类 & 0xF0:
                    self.槽[i] = 气球槽_类()
                    continue
            elif not self.冻结:
                速 = self.速度[槽.种类 & 15]
                速 = 速 * 2 if self.变速 == -1 else 速 >> 1 if self.变速 == 1 else 速
                槽.y = self._短(槽.y - 速)
            帧 = (槽.种类 & 15) + 1
            框 = self._框(帧)
            左, 上 = 槽.x - 框.原x, 槽.y - 框.原y
            if 左 >= 640 or 左 + 框.宽 <= 0 or 上 >= 387 or 上 + 框.高 <= 0:
                self.槽[i] = 气球槽_类()
                continue
            self._画(91, 帧, 槽.x, 槽.y)
            有 = True
        if not 有 and self.终 == 1:
            self.终 = 2

    def api_点击(self, arg_x: int, arg_y: int) -> int:
        if self.阶段 != 小游戏阶段_类.游玩 or self.终 == 2 or self.倒数:
            return 0
        弹 = 0
        for 槽 in self.槽:
            if not 槽.x or 槽.种类 & 0xF0:
                continue
            宽, 高 = (18, 26) if 槽.种类 >= 6 else (22, 30)
            if not 槽.x - 宽 <= arg_x <= 槽.x + 宽 or not 槽.y - 高 <= arg_y <= 槽.y + 高:
                self._声(20)
                continue
            self._声(21)
            弹 += 1
            if 槽.种类 == 9:
                self.分 = 股市_类._回绕(self.分 + self.分)
            elif 槽.种类 == 10:
                self.分 >>= 1
            elif 槽.种类 == 11:
                self.冻结 = self.变速 = 0
                效 = self.随机.api_下一个() % 6
                if 效 == 0:
                    self.剩余帧 = 1
                elif 效 == 1:
                    self.冻结 = 20
                elif 效 in (2, 3):
                    self.变速 = -1 if 效 == 2 else 1
                elif 效 == 4:
                    self.分 = 0
                else:
                    self.分 = 股市_类._回绕(self.分 + self.分)
            else:
                self.分 = 股市_类._回绕(self.分 + 槽.种类 + 1)
                if self.分 >= 1000:
                    self.分 = 999
            槽.种类 = 0x3C
        return 弹


@dataclass
class 天降槽_类:
    """
    原抛物槽，低位种类/动画帧，高字节有符号横向漂移。

    更新日志：
    2026.10.23 - 对应Catcher::Slot。
    """

    x: int = 0
    y: int = 0
    位: int = 0
    vy: int = 0


class 天降_类(小游戏_类):
    """
    财神与鬼怪原状态机、精灵框接取及扩展精度漂移/缩放。

    更新日志：
    2026.10.23 - 对应Catcher，定时器50ms。
    """

    下落速度 = (24, 18, 15, 12, 15)
    财神帧 = (
        0,
        1,
        2,
        3,
        5,
        6,
        0,
        1,
        2,
        4,
        5,
        6,
        7,
        8,
        9,
        10,
        11,
        0,
        11,
        10,
        9,
        8,
        7,
        0,
        12,
        13,
        14,
        15,
        17,
        18,
        12,
        13,
        14,
        16,
        17,
        18,
    )

    def __init__(
        self, arg_种: int, arg_角色: int, arg_框: list[图框_类], arg_爆炸帧: int = 19
    ) -> None:
        super().__init__(arg_种)
        if len(arg_框) < 5:
            raise ValueError("catcher sprite needs at least 5 frames")
        self.条目, self.框, self.爆炸帧 = (
            100 + (arg_角色 & 255) % 12,
            list(arg_框),
            max(1, arg_爆炸帧),
        )
        self.每向帧 = (len(self.框) - 5) >> 1
        self.槽, self.接到 = [天降槽_类() for _ in range(16)], [0] * 5
        self.终, self.爆炸, self.爆x, self.爆龄 = 0, False, 0, 0
        self.鬼帧, self.鬼x = -1, 0
        self.财神态, self.财神步, self.财神x, self.投步 = 3, 4, 110, 0
        self.接者x, self.方向, self.步行, self.姿态, self.炸弹数, self.目标 = 320, 0, 0, 0, 0, 320
        self.剩余帧, self.倒数 = 360, 10
        self._步进()

    @staticmethod
    def api_漂移(arg_x: int) -> int:
        t = 扩展数_类.api_从值(股市_类._浮点(股市_类._位(arg_x - 320)))
        return ((t / 扩展数_类.api_从值(210) * 扩展数_类.api_从值(260)) - t).api_整数()

    def api_得分(self) -> int:
        return self.接到[1] * 5 + self.接到[0] * 10 + self.接到[2] * 3 + self.接到[3]

    def api_目标(self, arg_x: int) -> None:
        self.目标 = arg_x

    def _接者帧(self) -> int:
        return (self.方向 - 1) * self.每向帧 + 5 + self.步行 if self.方向 else self.姿态

    def _生成(self, arg_x: int, arg_炸: bool) -> None:
        空 = next((槽 for 槽 in self.槽 if not 槽.x), None)
        if 空 is None:
            return
        类 = 4
        if not arg_炸:
            r = self.随机.api_下一个() % 20
            类 = 3 if r < 9 else 2 if r < 15 else 1 if r < 18 else 0
        else:
            self.炸弹数 += 1
        空.x, 空.y, 空.位, 空.vy = (
            self._短(arg_x),
            100,
            (类 + (self.api_漂移(arg_x) << 8)) & 65535,
            -16,
        )

    def api_帧(self) -> None:
        if self.阶段 == 小游戏阶段_类.完成:
            return
        if self.阶段 == 小游戏阶段_类.结算:
            self.停留 -= 1
            if not self.停留:
                self.阶段 = 小游戏阶段_类.完成
            return
        if self.倒数:
            self.倒数 -= 1
            if not self.倒数:
                self.阶段 = 小游戏阶段_类.准备
            return
        if self.阶段 != 小游戏阶段_类.游玩:
            return
        if self.剩余帧:
            self.剩余帧 -= 1
            if not self.剩余帧:
                self.终 = 1
        self._步进()
        if self.终 == 2:
            if self.姿态 != 4:
                self.方向 = 0
                分 = self.api_得分()
                self.姿态 = 1 if 分 < 40 else 2 if 分 < 50 else 0 if 分 < 60 else 3
            self._步进()
            self.阶段, self.停留 = 小游戏阶段_类.结算, 40
        if self.爆炸:
            self.爆龄 += 1
            if self.爆龄 >= self.爆炸帧:
                self.爆炸, self.终 = False, 2

    def _步进(self) -> None:
        self.场景.clear()
        有, E = False, 扩展数_类.api_从值
        for i, 槽 in enumerate(self.槽):
            if not 槽.x:
                continue
            上距 = 槽.y - 130 if 槽.y >= 130 else 0
            比 = (E(上距) / E(250)).api_单精度()
            vx = self._短(槽.位) >> 8
            dx = (E(vx) * E(比)).api_整数()
            缩 = (E(比) * E(32768) + E(32768)).api_整数() & 0xFFFFFFFF
            x, 类 = 槽.x + dx, 槽.位 & 15
            if self.方向:
                框 = 事件_类._取(self.框, self._接者帧())
                左, 上 = self.接者x - 框.原x, 380 - 框.原y
                if 左 < x < 左 + 框.宽 and 上 < 槽.y < 上 + 框.高 and not self.爆炸:
                    if 类 == 4:
                        self._声(24, 2)
                        self._声(15)
                        self.爆炸, self.爆x, self.爆龄 = True, self.接者x - 55, 0
                        self.方向, self.姿态, self.终 = 0, 4, 1
                    else:
                        self.接到[类] += 1
                    self.槽[i] = 天降槽_类()
                    槽 = self.槽[i]
            if 槽.x:
                self._画(95 + 类, (槽.位 & 0xF0) >> 4, x, 槽.y, 缩)
                槽.位 = (槽.位 & 0xFF00) | ((槽.位 + 0x10) & 0x7F)
                if 槽.y < 130:
                    槽.vy = self._短(min(16, 槽.vy + 2))
                    槽.y = self._短(槽.y + 槽.vy)
                else:
                    槽.y = self._短(槽.y + self.下落速度[类])
                if 槽.y > 380:
                    if 类 == 4:
                        self.炸弹数 -= 1
                        if self.炸弹数 == 0:
                            self._声(24, 2)
                    self.槽[i] = 天降槽_类()
                    槽 = self.槽[i]
            if 槽.x:
                有 = True
        if self.鬼帧 != -1:
            self._画(94, self.鬼帧, self.鬼x, 125)
        self._画(93, 事件_类._取(self.财神帧, self.财神态 * 6 + self.财神步), self.财神x, 126)
        if self.终 != 2 and not self.爆炸:
            距 = self.接者x - self.目标
            if abs(距) > 8:
                self.方向 = 1 if 距 > 0 else 2
                self.接者x += -10 if 距 > 0 else 10
                self.步行 += 1
                if self.步行 == self.每向帧:
                    self.步行 = 0
        self._画(self.条目, self._接者帧(), self.接者x, 380)
        if self.鬼帧 == -1:
            if (self.财神态 < 2 and self.财神x > 320) or (self.财神态 > 3 and self.财神x < 320):
                if self.随机.api_下一个() % 10 >= 7 and self.终 == 0:
                    r = self.随机.api_下一个() % 140
                    self.鬼帧, self.鬼x = 0, r + (160 if self.财神x > 320 else 360)
        else:
            self.鬼帧 += 1
            if self.鬼帧 == 8 and not self.爆炸:
                self._声(22)
                self._声(24, 1)
                self._生成(self.鬼x, True)
            if self.鬼帧 == 12:
                self.鬼帧 = -1
        if self.终 == 1:
            self.财神态, self.财神步 = 2, 2
        elif self.财神态 in (0, 4):
            右 = self.财神态 == 0
            if self.财神步 < 5:
                if self.财神步 == self.投步:
                    self._生成(self.财神x, False)
                self.财神步 += 1
                self.财神x += 12 if 右 else -12
            else:
                转 = False
                if self.财神x > 320 if 右 else self.财神x < 320:
                    转 = self.随机.api_下一个() % 4 == 0
                if not 转:
                    转 = self.财神x == (530 if 右 else 110)
                if 转:
                    self.财神态 = 2 if 右 else 3
                else:
                    self.投步 = self.随机.api_下一个() % 5
                    self.财神x += 12 if 右 else -12
                self.财神步 = 0
        elif self.财神态 in (2, 3):
            self.财神步 += 1
            if self.财神步 == 5:
                self.财神态 = 4 if self.财神态 == 2 else 0
                self.财神步 = 0
        if not 有 and self.终 == 1:
            self.终 = 2
