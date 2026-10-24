# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/monthly.cpp::MonthlyScreens；原gallery只作研究夹具，不作正式游戏。
# ◑ 导入
from collections import deque
from copy import deepcopy

from rich4.game_types import 效果_类, 效果种类_类
from rich4.monthly_common import 月报共用_类, 月报声音_类
from rich4.monthly_lottery import 月报开奖_类
from rich4.monthly_report import 月报结算_类
from rich4.monthly_types import 月播_类
from rich4.native_frame import 画框_类
from rich4.original_text import 原版文字_类
from rich4.world import 世界_类


# ◕ 功能
class 月报屏幕_类(月报开奖_类, 月报结算_类, 月报共用_类):
    """
    原股利、开奖、月末报告的顺序队列与模态播放，不重复结算原MonthlyFigures。

    更新日志：
    2026.10.24 - 真实语音最短等待、点击语义及开发逐屏单帧策略保持独立。
    """

    def __init__(self, arg_声音: 月报声音_类, arg_原文: 原版文字_类) -> None:
        self.声音, self.原文 = arg_声音, arg_原文
        self._跳过 = False
        self._队列: deque[效果_类] = deque()
        self._当前: 月播_类 | None = None

    @staticmethod
    def api_处理(arg_效: 效果_类) -> bool:
        return (
            arg_效.种类 in (效果种类_类.股利, 效果种类_类.彩票开奖, 效果种类_类.月报)
            and arg_效.月报 is not None
        )

    def api_跳过(self, arg_跳过: bool) -> None:
        self._跳过 = arg_跳过

    def api_活跃(self) -> bool:
        return self._当前 is not None or bool(self._队列)

    def api_画面名(self) -> str:
        if self._当前 is None:
            return ""
        k = self._当前.效果.种类
        return (
            "dividend"
            if k == 效果种类_类.股利
            else "lottery"
            if k == 效果种类_类.彩票开奖
            else "report"
        )

    def api_入队(self, arg_效: 效果_类) -> None:
        if self.api_处理(arg_效):
            self._队列.append(deepcopy(arg_效))

    def api_清空(self) -> None:
        self._队列.clear()
        self._当前 = None

    def _开始(self, arg_播: 月播_类) -> None:
        p = arg_播
        if p.效果.月报 is None:
            raise ValueError("原月结效果缺少数据")
        p.数据 = deepcopy(p.效果.月报)
        p.种子 = (0x2545F491 ^ p.数据.号码 ^ (int(p.效果.种类) << 8)) & 0xFFFFFFFF
        if p.效果.种类 == 效果种类_类.股利:
            p.节拍 = 1000
            if self.声音.播放:
                self.声音.播放(61)
        elif p.效果.种类 == 效果种类_类.彩票开奖:
            p.节拍, p.布局, p.状态 = 50, 0, 1
            self._说(p, 22, 300, 47, -10, 0, 17)
        else:
            p.节拍, p.状态 = 100, 1
            self._说(p, 1, 190, 10, 0, -30, 92)

    def api_绘制(self, arg_框: 画框_类, arg_世: 世界_类, arg_毫秒: int) -> None:
        if self._当前 is None:
            if not self._队列:
                return
            self._当前 = 月播_类(self._队列.popleft())
            self._开始(self._当前)
        p = self._当前
        if self._跳过 and p.画过:
            self._当前 = None
            return
        dt = arg_毫秒 & 0xFFFFFFFF
        if p.效果.种类 == 效果种类_类.股利:
            开 = self._画股利(arg_框, arg_世, p, dt)
        elif p.效果.种类 == 效果种类_类.彩票开奖:
            开 = self._画开奖(arg_框, p, dt)
        else:
            开 = self._画月报(arg_框, p, dt)
        p.画过, p.点过 = True, False
        arg_框.按钮.clear()

        def 继续() -> None:
            if self._当前 is not None:
                self._当前.点过 = True

        arg_框.api_命中(911, (0, 0, 640, 480), 继续)
        if not 开:
            self._当前 = None
