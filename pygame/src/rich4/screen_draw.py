# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/draw.hpp/draw.cpp；商业图像保持外部读取。
# ◑ 导入
from collections.abc import Callable
from dataclasses import dataclass

from rich4.calendar import 日期_类
from rich4.graphics import 图像_类
from rich4.holidays import 节日_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类
from rich4.world import 世界_类


# ◕ 功能
@dataclass(frozen=True)
class 屏幕字样_类:
    """
    原屏幕字体Style，flags位1/2/4分别为阴影/粗体/描边。

    更新日志：
    2026.10.24 - 与Font的TextStyle分开，保留原GDI基线偏移及对齐。
    """

    大小: int = 16
    颜色: int = 0xF0F0F0
    颜色2: int = 0x101010
    标志: int = 3


@dataclass
class 屏幕宿主_类:
    """
    原Host仅提供绘图与声音/短提示回调，不持有独立游戏状态。

    更新日志：
    2026.10.24 - instant只用于开发重放，正式屏幕使用真实时钟。
    """

    框: 画框_类
    声音: Callable[[int], None] | None = None
    提示: Callable[[str], None] | None = None
    即时: bool = False
    语音: Callable[[int], None] | None = None


class 屏幕绘图_类:
    """
    原八种对齐、颜色表、局部/缩放图片、节庆缓存及声音命中注册。

    更新日志：
    2026.10.24 - 绘图保留RGB555与独立透明掩码，局部图片坐标不改游戏投影。
    """

    白字 = 屏幕字样_类()
    黑字 = 屏幕字样_类(16, 0x101010, 0, 2)

    def __init__(self) -> None:
        self._节庆: dict[tuple[int, int], 图像_类] = {}
        self._缩放: dict[tuple[int, int], 图像_类] = {}
        self._缩放源: dict[int, 图像_类] = {}

    @staticmethod
    def api_RGB(arg_色: int) -> int:
        return 原生界面_类.api_玩家色(arg_色)

    @staticmethod
    def api_货币(arg_值: int) -> str:
        return f"{arg_值:,}"

    @staticmethod
    def _行(arg_文: str | bytes) -> list[bytes]:
        return 原生界面_类.api_原串(arg_文).split(b"\n")

    @classmethod
    def api_测量(cls, arg_框: 画框_类, arg_文: str | bytes, arg_式: 屏幕字样_类) -> int:
        return max(
            arg_框.字体.api_测量(行, arg_式.大小) + int(bool(arg_式.标志 & 2))
            for 行 in cls._行(arg_文)
        )

    @classmethod
    def _画行(
        cls,
        arg_框: 画框_类,
        arg_文: bytes,
        arg_x: int,
        arg_顶: int,
        arg_式: 屏幕字样_类,
    ) -> None:
        y = arg_顶 - 画框_类._零除(arg_式.大小, 5)

        def 画(arg_dx: int, arg_dy: int, arg_色: int) -> None:
            arg_框.字体.api_绘制(
                arg_框.画布, arg_文, arg_x + arg_dx, y + arg_dy, arg_式.大小, arg_色
            )
            if arg_式.标志 & 2:
                arg_框.字体.api_绘制(
                    arg_框.画布, arg_文, arg_x + arg_dx + 1, y + arg_dy, arg_式.大小, arg_色
                )

        if arg_式.标志 & 4:
            for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                画(dx, dy, cls.api_RGB(arg_式.颜色2))
        elif arg_式.标志 & 1:
            画(1, 1, cls.api_RGB(arg_式.颜色2))
        画(0, 0, cls.api_RGB(arg_式.颜色))

    @classmethod
    def api_文字(
        cls,
        arg_框: 画框_类,
        arg_文: str | bytes,
        arg_x: int,
        arg_y: int,
        arg_对齐: int,
        arg_式: 屏幕字样_类,
    ) -> None:
        行 = cls._行(arg_文)
        高, 除 = arg_式.大小 + 3, 画框_类._零除
        if arg_对齐 == 3:
            文, 位 = 原生界面_类.api_原串(arg_文), 0
            顶 = arg_y - 除(len(原生界面_类.api_码点(文)) * arg_式.大小, 2)
            while 位 < len(文):
                首 = 文[位]
                长 = 4 if 首 >= 0xF0 else 3 if 首 >= 0xE0 else 2 if 首 >= 0xC0 else 1
                字 = 文[位 : 位 + 长]
                cls._画行(arg_框, 字, arg_x - 除(cls.api_测量(arg_框, 字, arg_式), 2), 顶, arg_式)
                顶, 位 = 顶 + arg_式.大小, 位 + 长
            return
        if arg_对齐 in (4, 7):
            块高 = len(行) * 高 - 3
            顶 = arg_y - (除(块高, 2) if arg_对齐 == 4 else 块高)
            for 文 in 行:
                cls._画行(arg_框, 文, arg_x - 除(cls.api_测量(arg_框, 文, arg_式), 2), 顶, arg_式)
                顶 += 高
            return
        顶 = arg_y
        if arg_对齐 in (2, 5, 6):
            顶 -= 除(arg_式.大小, 2) + 除((len(行) - 1) * 高, 2)
        for 文 in 行:
            宽 = cls.api_测量(arg_框, 文, arg_式)
            左 = arg_x - 宽 if arg_对齐 in (1, 6) else arg_x - 除(宽, 2) if arg_对齐 == 2 else arg_x
            cls._画行(arg_框, 文, 左, 顶, arg_式)
            顶 += 高

    @staticmethod
    def _范围(arg_图: 图像_类, arg_框: tuple[int, int, int, int]) -> tuple[int, int, int, int]:
        左, 顶, 右, 底 = arg_框
        return (
            max(0, min(左, arg_图.宽)),
            max(0, min(顶, arg_图.高)),
            max(0, min(右, arg_图.宽)),
            max(0, min(底, arg_图.高)),
        )

    @classmethod
    def api_暗化(cls, arg_图: 图像_类, arg_框: tuple[int, int, int, int], arg_级: int) -> None:
        左, 顶, 右, 底 = cls._范围(arg_图, arg_框)
        倍 = min(max(32 + arg_级, 0), 32)
        for y in range(顶, 底):
            for x in range(左, 右):
                i = y * arg_图.宽 + x
                色 = arg_图.像素[i]
                arg_图.像素[i] = sum((((色 >> s) & 31) * 倍 // 32) << s for s in (0, 5, 10))

    @classmethod
    def api_灰阶(cls, arg_图: 图像_类, arg_框: tuple[int, int, int, int]) -> None:
        左, 顶, 右, 底 = cls._范围(arg_图, arg_框)
        for y in range(顶, 底):
            for x in range(左, 右):
                i = y * arg_图.宽 + x
                色 = arg_图.像素[i]
                灰 = (((色 >> 10) & 31) * 30 + ((色 >> 5) & 31) * 59 + (色 & 31) * 11) // 100
                arg_图.像素[i] = 灰 << 10 | 灰 << 5 | 灰

    def api_节日(self, arg_框: 画框_类, arg_世界: 世界_类) -> 图像_类 | None:
        日, 月, 年 = arg_世界.头.日期
        try:
            条 = 节日_类.api_节日图片(日期_类(年, 月, 日), arg_世界.头.地图, arg_世界.头.阶段)
        except ValueError:
            # 原festival_picture遇坏日期/图号保留季节图，不改变规则世界。
            return None
        if 条 is None:
            return None
        键 = id(arg_框.美术), 条
        if 键 not in self._节庆:
            self._节庆[键] = arg_框.美术.api_原图("d", 条, 200, 200)
        return self._节庆[键]

    @staticmethod
    def api_局部(
        arg_画: 图像_类,
        arg_图: 图像_类,
        arg_框: tuple[int, int, int, int],
        arg_x: int,
        arg_y: int,
    ) -> None:
        左, 顶, 右, 底 = arg_框
        arg_画.api_绘制(
            arg_图,
            arg_x - 左 + arg_图.原点x,
            arg_y - 顶 + arg_图.原点y,
            (arg_x, arg_y, arg_x + 右 - 左, arg_y + 底 - 顶),
        )

    api_边框 = staticmethod(原生界面_类.api_边框)

    @classmethod
    def api_按下斜面(cls, arg_图: 图像_类, arg_框: tuple[int, int, int, int]) -> None:
        左, 顶, 右, 底 = cls._范围(arg_图, arg_框)
        if 右 - 左 < 2 or 底 - 顶 < 2:
            return
        for y in range(底 - 1, 顶, -1):
            for x in range(右 - 1, 左, -1):
                arg_图.像素[y * arg_图.宽 + x] = arg_图.像素[(y - 1) * arg_图.宽 + x - 1]
        cls.api_暗化(arg_图, (左, 顶, 右, 顶 + 1), -16)
        cls.api_暗化(arg_图, (左, 顶 + 1, 左 + 1, 底), -16)

    def api_缩放(
        self,
        arg_框: 画框_类,
        arg_库: str,
        arg_条: int,
        arg_帧: int,
        arg_倍: int,
    ) -> 图像_类:
        源 = arg_框.美术.api_帧(arg_库, arg_条, arg_帧)
        if arg_倍 <= 1:
            return 源
        键 = id(源), arg_倍
        if 键 not in self._缩放:
            w, h = 源.宽 * arg_倍, 源.高 * arg_倍
            索 = [(y // arg_倍) * 源.宽 + x // arg_倍 for y in range(h) for x in range(w)]
            self._缩放[键] = 图像_类(
                w,
                h,
                [源.像素[i] for i in 索],
                源.原点x * arg_倍,
                源.原点y * arg_倍,
                bytes(源.不透明[i] for i in 索) if 源.不透明 else b"",
            )
            self._缩放源[id(源)] = 源
        return self._缩放[键]

    @staticmethod
    def api_背景(arg_框: 画框_类, arg_库: str, arg_条: int, arg_帧: int) -> None:
        图 = arg_框.美术.api_帧(arg_库, arg_条, arg_帧)
        arg_框.画布.api_绘制(图, 图.原点x, 图.原点y, arg_强制不透明=True)

    @classmethod
    def api_弹框(cls, arg_宿: 屏幕宿主_类, arg_文: str, arg_y: int = 196) -> None:
        arg_宿.框.api_资源图("p", 73, 5, 228, arg_y)
        cls.api_文字(arg_宿.框, arg_文, 320, arg_y + 44, 4, cls.黑字)

    @staticmethod
    def api_命中(
        arg_宿: 屏幕宿主_类,
        arg_号: int,
        arg_框: tuple[int, int, int, int],
        arg_声音: int,
        arg_动作: Callable[[], None],
        arg_启用: bool = True,
    ) -> None:
        声 = arg_宿.声音

        def 执行() -> None:
            if arg_声音 >= 0 and 声:
                声(arg_声音)
            arg_动作()

        arg_宿.框.api_命中(arg_号, arg_框, 执行, arg_启用)
        arg_宿.框.按钮[-1].点击声音 = False
