# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/ai_settings.cpp；编辑副本，确认才提交真实设置。
# ◑ 导入
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass

from rich4.game import 游戏会话_类
from rich4.game_types import 托管设置_类
from rich4.native_ui import 原生界面_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类
from rich4.world import 世界_类


# ◕ 功能
@dataclass(frozen=True)
class 托管动作_类:
    """
    原AiSettingsActions；每个变化槽位只提交一次，然后关闭。

    更新日志：
    2026.10.24 - 回调由正式应用接到GameSession.set_ai_settings。
    """

    应用: Callable[[int, 托管设置_类], None]
    关闭: Callable[[], None]


class 托管屏幕_类:
    """
    原Panel77、四人标签、卡道具/个性与两行比例编辑。

    更新日志：
    2026.10.24 - 原值与编辑分开拷贝，取消不写会话，拖条最大90仍可箭头至100。
    """

    def __init__(self) -> None:
        self._编辑: list[托管设置_类 | None] = [None] * 4
        self._原值: list[托管设置_类 | None] = [None] * 4
        self._选中 = 0

    def api_打开(self, arg_会: 游戏会话_类, arg_当前: int) -> bool:
        self._编辑 = [arg_会.api_托管设置(i) for i in range(4)]
        # C++的optional赋值复制值；共享同一Python对象会令确认时的变化比较失效。
        self._原值 = deepcopy(self._编辑)
        first = next((i for i, v in enumerate(self._编辑) if v is not None), None)
        if first is None:
            return False
        self._选中 = arg_当前 if 0 <= arg_当前 < 4 and self._编辑[arg_当前] is not None else first
        return True

    def api_编辑(self, arg_槽: int) -> 托管设置_类 | None:
        return deepcopy(self._编辑[arg_槽]) if 0 <= arg_槽 < 4 else None

    def api_取消(self, arg_宿: 屏幕宿主_类, arg_动: 托管动作_类) -> None:
        if arg_宿.声音 is None:
            raise ValueError("原托管取消入口要求声音回调")
        arg_宿.声音(4)
        arg_动.关闭()

    def api_绘制(self, arg_宿: 屏幕宿主_类, arg_世: 世界_类, arg_动: 托管动作_类) -> None:
        框, 文, hit = arg_宿.框, 屏幕绘图_类.api_文字, 屏幕绘图_类.api_命中

        def 图(arg_号: int, arg_x: int, arg_y: int) -> None:
            框.画布.api_绘制(框.美术.api_帧("p", 77, arg_号), arg_x, arg_y)

        title, label, button = 屏幕字样_类(20), 屏幕字样_类(), 屏幕字样_类(20, 0x101010, 0, 2)
        图(0, 102, 62)
        for s, x, y in (("託管AI", 275, 88), ("個  性", 275, 176), ("資金運用比例", 351, 308)):
            文(框, s, x, y, 2, title)
        for s, y in (
            ("使用卡片", 115),
            ("使用道具", 146),
            ("乖寶寶", 203),
            ("普通人", 235),
            ("大老奸", 268),
        ):
            文(框, s, 346, y, 2, label)
        for s, x, y, mode in (
            ("現金", 293, 339, 6),
            ("存款", 407, 339, 5),
            ("股票", 293, 372, 6),
            ("資金", 407, 372, 5),
        ):
            文(框, s, x, y, mode, label)
        文(框, "確定", 499, 187, 3, button)
        文(框, "取消", 499, 275, 3, button)
        for slot, setting in enumerate(self._编辑[: len(arg_世.玩家)]):
            if setting is None:
                continue
            y = 70 + 83 * slot
            图(1 if slot == self._选中 else 2, 110, y)
            图(6 + arg_世.玩家[slot].记录.角色 % 12, 182, 110 + 83 * slot)
            if setting.自动:
                图(3, 121, 106 + 83 * slot)

            def 选择(arg_槽: int = slot) -> None:
                e = self._编辑[arg_槽]
                if self._选中 == arg_槽 and e is not None:
                    e.自动 = not e.自动
                self._选中 = arg_槽

            hit(arg_宿, 1600 + slot, (110, y, 226, y + 83), 1, 选择)
        if self._选中 >= 4 or self._编辑[self._选中] is None:
            return
        edit = self._编辑[self._选中]
        if edit.卡片策略 & 1:
            图(3, 288, 107)
        if edit.卡片策略 & 2:
            图(3, 288, 139)
        图(3, 288, (195, 227, 259)[min(edit.性格, 2)])

        def 卡片() -> None:
            edit.卡片策略 ^= 1

        def 道具() -> None:
            edit.卡片策略 ^= 2

        hit(arg_宿, 1610, (280, 100, 420, 130), 1, 卡片)
        hit(arg_宿, 1611, (280, 131, 420, 161), 1, 道具)
        for p, y in enumerate((203, 235, 268)):

            def 个性(arg_p: int = p) -> None:
                edit.性格 = arg_p

            hit(arg_宿, 1612 + p, (280, y - 15, 420, y + 16), 1, 个性)
        for row in range(2):
            bar = (310, 357 if row else 322, 390, 391 if row else 356)
            down = (266, bar[1], 310, bar[3])
            up = (390, bar[1], 436, bar[3])
            if 框.按下 and 框.api_指针内(bar):
                value = min(max((框.指针x - 310) // 8 * 10, 0), 100)
                if row:
                    edit.股票比例 = value
                else:
                    edit.现金比例 = value
            value = edit.股票比例 if row else edit.现金比例
            top = 361 if row else 328
            for k in range(10):
                if value > k * 10:
                    原生界面_类.api_填充(
                        框.画布,
                        (311 + 8 * k, top, 318 + 8 * k, top + 22),
                        屏幕绘图_类.api_RGB(0xFF0000),
                    )
            if 框.按下 and 框.api_指针内(down):
                图(4, 299, top + 1)
            if 框.按下 and 框.api_指针内(up):
                图(5, 393, top + 1)

            def 比例(arg_行: int, arg_差: int) -> None:
                n = edit.股票比例 if arg_行 else edit.现金比例
                n = max(0, n - 10) if arg_差 < 0 else min(100, n + 10)
                if arg_行:
                    edit.股票比例 = n
                else:
                    edit.现金比例 = n

            hit(arg_宿, 1623 if row else 1620, down, 1, lambda row=row: 比例(row, -10))
            hit(arg_宿, 1624 if row else 1621, up, 1, lambda row=row: 比例(row, 10))
            hit(arg_宿, 1625 if row else 1622, bar, -1, lambda: None)
        if 框.按下 and 框.api_指针内((468, 150, 532, 226)):
            屏幕绘图_类.api_按下斜面(框.画布, (479, 159, 519, 215))
        if 框.按下 and 框.api_指针内((468, 238, 532, 314)):
            屏幕绘图_类.api_按下斜面(框.画布, (479, 247, 519, 303))

        def 确定() -> None:
            for slot, e in enumerate(self._编辑):
                if e is not None and e != self._原值[slot]:
                    arg_动.应用(slot, e)
            arg_动.关闭()

        hit(arg_宿, 1630, (468, 150, 532, 226), 2, 确定)
        hit(arg_宿, 1631, (468, 238, 532, 314), 4, arg_动.关闭)
