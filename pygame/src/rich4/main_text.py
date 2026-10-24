# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/main_screen.cpp匿名绘图辅助；主屏GDI墨框约定不同于菜单。
# ◑ 导入
from dataclasses import dataclass

from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类


# ◕ 功能
@dataclass(frozen=True)
class 主屏字样_类:
    """
    主屏Text样式，spacing为原值，实际附加间距是spacing-1。

    更新日志：
    2026.10.24 - 单色阈值、随尺寸增宽的描粗与墨框锚定按原实现。
    """

    大小: int = 12
    颜色: int = 2114
    间距: int = 1
    描边: int | None = None
    粗体: bool = False


class 主屏绘字_类:
    """
    原主屏字符消费/墨框对齐、描边、色章和受限矩形描线。

    更新日志：
    2026.10.24 - 按字节切UTF8，不以Python字符串迭代改写坏编码边界。
    """

    @staticmethod
    def api_字列(arg_文: str | bytes) -> list[bytes]:
        文, 位, 组 = 原生界面_类.api_原串(arg_文), 0, []
        while 位 < len(文):
            首 = 文[位]
            长 = 4 if 首 >= 0xF0 else 3 if 首 >= 0xE0 else 2 if 首 >= 0xC0 else 1
            组.append(文[位 : 位 + 长])
            位 += 长
        return 组

    @classmethod
    def _一行(
        cls,
        arg_框: 画框_类,
        arg_文: str | bytes,
        arg_x: int,
        arg_y: int,
        arg_式: 主屏字样_类,
        arg_色: int,
    ) -> None:
        x = arg_x
        for 字 in cls.api_字列(arg_文):
            描数 = max(1, arg_式.大小 // 20) if arg_式.粗体 else 1 if arg_式.大小 >= 18 else 0
            for dx in range(描数 + 1):
                arg_框.字体.api_绘制(arg_框.画布, 字, x + dx, arg_y, arg_式.大小, arg_色, 0, True)
            x += arg_框.字体.api_测量(字, arg_式.大小, True) + arg_式.间距 - 1

    @classmethod
    def _样式(
        cls,
        arg_框: 画框_类,
        arg_文: str | bytes,
        arg_x: int,
        arg_y: int,
        arg_式: 主屏字样_类,
    ) -> None:
        if arg_式.描边 is not None:
            for dy in range(3):
                for dx in range(3):
                    if dx != 1 or dy != 1:
                        cls._一行(
                            arg_框, arg_文, arg_x + dx - 1, arg_y + dy - 1, arg_式, arg_式.描边
                        )
        cls._一行(arg_框, arg_文, arg_x, arg_y, arg_式, arg_式.颜色)

    @classmethod
    def api_文字(
        cls,
        arg_框: 画框_类,
        arg_文: str | bytes,
        arg_x: int,
        arg_y: int,
        arg_对齐: int,
        arg_式: 主屏字样_类 = 主屏字样_类(),
    ) -> None:
        除, 字体 = 画框_类._零除, arg_框.字体
        if arg_对齐 == 3:
            字组 = cls.api_字列(arg_文)
            步 = arg_式.大小 + arg_式.间距 + int(arg_式.描边 is not None or arg_式.粗体)
            顶 = arg_y - 除(len(字组) * 步 - arg_式.间距, 2)
            for 字 in 字组:
                左, 上, 右, 下 = 字体.api_墨框(字, arg_式.大小, 0, True)
                cls._样式(
                    arg_框, 字, arg_x - 除(左 + 右, 2), 顶 + 除(arg_式.大小 - 下 - 上, 2), arg_式
                )
                顶 += 步
            return
        左, 上, 右, 下 = 字体.api_墨框(arg_文, arg_式.大小, arg_式.间距 - 1, True)
        y = arg_y - (除(上 + 下, 2) if arg_对齐 == 2 else 上)
        x = arg_x - (左 if arg_对齐 == 0 else 右 if arg_对齐 == 1 else 除(左 + 右, 2))
        cls._样式(arg_框, arg_文, x, y, arg_式)

    @staticmethod
    def api_色章(
        arg_画: 图像_类,
        arg_章: 图像_类,
        arg_x: int,
        arg_y: int,
        arg_色: int,
        arg_裁剪: tuple[int, int, int, int],
    ) -> None:
        左, 顶 = arg_x - arg_章.原点x, arg_y - arg_章.原点y
        for 行 in range(arg_章.高):
            for 列 in range(arg_章.宽):
                i = 行 * arg_章.宽 + 列
                可见 = arg_章.不透明[i] != 0 if arg_章.不透明 else arg_章.像素[i] != 0
                x, y = 左 + 列, 顶 + 行
                if 可见 and 原生界面_类.api_包含(arg_裁剪, x, y):
                    arg_画.像素[y * arg_画.宽 + x] = arg_色

    @staticmethod
    def api_线框(
        arg_画: 图像_类,
        arg_框: tuple[int, int, int, int],
        arg_色: int,
        arg_裁剪: tuple[int, int, int, int],
    ) -> None:
        左, 顶, 右, 底 = arg_框
        for x in range(左, 右):
            for y in (顶, 底 - 1):
                if 原生界面_类.api_包含(arg_裁剪, x, y):
                    arg_画.像素[y * arg_画.宽 + x] = arg_色
        for y in range(顶, 底):
            for x in (左, 右 - 1):
                if 原生界面_类.api_包含(arg_裁剪, x, y):
                    arg_画.像素[y * arg_画.宽 + x] = arg_色
