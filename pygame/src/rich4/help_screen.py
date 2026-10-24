# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/help.cpp/HelpScreen；帮助正文只读外部help.mkf。
# ◑ 导入
from rich4.artwork import 美术_类
from rich4.help_topics import 帮助目录_类
from rich4.native_ui import 原生界面_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类


# ◕ 功能
class 帮助屏幕_类:
    """
    原400方窗、八分类/八话题行、十四行正文和逐分类滚动记忆。

    更新日志：
    2026.10.24 - 保留原空页资源失败、冬眠说明修正及窗口内外命中顺序。
    """

    正文式 = 屏幕字样_类(12, 0x101010, 0x101010, 0)
    话题式 = 屏幕字样_类(15, 0x101010, 0x101010, 2)

    def __init__(self) -> None:
        self._开 = False
        self._x, self._y = 20, 60
        self._类别 = self._话题 = self._页 = 0
        self._首行 = [0] * 8
        self._页表: list[list[str]] = []
        self._已载 = -1

    def api_打开(self, arg_x: int, arg_y: int) -> None:
        self._开 = True
        self._x, self._y = 120 if arg_x < 0 else arg_x, 40 if arg_y < 0 else arg_y
        self._类别 = self._话题 = self._页 = 0
        self._已载 = -1

    def api_关闭(self) -> None:
        self._开 = False

    def api_活跃(self) -> bool:
        return self._开

    def api_取消(self, arg_宿: 屏幕宿主_类) -> None:
        arg_宿.声音(4)
        self.api_关闭()

    def _选择(self, arg_美术: 美术_类, arg_类: int, arg_话题: int) -> None:
        self._类别, self._话题 = arg_类, arg_话题
        entry = 帮助目录_类.分类[arg_类][2] + arg_话题
        if entry == self._已载:
            return
        self._已载, self._页, self._页表 = entry, 0, [[]]
        try:
            data = arg_美术.api_解码("h", entry)
        except (ValueError, IndexError, OSError):
            # 原select资源坏时已记录loaded且保留一空页；不伪造替代正文或反复重载。
            return
        lines = data.split(b"\0")
        while lines and not lines[-1]:
            lines.pop()
        text = ["@" if line == b"@" else 原生界面_类.api_繁中(line) for line in lines]
        if entry == 58:
            text = ["功能：讓其他所有角色", "冬眠五天，期間無法行", "動。"]
        for line in text:
            if line == "@":
                self._页表.append([])
                continue
            if len(self._页表[-1]) == 14:
                self._页表.append([])
            self._页表[-1].append(line)
        while len(self._页表) > 1 and not self._页表[-1]:
            self._页表.pop()

    def _滚动(self, arg_方向: int) -> None:
        count = len(帮助目录_类.分类[self._类别][1])
        if count <= 8:
            return
        first = self._首行[self._类别]
        target = max(first - 8, 0) if arg_方向 < 0 else min(first + 8, count - 8)
        self._话题 = min(max(self._话题 + target - first, 0), count - 1)
        self._首行[self._类别] = target

    def api_绘制(self, arg_宿: 屏幕宿主_类) -> None:
        if not self._开:
            return
        f, 绘 = arg_宿.框, 屏幕绘图_类
        if self._已载 < 0:
            self._选择(f.美术, self._类别, self._话题)
        x, y = self._x, self._y

        def 框(arg_l: int, arg_t: int, arg_r: int, arg_b: int) -> tuple[int, int, int, int]:
            return x + arg_l, y + arg_t, x + arg_r, y + arg_b

        def 图(arg_帧: int, arg_x: int, arg_y: int) -> None:
            f.api_资源图("h", 0, arg_帧, x + arg_x, y + arg_y)

        def 文(arg_文: str, arg_x: int, arg_y: int, arg_式: 屏幕字样_类 = self.正文式) -> None:
            绘.api_文字(f, arg_文, x + arg_x, y + arg_y, 2, arg_式)

        def 按下(arg_框: tuple[int, int, int, int]) -> bool:
            return f.按下 and f.api_指针内(arg_框)

        name, topics, _ = 帮助目录_类.分类[self._类别]
        count = len(topics)
        图(0, 0, 0)
        for i, (title, _, _) in enumerate(帮助目录_类.分类):
            文(title, 59, 73 + 36 * i)
        图(1, 26, 58 + 36 * self._类别)
        文(name, 59, 73 + 36 * self._类别)
        文(name, 140, 57)
        self._首行[self._类别] = first = min(self._首行[self._类别], max(count - 8, 0))
        up, down = 框(146, 30, 204, 58), 框(146, 58, 204, 78)
        if count > 8:
            图(6 if 按下(up) else 4, 170, 43)
            图(7 if 按下(down) else 5, 170, 59)
        for row in range(min(8, count - first)):
            index = first + row
            图(3 if index == self._话题 else 2, 108, 78 + 34 * row)
            文(topics[index], 150, 94 + 34 * row, self.话题式)
        文(topics[self._话题], 270, 63, self.话题式)
        lines = self._页表[min(self._页, len(self._页表) - 1)]
        for i, line in enumerate(lines):
            绘.api_文字(f, line, x + 232, y + 90 + 18 * i, 0, self.正文式)
        paged = len(self._页表) > 1
        prev, next = 框(296, 30, 344, 86), 框(344, 30, 396, 86)
        if paged:
            图(10 if 按下(prev) else 8, 322, 48)
            图(11 if 按下(next) else 9, 343, 48)
        for i in range(8):
            绘.api_命中(
                arg_宿,
                1120 + i,
                框(14, 56 + 36 * i, 98, 92 + 36 * i),
                1,
                lambda i=i: self._选择(f.美术, i, 0),
            )
        if count > 8:
            绘.api_命中(arg_宿, 1140, up, 1, lambda: self._滚动(-1), first > 0)
            绘.api_命中(arg_宿, 1141, down, 1, lambda: self._滚动(1), first + 8 < count)
        for row in range(min(8, count - first)):
            绘.api_命中(
                arg_宿,
                1130 + row,
                框(100, 77 + 34 * row, 204, 111 + 34 * row),
                1,
                lambda index=first + row: self._选择(f.美术, self._类别, index),
            )
        if paged:
            绘.api_命中(arg_宿, 1142, prev, 1, lambda: self._翻页(-1), self._页 > 0)
            绘.api_命中(
                arg_宿, 1143, next, 1, lambda: self._翻页(1), self._页 + 1 < len(self._页表)
            )
            绘.api_命中(arg_宿, 1144, 框(210, 86, 380, 380), 1, self._下一页)
        绘.api_命中(arg_宿, 1145, 框(0, 0, 400, 400), -1, lambda: None)
        绘.api_命中(arg_宿, 1146, (0, 0, 640, 480), 4, self.api_关闭)

    def _翻页(self, arg_方向: int) -> None:
        self._页 = max(self._页 - 1, 0) if arg_方向 < 0 else self._页 + 1

    def _下一页(self) -> None:
        self._页 = self._页 + 1 if self._页 + 1 < len(self._页表) else 0
