# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/menus.cpp/.hpp::SaveLoadScreen；不假装已经完成会话运行恢复。
# ◑ 导入
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field

from rich4.screen_draw import 屏幕宿主_类, 屏幕绘图_类


# ◕ 功能
@dataclass
class 存档槽_类:
    """
    原SaveSlot的日期/地图/人物摘要，文件有效性由真实存档管理器提供。

    更新日志：
    2026.10.24 - 日期按日/月/年保存，不将槽摘要当成运行存档。
    """

    有效: bool = False
    日期: tuple[int, int, int] = (0, 0, 0)
    地图: int = 0
    阶段: int = 0
    人物: list[int] = field(default_factory=list)


class 存档槽屏幕_类:
    """
    原Data520六读取/五保存槽、悬选描框与外部取消。

    更新日志：
    2026.10.24 - 空档只禁读取，保存跳过AUTO，窗口体吞点击。
    """

    def __init__(self) -> None:
        self._保存 = False
        self._自动 = False
        self._档 = [存档槽_类() for _ in range(6)]
        self._悬选 = -1

    def api_打开(self, arg_保存: bool, arg_槽: list[存档槽_类]) -> None:
        if len(arg_槽) != 6:
            raise ValueError("原存档屏幕要求六个槽位")
        self._保存, self._自动, self._档, self._悬选 = arg_保存, False, deepcopy(arg_槽), -1

    def api_打开自动(self, arg_槽: list[存档槽_类]) -> None:
        if len(arg_槽) != 6:
            raise ValueError("自动读取仍使用六槽画面")
        self._保存, self._自动, self._档, self._悬选 = False, True, deepcopy(arg_槽), -1

    def api_自动中(self) -> bool:
        return self._自动

    def api_保存中(self) -> bool:
        return self._保存

    def api_槽(self) -> tuple[存档槽_类, ...]:
        return tuple(deepcopy(self._档))

    def _行顶(self, arg_槽: int) -> int:
        return 57 + 72 * (arg_槽 - 1) if self._保存 else 24 + 72 * arg_槽

    def api_绘制(
        self,
        arg_宿: 屏幕宿主_类,
        arg_选: Callable[[int], None],
        arg_关: Callable[[], None],
        arg_切换: Callable[[], None] | None = None,
    ) -> None:
        框, 绘 = arg_宿.框, 屏幕绘图_类
        window = (40, 48, 595, 429) if self._保存 else (40, 15, 595, 466)
        框.api_资源图("d", 520, 1 if self._保存 else 0, window[0], window[1])
        first = 1 if self._保存 else 0
        last = 3 if self._自动 else 6
        for slot in range(first, last):
            e, y = self._档[slot], self._行顶(slot)
            if not e.有效:
                continue
            框.api_资源图("d", 520, 10, 129, y)
            if self._自动:
                绘.api_文字(框, ("NEW", "PREV", "START")[slot], 165, y + 15, 2, 绘.白字)
            elif slot == 0:
                绘.api_文字(框, "AUTO", 165, y + 15, 2, 绘.白字)
            日, 月, 年 = e.日期
            绘.api_文字(框, str(年), 165, y + 36, 2, 绘.白字)
            绘.api_文字(框, f"{月}/{日}", 165, y + 57, 2, 绘.白字)
            框.api_资源图("d", 520, 2 + min(e.地图, 3) + 4 * min(e.阶段, 1), 209, y)
            for k, c in enumerate(e.人物[:4]):
                if c < 12:
                    框.api_资源图("d", 2, c, 289 + 72 * k, y)
        hovered = -1
        if 130 <= 框.指针x < 577:
            y = 框.指针y
            slot = (
                ((y - 57) // 72 + 1 if 58 <= y < 417 else -1)
                if self._保存
                else ((y - 24) // 72 if 25 <= y < 456 else -1)
            )
            if first <= slot < last:
                hovered = slot
        if hovered != self._悬选:
            if hovered >= 0 and arg_宿.声音:
                arg_宿.声音(0)
            self._悬选 = hovered
        if hovered >= 0:
            y = self._行顶(hovered)
            for r in ((127, y - 2, 579, y + 74), (128, y - 1, 578, y + 73)):
                绘.api_边框(框.画布, r, 绘.api_RGB(0xFFFF00))
        for slot in range(first, last):
            y = self._行顶(slot)
            绘.api_命中(
                arg_宿,
                (530 if self._保存 else 520) + slot,
                (130, y + 1, 577, y + 73),
                2,
                lambda slot=slot: arg_选(slot),
                self._保存 or self._档[slot].有效,
            )
        if arg_切换 is not None and not self._保存:
            # 六槽原版布局不变；左侧小按钮切换成三个只读自动恢复点。
            toggle = (47, 20, 124, 63)
            绘.api_边框(框.画布, toggle, 绘.api_RGB(0xFFFF00))
            绘.api_文字(框, "MANUAL" if self._自动 else "AUTO 3", 52, 34, 2, 绘.白字)
            绘.api_命中(arg_宿, 680, toggle, 3, arg_切换)
        绘.api_命中(arg_宿, 429, window, -1, lambda: None)
        绘.api_命中(arg_宿, 529, (0, 0, 640, 480), 4, arg_关)
