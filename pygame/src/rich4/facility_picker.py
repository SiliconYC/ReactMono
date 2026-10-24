# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/facility.cpp；真实建造和改建仍由核心结算。
# ◑ 导入
from collections.abc import Callable

from rich4.game_types import 决策_类, 决策种类_类
from rich4.message_overlay import 消息层_类
from rich4.native_ui import 原生界面_类, 文字样式_类
from rich4.screen_draw import 屏幕宿主_类, 屏幕绘图_类


# ◕ 功能
class 设施选择_类:
    """
    原五类设施条、按决策键保留悬选、二次点击与可取消改建。

    更新日志：
    2026.10.24 - 原Data517图片、置灰、三层选框及稳定编号。
    """

    提示 = "請選擇設施類別"
    名字 = ("公  園", "旅  館", "購物中心", "加油站", "研究所")
    式 = 文字样式_类(
        16, 原生界面_类.api_颜色(240, 240, 240), True, True, False, 原生界面_类.api_颜色(16, 16, 16)
    )

    def __init__(self) -> None:
        self._键 = ""
        self._选中: int | None = None

    @staticmethod
    def _选项(arg_决: 决策_类, arg_值: int) -> int | None:
        return next((i for i, o in enumerate(arg_决.选项) if o.值 == arg_值), None)

    @classmethod
    def _取消项(cls, arg_决: 决策_类) -> int | None:
        return cls._选项(arg_决, -1) if arg_决.种类 == 决策种类_类.行动目标 else None

    @classmethod
    def api_接管(cls, arg_决: 决策_类) -> bool:
        return arg_决.种类 == 决策种类_类.建造设施 or (
            arg_决.种类 == 决策种类_类.行动目标
            and arg_决.提示 == cls.提示
            and all(o.位置 is None and -1 <= o.值 <= 4 for o in arg_决.选项)
        )

    @classmethod
    def api_可取消(cls, arg_决: 决策_类) -> bool:
        return cls._取消项(arg_决) is not None

    @classmethod
    def api_取消(cls, arg_宿: 屏幕宿主_类, arg_决: 决策_类, arg_答: Callable[[int], None]) -> None:
        index = cls._取消项(arg_决)
        if index is not None:
            if arg_宿.声音 is None:
                raise ValueError("原设施取消入口要求声音回调")
            arg_宿.声音(4)
            arg_答(index)

    def api_绘制(
        self,
        arg_宿: 屏幕宿主_类,
        arg_决: 决策_类,
        arg_键: str,
        arg_答: Callable[[int], None],
    ) -> None:
        框 = arg_宿.框
        if self._键 != arg_键:
            self._键, self._选中 = arg_键, None
        框.画布.api_绘制(框.美术.api_帧("d", 517, 5), 220, 140)
        消息层_类.api_文字(框, self.提示, 220, 122, 2, self.式)
        框.画布.api_绘制(框.美术.api_帧("d", 517, 4), 43, 279, arg_强制不透明=True)
        for slot in range(5):
            x, index = 50 + 68 * slot, self._选项(arg_决, slot)
            cell = (43 if slot == 0 else x, 279, x + 75 if slot == 4 else x + 68, 362)
            if index is None:
                屏幕绘图_类.api_暗化(框.画布, (x, 286, x + 68, 354), -16)
                continue
            chosen = self._选中 == slot
            if chosen:
                for inset in range(3):
                    屏幕绘图_类.api_边框(
                        框.画布,
                        (x + inset, 286 + inset, x + 68 - inset, 354 - inset),
                        屏幕绘图_类.api_RGB(0xFFFF00),
                    )

            def 选择(arg_槽: int = slot, arg_选: bool = chosen, arg_i: int = index) -> None:
                if arg_选:
                    arg_答(arg_i)
                else:
                    self._选中 = arg_槽

            屏幕绘图_类.api_命中(arg_宿, 210 + index, cell, 1 if chosen else 0, 选择)
        if self._选中 is not None:
            消息层_类.api_文字(框, self.名字[self._选中], 220, 154, 4, self.式)
        cancel = self._取消项(arg_决)
        left = 128 if cancel is not None else 180
        selected = self._选项(arg_决, self._选中) if self._选中 is not None else None
        rect = (left, 372, left + 80, 412)
        框.api_按钮(207, rect, "確定", lambda: None, selected is not None)
        框.按钮.pop()

        def 确定() -> None:
            if selected is not None:
                arg_答(selected)

        屏幕绘图_类.api_命中(arg_宿, 207, rect, 1, 确定, selected is not None)
        if cancel is not None:
            rect = (232, 372, 312, 412)
            框.api_按钮(210 + cancel, rect, "取消", lambda: None)
            框.按钮.pop()
            屏幕绘图_类.api_命中(arg_宿, 210 + cancel, rect, 4, lambda: arg_答(cancel))
