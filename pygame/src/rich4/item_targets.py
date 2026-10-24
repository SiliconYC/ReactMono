# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定items.cpp::Screens::draw_targets；只消费核心给出的实际位置选项。
# ◑ 导入
from collections.abc import Callable

from rich4.board_models import 相机_类
from rich4.board_projection import 棋盘投影_类
from rich4.game_types import 决策_类, 决策种类_类
from rich4.item_paint import 物品绘图_类
from rich4.native_frame import 画框_类
from rich4.services import 服务_类


# ◕ 功能
class 地图目标绘制_类:
    """
    原目标光标动画、选定跳箭与重叠时最近中心命中。

    更新日志：
    2026.10.24 - 时钟/上次道具由Screens显式传入，不产生目标或改规则世界。
    """

    @staticmethod
    def api_绘制(
        arg_框: 画框_类,
        arg_决: 决策_类,
        arg_相机: 相机_类,
        arg_选: int | None,
        arg_点: Callable[[int], None],
        arg_工具: int,
        arg_时: int,
    ) -> str:
        first, count, card, item = 8, 4, False, arg_工具
        for i, name in enumerate(服务_类.卡名):
            if arg_决.提示.startswith(name):
                card, item = True, i + 1
        if card:
            first, count = 12, 15
        elif arg_决.种类 == 决策种类_类.行动目标 and arg_工具:
            if arg_工具 in (2, 3, 4, 7, 13):
                first, count = {2: 0, 3: 1, 4: 2, 7: 3, 13: 4}[arg_工具], 1
            elif arg_工具 == 9:
                first, count = 9, 3
            elif arg_工具 == 11:
                first, count = (9, 3) if "目的" in arg_决.提示 else (32, 2)
        markers = []
        for i, o in enumerate(arg_决.选项):
            if o.位置 is None:
                continue
            point = 棋盘投影_类.api_投影((o.位置.x, o.位置.y), arg_相机)
            if point is not None and 12 <= point[0] < 428 and 54 <= point[1] < 466:
                markers.append((i, point))
        animation, 绘 = arg_时 // 100, 物品绘图_类
        shot = f"target-{'card' if card else 'tool'}-{item}" + (
            "-selected" if arg_选 is not None else ""
        )
        for i, (x, y) in markers:
            if arg_选 == i:
                continue
            if (animation // 3 + i) % 2 == 0:
                绘.api_图(arg_框, "d", 0, 42, x, y + 12)
            绘.api_图(arg_框, "d", 0, first + (animation + i) % count, x, y)
        for i, (x, y) in markers:
            if arg_选 != i:
                continue
            绘.api_图(arg_框, "d", 0, 42, x, y + 12)
            绘.api_图(arg_框, "d", 0, first + animation % count, x, y)
            bounce = arg_时 // 80 % 8
            绘.api_图(arg_框, "d", 0, 38, x, y - 16 - (bounce if bounce < 4 else 8 - bounce))

        def 最近() -> None:
            best, distance = None, 0
            for i, (x, y) in markers:
                d = (x - arg_框.指针x) ** 2 + (y - arg_框.指针y) ** 2
                if best is None or d < distance:
                    best, distance = i, d
            if best is not None:
                arg_点(best)

        for i, (x, y) in markers:
            arg_框.api_命中(5000 + i, (x - 30, y - 32, x + 30, y + 28), 最近)
        return shot
