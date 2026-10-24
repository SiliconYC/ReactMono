# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/spinners.cpp；只重放已结算效果，真实交互数位由核心推进。
# ◑ 导入
from collections import deque
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field

from rich4.game_types import 决策_类, 决策种类_类, 效果_类, 效果种类_类, 转盘状态_类
from rich4.gods import 金钱转盘_类
from rich4.message_overlay import 消息层_类
from rich4.message_rules import 消息规则_类
from rich4.native_frame import 按钮_类, 画框_类
from rich4.original_text import 原版文字_类
from rich4.random import 随机数_类
from rich4.world import 世界_类


# ◕ 功能
@dataclass
class 转盘声音_类:
    """
    原一次音、替换循环及停止循环接口，收帧后只保留当前可见转动声音。

    更新日志：
    2026.10.24 - 与真实音频宿主分开，空声道依原不阻断绘制。
    """

    播放: Callable[[int], None] | None = None
    循环: Callable[[int], None] | None = None
    停循环: Callable[[], None] | None = None


@dataclass
class _转播_类:
    """
    原Playing的私有重放状态与随机流，不回写核心规则。

    更新日志：
    2026.10.24 - 保留轮盘速度/计数与人类结果跳过标志。
    """

    效果: 效果_类
    状态: 转盘状态_类
    已过: int = 0
    帧数: int = 0
    轮状态: int = 1
    周期: int = 1
    计数: int = 3
    上次: int = 0
    机器: 金钱转盘_类 | None = None
    随机: 随机数_类 = field(default_factory=lambda: 随机数_类(0))
    跳过: bool = False


