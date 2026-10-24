# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定market.cpp::draw_lottery/neon_frames；真实选号由核心结算。
# ◑ 导入
import logging
from collections.abc import Callable
from dataclasses import dataclass

from rich4.artwork import 美术_类
from rich4.game_types import 决策_类
from rich4.graphics import 图像_类
from rich4.original_text import 原版文字_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类
from rich4.world import 世界_类


# ◕ 功能
@dataclass
class 彩票告别_类:
    """
    原LotteryFarewell；选项0是有效等待，None才表示不在告别。

    更新日志：
    2026.10.24 - 保留号格、起始时钟与真实语音长度。
    """

    选项: int | None = None
    号码: int = -1
    开始: int = 0
    语音毫秒: int = 0

    def api_清空(self) -> None:
        self.选项, self.号码, self.开始, self.语音毫秒 = None, -1, 0, 0


class 彩票柜台_类:
    """
    原Panel12柜台/36号格、Panel14霓虹和最短两秒告别。

    更新日志：
    2026.10.24 - 长对白外部读取；坏霓虹依原记录后不重试，规则不受装饰影响。
    """

    def __init__(self, arg_原文: 原版文字_类) -> None:
        self._原文 = arg_原文
        self._霓虹: dict[美术_类, list[图像_类]] = {}

    def _霓虹帧(self, arg_美术: 美术_类) -> list[图像_类]:
        if arg_美术 not in self._霓虹:
            frames = []
            try:
                movie = arg_美术.api_动画("p", 14)
                while len(frames) < movie.帧数 and movie.api_下一帧():
                    frames.append(movie.api_图像())
            except (ValueError, IndexError, OSError) as error:
                logging.getLogger(__name__).warning("彩票霓虹按原跳过：%s", error)
            self._霓虹[arg_美术] = frames or [图像_类(0, 0, [])]
        return self._霓虹[arg_美术]

    def api_绘制(
        self,
        arg_宿: 屏幕宿主_类,
        arg_世: 世界_类,
        arg_决: 决策_类,
        arg_答: Callable[[int], None],
        arg_告别: 彩票告别_类 | None = None,
        arg_再见: Callable[[bool], int] | None = None,
    ) -> None:
        框, 绘 = arg_宿.框, 屏幕绘图_类
        if arg_告别 is not None and arg_告别.选项 is not None and arg_告别.选项 >= len(arg_决.选项):
            arg_告别.api_清空()
        leaving = arg_告别 is not None and arg_告别.选项 is not None
        绘.api_背景(框, "p", 12, 0)
        neon = self._霓虹帧(框.美术)
        if neon[0].像素:
            框.画布.api_绘制(neon[框.时钟 // 100 % len(neon)], 8, 8)
        if leaving:
            框.api_资源图("p", 12, 2, 154, -8)
        else:
            框.api_资源图("p", 12, 1, 210, -5)
        if not leaving and 框.时钟 // 100 % 35 < 3:
            框.api_资源图("p", 12, (3, 4, 3)[框.时钟 // 100 % 35], 273, 63)
        框.api_资源图("p", 12, 9, 28, 27)
        pool, right = "$" + 绘.api_货币(arg_世.公共基金), 184
        for c in reversed(pool):
            width = 12 if c == "," else 18
            glyph = 10 if c == "," else 11 if c == "$" else ord(c) - 48
            框.画布.api_绘制(框.美术.api_帧("p", 13, glyph), right - width // 2, 41)
            right -= width
        can_buy = any(o.值 > 0 for o in arg_决.选项)
        if leaving:
            voice = 14 if arg_告别.号码 >= 0 else 16
            line = self._原文.api_配音(voice).文字
            if voice == 14:
                line = line.replace("！", "！\n", 1)
        else:
            line = self._原文.api_配音(13 if can_buy else 15).文字
        框.api_资源图("p", 12, 8, 360, 20)
        绘.api_文字(框, line, 498, 116, 4, 屏幕字样_类(20, 0x101010, 0, 2))
        if 框.时钟 // 150 % 2:
            框.api_资源图("p", 12, 5, 273, 105)
        slot = arg_决.玩家
        for n, owner in enumerate(arg_世.彩票):
            column, row = n % 9, n // 9
            x, y = 30 + 64 * column, 271 + 48 * row
            if owner:
                绘.api_暗化(
                    框.画布,
                    (31 + 64 * column, 272 + 48 * row, 93 + 64 * column, 318 + 48 * row),
                    -10,
                )
            if owner == slot + 1 or (leaving and arg_告别.号码 == n):
                框.画布.api_绘制(框.美术.api_帧("p", 12, 7), x + 32, y + 24)
        if leaving:

            def 完成() -> None:
                index = arg_告别.选项
                arg_告别.api_清空()
                arg_答(index)

            until = (arg_告别.开始 + max(2000, arg_告别.语音毫秒)) & 0xFFFFFFFFFFFFFFFF
            if 框.时钟 >= until:
                完成()
                return
            绘.api_命中(arg_宿, 210 + arg_告别.选项, (0, 0, 640, 480), 1, 完成)
            return
        instant = arg_宿.即时

        def 选择(arg_i: int, arg_号: int) -> None:
            if arg_告别 is None or instant:
                arg_答(arg_i)
                return
            arg_告别.选项, arg_告别.号码, arg_告别.开始 = arg_i, arg_号, 框.时钟
            arg_告别.语音毫秒 = (arg_再见(arg_号 >= 0) if arg_再见 else 0) & 0xFFFFFFFF

        if 框.api_指针内((30, 271, 606, 463)):
            n = (框.指针y - 271) // 48 * 9 + (框.指针x - 30) // 64
            if 0 <= n < 36 and not arg_世.彩票[n] and can_buy:
                框.画布.api_绘制(框.美术.api_帧("p", 12, 7), 62 + 64 * (n % 9), 295 + 48 * (n // 9))
        leave = None
        for index, option in enumerate(arg_决.选项):
            if option.值 <= 0 or option.值 > 36:
                leave = index
                continue
            n = option.值 - 1
            rect = (30 + 64 * (n % 9), 271 + 48 * (n // 9), 94 + 64 * (n % 9), 319 + 48 * (n // 9))
            绘.api_命中(arg_宿, 210 + index, rect, 1, lambda index=index, n=n: 选择(index, n))
        if leave is not None:

            def 离开() -> None:
                if can_buy:
                    选择(leave, -1)
                else:
                    arg_答(leave)

            绘.api_命中(arg_宿, 210 + leave, (0, 0, 640, 480), 4, 离开)
