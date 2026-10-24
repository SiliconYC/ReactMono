# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/menus.cpp::NewGameSetup；保留原时钟、私有MT及不支持行。
# ◑ 导入
from collections.abc import Callable

from rich4.graphics import 图像_类
from rich4.menu_random import 菜单随机_类
from rich4.native_ui import 原生界面_类
from rich4.new_game_types import 新局选择_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类
from rich4.world_options import 新玩家_类


# ◕ 功能
class 新局屏幕_类:
    """
    原Jump背景、十二人头像、设置下拉与骑乘退场；原未实现行保持禁用。

    更新日志：
    2026.10.24 - 1100毫秒补一人，50毫秒加速退场，保留即时重放分支。
    """

    资金 = (300000, 200000, 100000, 50000, 30000, 10000)
    期间 = ("無限期", "二年", "一年", "六個月", "三個月", "一個月")
    倍数 = (0, 100, 50, 10, 5, 3)
    标签 = ("遊戲人數", "總 資 金", "行進方式", "土地權限", "遊戲時間", "勝利條件")
    人名 = (
        "約 翰 喬",
        "沙隆巴斯",
        "忍 太 郎",
        "錢 夫 人",
        "阿 土 伯",
        "莎拉公主",
        "宮本寶藏",
        "糖 糖",
        "烏 咪",
        "孫 小 美",
        "小 丹 尼",
        "金 貝 貝",
    )
    下拉框 = (
        (561, 251, 602, 320),
        (536, 287, 602, 425),
        (561, 323, 602, 392),
        (536, 195, 602, 333),
        (536, 231, 602, 369),
        (516, 267, 602, 405),
    )
    下拉帧 = (5, 6, 5, 6, 6, 7)

    def __init__(self) -> None:
        self._阶段 = self._地图 = 0
        self._值 = [2, 1, 0, 0, 0, 0]
        self._人选: list[int] = []
        self._人类数 = 0
        self._下拉 = self._悬选 = -1
        self._填充 = self._离开 = False
        self._填时 = self._离时 = 0
        self._随机 = 菜单随机_类(1)
        self._背景 = 图像_类(0, 0, [])
        self._背景键 = -1

    def api_打开(self, arg_阶段: int, arg_地图: int, arg_种子: int) -> None:
        values = self._值.copy()
        self.__init__()
        self._值, self._阶段, self._地图 = values, arg_阶段, arg_地图 % 4
        self._随机.api_播种(arg_种子)

    def api_人选(self) -> tuple[int, ...]:
        return tuple(self._人选)

    def api_地图(self) -> int:
        return self._地图

    def api_阶段(self) -> int:
        return self._阶段

    def api_人数(self) -> int:
        return self._值[0] + 2

    def api_忙(self) -> bool:
        return self._填充 or self._离开

    def _选择(self) -> 新局选择_类:
        return 新局选择_类(
            self._阶段,
            self._地图,
            self.资金[self._值[1]],
            self._值[3],
            [
                新玩家_类(c, 1 if i < self._人类数 else 2, self._值[2], 0)
                for i, c in enumerate(self._人选)
            ],
        )

    def _补一人(self) -> None:
        available = [i for i in range(12) if i not in self._人选]
        if available and len(self._人选) < self.api_人数():
            self._人选.append(available[self._随机.api_取() % len(available)])

    def api_取消(self, arg_宿: 屏幕宿主_类, arg_关: Callable[[], None]) -> None:
        if arg_宿.声音:
            arg_宿.声音(4)
        if self._下拉 >= 0:
            self._下拉 = -1
        elif not self.api_忙():
            arg_关()

    def _条名(self, arg_行: int, arg_值: int) -> str:
        if arg_行 == 0:
            return ("二人", "三人", "四人")[arg_值]
        if arg_行 == 1:
            return str(self.资金[arg_值])
        if arg_行 == 2:
            return ("步行", "機車", "汽車")[arg_值]
        if arg_行 == 5:
            return "無限" if arg_值 == 0 else str(self.资金[self._值[1]] * self.倍数[arg_值])
        return self.期间[arg_值]

    def _画背景(self, arg_宿: 屏幕宿主_类) -> None:
        框, key = arg_宿.框, self._阶段 * 4 + self._地图
        if self._背景键 != key:
            self._背景 = 框.美术.api_原图("j", key, 640, 480)
            屏幕绘图_类.api_暗化(self._背景, (0, 0, 640, 480), -16)
            self._背景键 = key
        shift = 框.时钟 // 100 * 2 % 640
        for x in (-shift, 640 - shift):
            框.画布.api_绘制(self._背景, x, 0, arg_强制不透明=True)

    def api_绘制(
        self,
        arg_宿: 屏幕宿主_类,
        arg_开: Callable[[新局选择_类], None],
        arg_关: Callable[[], None],
    ) -> None:
        框, 文, 绘 = arg_宿.框, 屏幕绘图_类.api_文字, 屏幕绘图_类
        if self._填充 and ((框.时钟 - self._填时) & 0xFFFFFFFFFFFFFFFF) >= 1100:
            self._补一人()
            self._填时 = 框.时钟
            if len(self._人选) >= self.api_人数():
                self._填充, self._离开, self._离时 = False, True, 框.时钟
        shift = 0
        if self._离开:
            steps = ((框.时钟 - self._离时) & 0xFFFFFFFFFFFFFFFF) // 50
            shift = 4 * steps + 3 * steps * steps
            if shift > 660:
                self._离开 = False
                arg_开(self._选择())
                return
        self._画背景(arg_宿)
        count = self.api_人数()
        框.api_资源图("j", 8, 0, 4, 10 - shift)
        for i in range(12):
            x, y = 8 + 72 * (i % 6), 15 + 72 * (i // 6) - shift
            框.api_资源图("d", 2, i, x, y)
            if i in self._人选:
                绘.api_暗化(框.画布, (x, y, x + 72, y + 72), -16)
        hovered = -1
        if not self.api_忙() and self._下拉 < 0 and 框.api_指针内((8, 15, 440, 159)):
            i = (框.指针y - 15) // 72 * 6 + (框.指针x - 8) // 72
            if i not in self._人选:
                hovered = i
        if hovered != self._悬选:
            if hovered >= 0 and arg_宿.声音:
                arg_宿.声音(0)
            self._悬选 = hovered
        if hovered >= 0:
            column, row = hovered % 6, hovered // 6
            框.api_资源图("d", 2, hovered, 12 + 72 * column, 11 + 72 * row)
            tag = 83 if row == 0 else 63
            绘.api_暗化(框.画布, (13 + 72 * column, tag, 83 + 72 * column, tag + 20), -20)
            文(框, self.人名[hovered], 48 + 72 * column, tag + 10, 2, 绘.白字)
        框.api_资源图("j", 8, 20 * self._阶段 + 1, 445 + shift, 10)
        框.api_资源图("j", 8, 8, 595 + shift, 30 + 32 * self._地图)
        label, grey = 屏幕字样_类(15, 0xFFFFFF), 屏幕字样_类(15, 0x909090)
        value, greyvalue = (
            屏幕字样_类(15, 0x101010, 0x101010, 2),
            屏幕字样_类(15, 0x808080, 0x101010, 2),
        )
        for row in range(6):
            y = 238 + 36 * row
            文(框, self.标签[row], 453 + shift, y, 5, label if row < 4 else grey)
            文(
                框,
                self._条名(row, self._值[row]),
                600 + shift,
                y,
                6,
                value if row < 4 else greyvalue,
            )
        pressing = 框.按下 and not self.api_忙() and self._下拉 < 0
        if pressing and 框.api_指针内((456, 176, 536, 216)) and self._人选:
            框.api_资源图("j", 8, 2, 456, 176)
        if pressing and 框.api_指针内((544, 176, 624, 216)):
            框.api_资源图("j", 8, 3, 544, 176)
        for row in range(4):
            r = (602, 226 + 36 * row, 626, 251 + 36 * row)
            if (pressing or self._下拉 == row) and (self._下拉 == row or 框.api_指针内(r)):
                框.api_资源图("j", 8, 4, 602, r[1])
        for slot, character in enumerate(self._人选):
            entry = 9 + 3 * character + self._值[2]
            frames = max(1, 框.美术.api_帧数("j", entry))
            x = ((330, 110, 0, 0), (366, 220, 74, 0), (385, 275, 165, 55))[
                min(max(count, 2), 4) - 2
            ][slot]
            框.画布.api_绘制(框.美术.api_帧("j", entry, 框.时钟 // 100 % frames), x + shift, 440)
        if self._离开:

            def 跳过() -> None:
                self._离时 = 0

            绘.api_命中(arg_宿, 49, (0, 0, 640, 480), -1, 跳过)
            return
        if self._填充:
            return
        if self._下拉 >= 0:
            a, b, c, d = self.下拉框[self._下拉]
            框.api_资源图("j", 8, self.下拉帧[self._下拉], a, b)
            for n in range(3 if self._下拉 in (0, 2) else 6):
                item = (a + 2, b + 2 + 23 * n, c - 1, b + 22 + 23 * n)
                lit = 框.api_指针内(item)
                if lit:
                    原生界面_类.api_填充(框.画布, item, 绘.api_RGB(0xAA0000))
                文(
                    框,
                    self._条名(self._下拉, n),
                    c - 2,
                    b + 13 + 23 * n,
                    6,
                    屏幕字样_类(15, 0xFFFFFF, 0x101010, 2) if lit else value,
                )

                def 选条(arg_n: int = n) -> None:
                    self._值[self._下拉] = arg_n
                    if self._下拉 == 0 and len(self._人选) > arg_n + 2:
                        self._人选 = self._人选[: arg_n + 2]
                    self._下拉 = -1

                绘.api_命中(arg_宿, 130 + n, item, 1, 选条)

            def 关条() -> None:
                self._下拉 = -1

            绘.api_命中(arg_宿, 49, (0, 0, 640, 480), 4, 关条)
            return
        for i in range(12):
            x, y = 8 + 72 * (i % 6), 15 + 72 * (i // 6)

            def 选人(arg_i: int = i) -> None:
                if arg_i in self._人选:
                    self._人选.remove(arg_i)
                elif len(self._人选) < count:
                    self._人选.append(arg_i)

            绘.api_命中(arg_宿, 10 + i, (x, y, x + 72, y + 72), 1, 选人)
        for m in range(4):

            def 选图(arg_m: int = m) -> None:
                self._地图 = arg_m

            绘.api_命中(arg_宿, 30 + m, (457, 31 + 32 * m, 626, 63 + 32 * m), 1, 选图)

        def 确定() -> None:
            self._人类数 = len(self._人选)
            if arg_宿.即时:
                for i in range(12):
                    if len(self._人选) >= self.api_人数():
                        break
                    if i not in self._人选:
                        self._人选.append(i)
                arg_开(self._选择())
                return
            self._填充, self._填时 = True, 框.时钟

        绘.api_命中(arg_宿, 40, (456, 176, 536, 216), 1, 确定, bool(self._人选))
        绘.api_命中(arg_宿, 41, (544, 176, 624, 216), 2, arg_关)
        for row in range(6):

            def 下拉(arg_r: int = row) -> None:
                self._下拉 = arg_r

            r = (self.下拉框[row][0], 220 + 36 * row, 630, 256 + 36 * row)
            绘.api_命中(arg_宿, 43 + row, r, 0, 下拉, row < 4)
