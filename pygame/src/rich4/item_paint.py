# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定items.cpp绘图辅助；原Frame与屏幕字样坐标语义不同，按原接口转写。
# ◑ 导入
from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类
from rich4.save_records import 玩家记录_类
from rich4.services import 服务_类


# ◕ 功能
class 物品绘图_类:
    """
    物品屏幕原居中行距、网格、下沉与暖色选择。

    更新日志：
    2026.10.24 - 按原下沉算法丢弃暗边高位，不复用保留高位的通用暗化。
    """

    白, 暗, 灰 = 32767, 2114, 21140

    @staticmethod
    def api_图(
        arg_框: 画框_类,
        arg_库: str,
        arg_条: int,
        arg_帧: int,
        arg_x: int,
        arg_y: int,
        arg_实: bool = False,
    ) -> None:
        arg_框.画布.api_绘制(
            arg_框.美术.api_帧(arg_库, arg_条, arg_帧), arg_x, arg_y, arg_强制不透明=arg_实
        )

    @staticmethod
    def api_字形(
        arg_框: 画框_类,
        arg_文: str,
        arg_x: int,
        arg_y: int,
        arg_大小: int,
        arg_色: int,
        arg_影: bool,
        arg_次色: int,
        arg_粗: bool,
    ) -> None:
        if arg_影:
            arg_框.字体.api_绘制(arg_框.画布, arg_文, arg_x + 1, arg_y + 1, arg_大小, arg_次色)
            if arg_粗:
                arg_框.字体.api_绘制(arg_框.画布, arg_文, arg_x + 2, arg_y + 1, arg_大小, arg_次色)
        arg_框.字体.api_绘制(arg_框.画布, arg_文, arg_x, arg_y, arg_大小, arg_色)
        if arg_粗:
            arg_框.字体.api_绘制(arg_框.画布, arg_文, arg_x + 1, arg_y, arg_大小, arg_色)

    @classmethod
    def api_中(
        cls,
        arg_框: 画框_类,
        arg_文: str,
        arg_x: int,
        arg_y: int,
        arg_大小: int,
        arg_色: int,
        arg_影: bool = True,
        arg_次色: int = 暗,
        arg_粗: bool = True,
    ) -> None:
        rows, height = arg_文.split("\n"), arg_大小 + 4
        y = arg_y - len(rows) * height // 2 + height // 2
        for row in rows:
            cls.api_字形(
                arg_框,
                row,
                arg_x - arg_框.字体.api_测量(row, arg_大小) // 2,
                y - arg_大小 * 9 // 16,
                arg_大小,
                arg_色,
                arg_影,
                arg_次色,
                arg_粗,
            )
            y += height

    @classmethod
    def api_右上(
        cls, arg_框: 画框_类, arg_文: str, arg_x: int, arg_y: int, arg_大小: int, arg_色: int
    ) -> None:
        cls.api_字形(
            arg_框,
            arg_文,
            arg_x - arg_框.字体.api_测量(arg_文, arg_大小) - 1,
            arg_y,
            arg_大小,
            arg_色,
            True,
            cls.暗,
            True,
        )

    @classmethod
    def api_右中(
        cls, arg_框: 画框_类, arg_文: str, arg_x: int, arg_y: int, arg_大小: int, arg_色: int
    ) -> None:
        cls.api_右上(arg_框, arg_文, arg_x, arg_y - arg_大小 * 9 // 16, arg_大小, arg_色)

    @staticmethod
    def api_格(arg_x: int, arg_y: int, arg_格: int) -> tuple[int, int, int, int]:
        c, r = arg_格 % 5, arg_格 // 5
        return arg_x + 6 + 80 * c, arg_y + 6 + 56 * r, arg_x + 84 + 80 * c, arg_y + 60 + 56 * r

    @classmethod
    def api_卡网格(cls, arg_框: 画框_类, arg_卡: list[int], arg_x: int, arg_y: int) -> list[int]:
        order = []
        for id in arg_卡:
            if not 1 <= id <= 30:
                continue
            tile = len(order)
            cls.api_中(
                arg_框,
                服务_类.卡名[id - 1],
                arg_x + 45 + 80 * (tile % 5),
                arg_y + 33 + 56 * (tile // 5),
                20,
                cls.白,
            )
            order.append(id)
        return order

    @classmethod
    def api_道具网格(
        cls, arg_框: 画框_类, arg_人: 玩家记录_类, arg_x: int, arg_y: int
    ) -> list[int]:
        order = []
        for id in range(1, 14):
            if not arg_人.道具[id - 1]:
                continue
            c, r = len(order) % 5, len(order) // 5
            cls.api_图(arg_框, "p", 11, id + 1, arg_x + 29 + 80 * c, arg_y + 33 + 56 * r)
            cls.api_右上(
                arg_框,
                f"×{arg_人.道具[id - 1]}",
                arg_x + 79 + 80 * c,
                arg_y + 23 + 56 * r,
                20,
                cls.白,
            )
            order.append(id)
        return order

    @staticmethod
    def api_下沉(arg_图: 图像_类, arg_区: tuple[int, int, int, int]) -> None:
        left, top, right, bottom = arg_区
        left, right = max(0, min(left, arg_图.宽)), max(0, min(right, arg_图.宽))
        top, bottom = max(0, min(top, arg_图.高)), max(0, min(bottom, arg_图.高))
        if right - left < 2 or bottom - top < 2:
            return
        for y in range(bottom - 1, top, -1):
            dest, src = y * arg_图.宽, (y - 1) * arg_图.宽
            arg_图.像素[dest + left + 1 : dest + right] = arg_图.像素[src + left : src + right - 1]
        for i in [
            *range(top * arg_图.宽 + left, top * arg_图.宽 + right),
            *(y * arg_图.宽 + left for y in range(top + 1, bottom)),
        ]:
            arg_图.像素[i] = (arg_图.像素[i] >> 1) & 0x3DEF

    @staticmethod
    def api_选色(arg_图: 图像_类, arg_区: tuple[int, int, int, int]) -> None:
        left, top, right, bottom = arg_区
        for y in range(max(0, top), min(arg_图.高, bottom)):
            for x in range(max(0, left), min(arg_图.宽, right)):
                i, value = y * arg_图.宽 + x, arg_图.像素[y * arg_图.宽 + x]
                arg_图.像素[i] = sum(
                    (((value >> (k * 5) & 31) + target) // 2) << (k * 5)
                    for k, target in enumerate((6, 28, 31))
                )

    api_边 = staticmethod(原生界面_类.api_边框)
