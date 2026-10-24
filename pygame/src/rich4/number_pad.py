# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/finance.cpp::NumberPad；数额确认交回真实规则回调。
# ◑ 导入
from collections.abc import Callable

from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.screen_draw import 屏幕宿主_类, 屏幕绘图_类


# ◕ 功能
class 数字板_类:
    """
    原Panel21数字板、稳定键号、量尺/拖拽与1/2倍几何，不代替交易规则。

    更新日志：
    2026.10.24 - 保留九位输入/十位MAX、取消等同0和回调可重入语义。
    """

    量尺 = (
        3,
        6,
        9,
        12,
        15,
        19,
        22,
        25,
        28,
        31,
        34,
        38,
        41,
        44,
        47,
        50,
        53,
        57,
        60,
        63,
        66,
        69,
        73,
        76,
        79,
        82,
        85,
        88,
        92,
        95,
        98,
        101,
        104,
        107,
    )
    键位 = (
        (2, 8, 63),
        (3, 64, 63),
        (4, 8, 95),
        (5, 48, 95),
        (6, 88, 95),
        (7, 8, 119),
        (8, 48, 119),
        (9, 88, 119),
        (10, 8, 143),
        (11, 48, 143),
        (12, 88, 143),
        (13, 8, 167),
        (14, 48, 167),
        (15, 88, 167),
    )

    def __init__(self) -> None:
        self._活跃 = self._拖 = False
        self._x, self._y, self._比例 = 256, 144, 1
        self._上限, self._文 = 0, "0"
        self._完成: Callable[[int], None] | None = None
        self._绘图 = 屏幕绘图_类()

    @staticmethod
    def _解析(arg_文: str) -> int:
        n = 0
        for c in arg_文:
            if "0" <= c <= "9":
                n = min(n * 10 + ord(c) - 48, 2147483647)
        return n

    @staticmethod
    def api_数字号(arg_字: int) -> int:
        return (
            905
            if arg_字 == 0
            else 900 + arg_字
            if arg_字 >= 7
            else 906 + arg_字
            if arg_字 >= 4
            else 912 + arg_字
        )

    def api_缩放(self, arg_比例: int) -> None:
        self._比例 = min(max(arg_比例, 1), 2)

    def api_比例(self) -> int:
        return self._比例

    def api_提示顶(self) -> int:
        return 2 if self._比例 > 1 else 42

    def api_活跃(self) -> bool:
        return self._活跃

    def api_上限(self) -> int:
        return self._上限

    def api_数字(self) -> str:
        return self._文

    def api_值(self) -> int:
        return min(self._解析(self._文), self._上限)

    def api_关闭(self) -> None:
        self._活跃 = False

    def api_打开(self, arg_上限: int, arg_完成: Callable[[int], None]) -> None:
        self._活跃, self._拖 = True, False
        self._上限, self._文, self._完成 = max(0, arg_上限), "0", arg_完成
        self._x = 320 - 64 * self._比例 if self._比例 > 1 else 256
        self._y = 92 if self._比例 > 1 else 144

    def _结束(self, arg_数: int) -> None:
        self._活跃 = False
        完成, self._完成 = self._完成, None
        if 完成:
            完成(arg_数)

    def _按键(self, arg_键: int) -> None:
        c = "??MEC0B789456123"[arg_键] if 2 <= arg_键 <= 15 else "?"
        if c == "M":
            self._文 = str(self._上限)
        elif c == "C":
            self._文 = "0"
        elif c == "B":
            self._文 = self._文[:-1] or "0"
        elif "0" <= c <= "9":
            if self._文 == "0":
                self._文 = ""
            if len(self._文) < 9:
                self._文 += c
            if not self._文:
                self._文 = "0"
            if self._解析(self._文) > self._上限:
                self._文 = str(max(0, self._上限))
        elif c == "E":
            self._结束(self.api_值())

    def _量尺(self, arg_x: int) -> None:
        pos = min(max(画框_类._零除(arg_x - self._x, self._比例) - 10, 0), 107)
        step = min(max((pos * 33 + 53) // 107, 0), 33)
        self._文 = str(self._上限 * step // 33)

    def api_取消(self, arg_宿: 屏幕宿主_类) -> None:
        if not self._活跃:
            return
        if arg_宿.声音:
            arg_宿.声音(4)
        self._结束(0)

    def api_键(self, arg_宿: 屏幕宿主_类, arg_键: str) -> None:
        if not self._活跃 or len(arg_键) != 1:
            return
        c = arg_键
        id = 0
        if "0" <= c <= "9":
            id = self.api_数字号(ord(c) - 48) - 900
        elif c in ("M", "m"):
            id = 2
        elif c == "\r":
            id = 3
        elif c in ("C", "c"):
            id = 4
        elif c == "\b":
            id = 6
        elif c in ("H", "h"):
            self._量尺(self._x + 64 * self._比例)
            if arg_宿.声音:
                arg_宿.声音(9)
            return
        if not id:
            return
        if arg_宿.声音:
            arg_宿.声音(7)
        self._按键(id)

    def api_下一键(self, arg_目标: int) -> int:
        want = str(min(max(arg_目标, 0), self._上限))
        if self._文 == want:
            return 903
        if self._文 == "0":
            return self.api_数字号(ord(want[0]) - 48)
        if want.startswith(self._文):
            return self.api_数字号(ord(want[len(self._文)]) - 48)
        return 904

    def api_绘制(self, arg_宿: 屏幕宿主_类) -> None:
        if not self._活跃:
            return
        框, k = arg_宿.框, self._比例

        def 图(arg_帧: int) -> 图像_类:
            return self._绘图.api_缩放(框, "p", 21, arg_帧, k)

        body = 图(0)
        if self._拖:
            if 框.按下:
                self._量尺(框.指针x)
            else:
                self._拖 = False
        框.api_图片(body, self._x, self._y)
        for n, c in enumerate(reversed(self._文[-9:])):
            框.api_图片(图(16 + ord(c) - 48), self._x + k * (107 - 12 * n), self._y + k * 11)
        框.api_图片(图(1), self._x + k * 10, self._y + k * 42)
        current = self.api_值()
        if current > 0 and self._上限 > 0:
            step = min(max(int(float(current) / self._上限 * 33), 0), 33)
            self._绘图.api_局部(
                框.画布,
                body,
                (k * 10, k * 42, k * (10 + self.量尺[step]), k * 54),
                self._x + k * 10,
                self._y + k * 42,
            )
        for id, x, y in self.键位:
            local = (
                (4, 59, 60, 91)
                if id == 2
                else (61, 59, 124, 91)
                if id == 3
                else (x - 4, y - 3, x + 37, y + 20)
            )
            rect = (
                self._x + k * local[0],
                self._y + k * local[1],
                self._x + k * local[2],
                self._y + k * local[3],
            )
            if 框.按下 and 框.api_指针内(rect):
                框.api_图片(图(id), self._x + k * x, self._y + k * y)
            self._绘图.api_命中(arg_宿, 900 + id, rect, 7, lambda id=id: self._按键(id))

        def 量尺() -> None:
            self._拖 = True
            self._量尺(框.指针x)

        self._绘图.api_命中(
            arg_宿,
            916,
            (self._x + k * 6, self._y + k * 34, self._x + k * 122, self._y + k * 58),
            9,
            量尺,
        )
        self._绘图.api_命中(
            arg_宿, 900, (self._x, self._y, self._x + k * 128, self._y + k * 192), -1, lambda: None
        )
        self._绘图.api_命中(arg_宿, 901, (0, 0, 640, 480), 4, lambda: self._结束(0))
