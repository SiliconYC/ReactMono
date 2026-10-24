# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/menus.cpp::MainMenu，使用原Data1图片与悬选/命中语义。
# ◑ 导入
from collections.abc import Callable
from dataclasses import dataclass

from rich4.graphics import 图像_类
from rich4.screen_draw import 屏幕宿主_类, 屏幕绘图_类


# ◕ 功能
@dataclass(frozen=True)
class 主菜单动作_类:
    """
    原MainMenu五入口；真实应用负责新局、读档、设置、退出和新资料片。

    更新日志：
    2026.10.24 - 不给运行入口假成功回调，保留读取可用标志。
    """

    开始: Callable[[], None]
    读取: Callable[[], None]
    设置: Callable[[], None]
    退出: Callable[[], None]
    新阶段: Callable[[], None]
    可读取: bool = True


class 主菜单_类:
    """
    原五按钮布局、精灵原点、首次悬选优先与扩大EXIT点击区。

    更新日志：
    2026.10.24 - 禁用读取仍保留悬选行为，实际派发须检查启用。
    """

    def __init__(self) -> None:
        self._悬选 = -1

    @staticmethod
    def _框(arg_图: 图像_类, arg_x: int, arg_y: int) -> tuple[int, int, int, int]:
        return (
            arg_x - arg_图.原点x,
            arg_y - arg_图.原点y,
            arg_x - arg_图.原点x + arg_图.宽,
            arg_y - arg_图.原点y + arg_图.高,
        )

    def api_绘制(self, arg_宿: 屏幕宿主_类, arg_动: 主菜单动作_类) -> None:
        框, 绘 = arg_宿.框, 屏幕绘图_类
        绘.api_背景(框, "d", 1, 0)
        entries = (
            (1, 190, 380, arg_动.开始, True),
            (2, 328, 380, arg_动.读取, arg_动.可读取),
            (3, 468, 378, arg_动.设置, True),
            (5, 328, 450, arg_动.退出, True),
            (4, 62, 380, arg_动.新阶段, True),
        )
        hovered = -1
        for i, (_, x, y, _, _) in enumerate(entries):
            框.画布.api_绘制(框.美术.api_帧("d", 1, 2 * i + 1), x, y)
            rect = self._框(框.美术.api_帧("d", 1, 2 * i + 2), x, y)
            if hovered < 0 and 框.api_指针内(rect):
                hovered = i
        if hovered != self._悬选:
            if hovered >= 0 and arg_宿.声音:
                arg_宿.声音(0)
            self._悬选 = hovered
        if hovered >= 0:
            _, x, y, _, _ = entries[hovered]
            框.画布.api_绘制(框.美术.api_帧("d", 1, 2 * hovered + 2), x, y)
        绘.api_文字(框, "V3.11", 638, 470, 6, 绘.白字)
        for i, (id, x, y, action, enabled) in enumerate(entries):
            rect = self._框(框.美术.api_帧("d", 1, 2 * i + 2), x, y)
            if id == 5:
                a, b, c, d = rect
                rect = a - 10, b - 6, c + 10, 480
            绘.api_命中(arg_宿, id, rect, 2 if id == 5 else 1, action, enabled)
