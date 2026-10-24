# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/native_frame.hpp::Button/Frame。
# ◑ 导入
from collections.abc import Callable
from dataclasses import dataclass

from rich4.artwork import 美术_类
from rich4.graphics import 图像_类
from rich4.native_ui import 原生界面_类, 字体_类


# ◕ 功能
@dataclass
class 按钮_类:
    """
    原稳定编号、半开命中区域和声音策略；绘制与派发分离。

    更新日志：
    2026.10.24 - 保留注册次序及原回调；禁用判定由应用派发执行。
    """

    编号: int
    区域: tuple[int, int, int, int]
    启用: bool
    动作: Callable[[], None]
    点击声音: bool = True


class 画框_类:
    """
    原Frame的画布、美术、字体、共用按钮列表与逻辑指针时钟。

    更新日志：
    2026.10.24 - 精灵原点抵消遵循原Frame；不改变底层blit的锚点约定。
    """

    人名 = (
        "約翰喬",
        "沙隆巴斯",
        "忍太郎",
        "錢夫人",
        "阿土伯",
        "莎拉公主",
        "宮本寶藏",
        "糖糖",
        "烏咪",
        "孫小美",
        "小丹尼",
        "金貝貝",
    )
    地图名 = ("台灣", "中國", "日本", "美國")

    def __init__(
        self,
        arg_画布: 图像_类,
        arg_美术: 美术_类,
        arg_字体: 字体_类,
        arg_按钮: list[按钮_类],
    ) -> None:
        self.画布, self.美术, self.字体, self.按钮 = arg_画布, arg_美术, arg_字体, arg_按钮
        self.指针x = self.指针y = -1
        self.按下, self.时钟 = False, 0

    @staticmethod
    def _零除(arg_值: int, arg_除: int) -> int:
        return abs(arg_值) // arg_除 * (-1 if arg_值 < 0 else 1)

    def api_图片(self, arg_图: 图像_类, arg_x: int, arg_y: int) -> None:
        self.画布.api_绘制(arg_图, arg_x + arg_图.原点x, arg_y + arg_图.原点y)

    def api_资源图(
        self,
        arg_库: str,
        arg_条: int,
        arg_帧: int,
        arg_x: int,
        arg_y: int,
    ) -> None:
        self.api_图片(self.美术.api_帧(arg_库, arg_条, arg_帧), arg_x, arg_y)

    def api_命中(
        self,
        arg_号: int,
        arg_框: tuple[int, int, int, int],
        arg_动作: Callable[[], None],
        arg_启用: bool = True,
    ) -> None:
        self.按钮.append(按钮_类(arg_号, arg_框, arg_启用, arg_动作))

    def api_按钮(
        self,
        arg_号: int,
        arg_框: tuple[int, int, int, int],
        arg_文: str | bytes,
        arg_动作: Callable[[], None],
        arg_启用: bool = True,
    ) -> None:
        self.api_命中(arg_号, arg_框, arg_动作, arg_启用)
        左, 顶, 右, 底 = arg_框
        原生界面_类.api_填充(
            self.画布, arg_框, 原生界面_类.纸色 if arg_启用 else 原生界面_类.api_颜色(190, 183, 158)
        )
        原生界面_类.api_边框(self.画布, arg_框, 原生界面_类.api_颜色(106, 72, 28))
        大小 = 16
        while 大小 > 12 and self.字体.api_测量(arg_文, 大小) > 右 - 左 - 8:
            大小 -= 2
        self.字体.api_绘制(
            self.画布,
            arg_文,
            左 + self._零除(右 - 左 - self.字体.api_测量(arg_文, 大小), 2),
            顶 + self._零除(底 - 顶 - 大小 - 3, 2),
            大小,
            原生界面_类.墨色 if arg_启用 else 原生界面_类.api_颜色(115, 110, 90),
        )

    def api_对话框(self, arg_框: tuple[int, int, int, int], arg_标题: str | bytes) -> None:
        左, 顶, 右, 底 = arg_框
        原生界面_类.api_填充(self.画布, arg_框, 原生界面_类.纸色)
        原生界面_类.api_边框(self.画布, arg_框, 原生界面_类.api_颜色(110, 74, 26))
        原生界面_类.api_边框(
            self.画布, (左 + 3, 顶 + 3, 右 - 3, 底 - 3), 原生界面_类.api_颜色(190, 146, 69)
        )
        self.字体.api_绘制(self.画布, arg_标题, 左 + 18, 顶 + 15, 20, 原生界面_类.蓝色)

    def api_文字(
        self,
        arg_文: str | bytes,
        arg_x: int,
        arg_y: int,
        arg_大小: int = 16,
        arg_色: int = 原生界面_类.墨色,
        arg_折宽: int = 0,
    ) -> None:
        self.字体.api_绘制(self.画布, arg_文, arg_x, arg_y, arg_大小, arg_色, arg_折宽)

    def api_居中(
        self,
        arg_文: str | bytes,
        arg_x: int,
        arg_y: int,
        arg_大小: int = 16,
        arg_色: int = 原生界面_类.墨色,
    ) -> None:
        self.api_文字(
            arg_文,
            arg_x - self._零除(self.字体.api_测量(arg_文, arg_大小), 2),
            arg_y,
            arg_大小,
            arg_色,
        )

    def api_指针内(self, arg_框: tuple[int, int, int, int]) -> bool:
        return 原生界面_类.api_包含(arg_框, self.指针x, self.指针y)