class 转盘屏幕_类:
    """
    原金额机与爱神轮盘画面、30/36ms重放、停止按钮及循环音效状态。

    更新日志：
    2026.10.24 - 真实交互读核心SpinnerState，电脑电影私有重播同一随机序列。
    """

    轮值 = (
        (1, -1, 0, -1, 1, -1, 2, -1, 3, -1, 2, -1),
        (-1, -1, 1, -1, -1, 4, -1, 3, -1, -1, 2, -1),
        (1, -1, 6, -1, 5, -1, 4, -1, 3, -1, 2, -1),
        (5, -1, 3, -1, 30, -1, 20, -1, 15, -1, 10, -1),
    )
    杆x = (317, 298)
    数位x = ((145, 182, 219, 256), (0, 163, 200, 237))
    提示地址 = {1: 0x4652AB, 2: 0x4652C3, 5: 0x4652D3, 6: 0x4652E9}

    def __init__(self, arg_声音: 转盘声音_类, arg_原文: 原版文字_类) -> None:
        self.声音, self.原文 = arg_声音, arg_原文
        self._队列: deque[效果_类] = deque()
        self._当前: _转播_类 | None = None
        self._跳过 = False
        self._待循环 = self._正在循环 = self._决策阶段 = 0
        self._消息规则 = 消息规则_类(arg_原文)

    def api_跳过(self, arg_跳过: bool) -> None:
        self._跳过 = arg_跳过

    def api_活跃(self) -> bool:
        return self._当前 is not None or bool(self._队列)

    @staticmethod
    def api_处理决策(arg_决: 决策_类) -> bool:
        return arg_决.转盘 is not None and arg_决.种类 in (决策种类_类.金额转盘, 决策种类_类.轮盘)

    @staticmethod
    def api_处理效果(arg_效: 效果_类) -> bool:
        return arg_效.转盘 is not None and arg_效.种类 in (效果种类_类.金额转盘, 效果种类_类.轮盘)

    @staticmethod
    def _版本(arg_状态: 转盘状态_类) -> int:
        return (((arg_状态.类型 - 1) & 0xFFFFFFFF) & 1) ^ 1

    @classmethod
    def api_金额(cls, arg_状态: 转盘状态_类) -> int:
        d = arg_状态.数位
        钱 = d[1] // 2 * 100 + d[2] // 2 * 10 + d[3] // 2
        return 钱 + d[0] // 2 * 1000 if cls._版本(arg_状态) == 0 else 钱

    def _神名(self, arg_种: int) -> str:
        if not 1 <= arg_种 <= 6:
            return ""
        p = self.原文.程序.api_指针表(0x47ED7A, 6)[arg_种 - 1]
        return self.原文.api_原文(p)

    def _轮文(self, arg_世: 世界_类, arg_状态: 转盘状态_类) -> str:
        s = arg_状态
        if s.类型 in (1, 2):
            名 = 消息规则_类.api_人名(arg_世, s.主体)
        else:
            名 = self._消息规则._公司(arg_世, s.主体)
        i = s.类型 if s.类型 in (0, 1, 2) else 3
        p = self.原文.程序.api_指针表(0x475CF8, 4)[i]
        return 消息规则_类.api_格式(self.原文.api_原文(p), [名])

    @staticmethod
    def _框(arg_框: 画框_类, arg_文: str) -> None:
        arg_框.画布.api_绘制(arg_框.美术.api_帧("d", 517, 5), 220, 140)
        消息层_类.api_文字(arg_框, arg_文, 220, 140, 4, 消息层_类.框字)

    def _画机器(self, arg_框: 画框_类, arg_状态: 转盘状态_类) -> None:
        s = arg_状态
        v = self._版本(s)
        if s.阶段 >= 9:
            文 = f"{self.api_金额(s)}元"
        else:
            文 = self._神名(s.类型) + self.原文.api_原文(
                self.提示地址.get(s.类型, self.提示地址[6])
            )
        self._框(arg_框, 文)
        画, 美 = arg_框.画布, arg_框.美术
        画.api_绘制(美.api_帧("p", 67, v), 220, 320, arg_强制不透明=True)
        画.api_绘制(美.api_帧("p", 67, 3 if s.阶段 in (2, 3) else 2), self.杆x[v], 240)
        if s.阶段 == 0:
            return
        for i in range(v, 4):
            画.api_绘制(
                美.api_帧("p", 67, 4 + s.数位[i] % 20), self.数位x[v][i], 320, arg_强制不透明=True
            )

    def _画轮(
        self, arg_框: 画框_类, arg_世: 世界_类, arg_状态: 转盘状态_类, arg_射箭: bool
    ) -> None:
        s = arg_状态
        条 = 68 + (s.类型 & 3)
        self._框(arg_框, self._轮文(arg_世, s))
        画, 美 = arg_框.画布, arg_框.美术
        轮 = 美.api_帧("p", 条, 2 + s.游标 % 12)
        if not arg_射箭:
            画.api_绘制(美.api_帧("p", 条, 0), 265, 230)
            画.api_绘制(轮, 220, 320)
        else:
            画.api_绘制(轮, 220, 320)
            画.api_绘制(美.api_帧("p", 条, 1), 265, 230)

    def api_绘决策(
        self,
        arg_框: 画框_类,
        arg_世: 世界_类,
        arg_决: 决策_类,
        arg_停止号: int,
        arg_停止: Callable[[], None],
    ) -> None:
        s = arg_决.转盘
        if s is None:
            raise ValueError("原转盘决策缺少数位状态")
        if arg_决.种类 == 决策种类_类.金额转盘:
            if self._决策阶段 <= 1 and 2 <= s.阶段 < 9 and self.声音.播放:
                self.声音.播放(1)
            self._决策阶段 = s.阶段
            self._画机器(arg_框, s)
            if s.阶段 <= 8:
                self._待循环 = 51
        else:
            self._画轮(arg_框, arg_世, s, False)
            self._待循环 = 52
        arg_框.按钮.append(按钮_类(arg_停止号, (0, 0, 640, 480), True, arg_停止, False))

    def api_入队(self, arg_效: 效果_类) -> None:
        if not self._跳过 and arg_效.转盘 is not None:
            self._队列.append(deepcopy(arg_效))

    def api_清空(self) -> None:
        self._队列.clear()
        self._当前 = None

    def _步轮(self, arg_播: _转播_类) -> bool:
        p = arg_播
        p.帧数 = (p.帧数 + 1) & 0xFFFFFFFF
        if p.轮状态 == 1 and p.帧数 >= 40:
            p.轮状态 = 2
        if p.轮状态 == 1:
            p.状态.游标 = (p.状态.游标 + 1) % 12
        elif p.轮状态 == 2:
            if self.声音.播放:
                self.声音.播放(1)
            p.轮状态, p.计数, p.周期, p.上次 = 3, 3, 1, p.帧数
        elif p.轮状态 == 3:
            if (p.帧数 - p.上次) & 0xFFFFFFFF != p.周期:
                return True
            p.状态.游标 = (p.状态.游标 + 1) % 12
            p.上次 = p.帧数
            p.计数 = (p.计数 - 1) & 0xFFFFFFFF
            if p.计数 == 0:
                p.计数, p.周期 = 3, (p.周期 + 1) & 0xFFFFFFFF
            if p.周期 >= 5 and self.轮值[p.状态.类型 & 3][p.状态.游标 % 12] >= 0:
                p.轮状态, p.帧数 = 5, 0
        elif p.轮状态 == 5:
            if p.帧数 >= 40 or p.跳过:
                return False
        else:
            return False
        return True

    def api_绘效果(self, arg_框: 画框_类, arg_世: 世界_类, arg_毫秒: int, arg_跳过号: int) -> None:
        if self._当前 is None:
            if not self._队列:
                return
            e = self._队列.popleft()
            p = _转播_类(e, deepcopy(e.转盘))
            if e.种类 == 效果种类_类.金额转盘:
                p.机器 = 金钱转盘_类(p.状态.类型)
                p.随机.状态 = p.状态.种子 & 0xFFFFFFFF
                p.状态.阶段 = 0
            else:
                p.轮状态 = 2 if p.状态.阶段 == 2 else 1
            self._当前 = p
        p = self._当前
        p.已过 = (p.已过 + min(arg_毫秒 & 0xFFFFFFFF, 100)) & 0xFFFFFFFF
        运行 = True
        if p.机器 is not None:
            while 运行 and p.已过 >= 30:
                p.已过 -= 30
                前 = p.机器.阶段
                p.机器.api_步进(p.随机, True)
                if 前 == 1 and p.机器.阶段 >= 2 and self.声音.播放:
                    self.声音.播放(1)
                运行 = not p.机器.完成
            p.状态.数位 = list(p.机器.数字)
            p.状态.阶段 = p.机器.阶段 & 255
        else:
            while 运行 and p.已过 >= 36:
                p.已过 -= 36
                运行 = self._步轮(p)
        if not 运行:
            self._当前 = None
            return
        arg_框.按钮.clear()
        if p.机器 is not None:
            self._画机器(arg_框, p.状态)
            if p.状态.阶段 <= 8:
                self._待循环 = 51
        else:
            self._画轮(arg_框, arg_世, p.状态, p.轮状态 >= 3)
            if p.轮状态 < 5:
                self._待循环 = 52
            elif p.效果.转盘.阶段 == 2:

                def 跳过() -> None:
                    if self._当前 is not None:
                        self._当前.跳过 = True

                arg_框.按钮.append(按钮_类(arg_跳过号, (0, 0, 640, 480), True, 跳过, False))

    def api_收帧(self) -> None:
        if self._待循环 != self._正在循环:
            if self._待循环 and self.声音.循环:
                self.声音.循环(self._待循环)
            elif not self._待循环 and self.声音.停循环:
                self.声音.停循环()
            self._正在循环 = self._待循环
        self._待循环 = 0
