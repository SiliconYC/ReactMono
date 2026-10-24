# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/menus.cpp::OptionsScreen；未支持功能保留原灰态。
# ◑ 导入
from copy import deepcopy

from rich4.native_ui import 原生界面_类
from rich4.options_types import 选项动作_类, 选项状态_类
from rich4.original_text import 原版文字_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类


# ◕ 功能
class 选项屏幕_类:
    """
    原Data3配置、八曲试听、原重开/退出二次确认。

    更新日志：
    2026.10.24 - 仅确认写配置，歌曲标题外部读取；连续音量/投降等仍按源禁用。
    """

    def __init__(self, arg_原文: 原版文字_类) -> None:
        self._原文 = arg_原文
        self._状态 = 选项状态_类()
        self._局内, self._确认 = False, -1

    def api_打开(self, arg_状态: 选项状态_类, arg_局内: bool) -> None:
        self._状态, self._局内, self._确认 = deepcopy(arg_状态), arg_局内, -1

    @staticmethod
    def _框(arg_x: int, arg_y: int, arg_x2: int, arg_y2: int) -> tuple[int, int, int, int]:
        return arg_x + 147, arg_y + 59, arg_x2 + 147, arg_y2 + 59

    def api_绘制(self, arg_宿: 屏幕宿主_类, arg_动: 选项动作_类) -> None:
        框, 绘, 文, at = arg_宿.框, 屏幕绘图_类, 屏幕绘图_类.api_文字, self._框
        state = self._状态
        框.api_资源图("d", 3, 0, 147, 59)
        框.api_资源图("d", 3, 11 if self._局内 else 10, 315, 61)
        label = 屏幕字样_类(15, 0x101010, 0, 2)
        for s, y in (
            ("遊戲速度", 25),
            ("動畫過程", 58),
            ("音 樂", 90),
            ("音 效", 122),
            ("自動存檔", 155),
        ):
            文(框, s, 161, 59 + y, 5, label)
        for s, x, y in (
            ("樂  曲", 49, 202),
            ("視  窗", 209, 202),
            ("日、月曆", 286, 226),
            ("縮小地圖", 286, 258),
            ("組合畫面", 286, 290),
        ):
            文(框, s, 147 + x, 59 + y, 2, label)
        文(框, "取 消", 371, 387, 2, 屏幕字样_类(20, 0x101010, 0, 2))
        文(框, "確 定", 443, 387, 2, 屏幕字样_类(20, 0x101010, 0, 2))
        big = (
            ("重新遊戲", "認輸投降", "結束遊戲")
            if self._局内
            else ("日期更改", "熱鍵設定", "遊戲說明")
        )
        bigrects = (at(227, 14, 327, 49), at(227, 68, 327, 103), at(227, 119, 327, 154))
        for i, r in enumerate(bigrects):
            enabled = i != 1 if self._局内 else i == 2 and arg_动.说明 is not None
            文(
                框,
                big[i],
                (r[0] + r[2]) // 2,
                (r[1] + r[3]) // 2,
                2,
                屏幕字样_类(16, 0x101010 if enabled else 0x8A8070, 0, 2),
            )
            if enabled and 框.按下 and 框.api_指针内(r) and self._确认 < 0:
                框.api_资源图("d", 3, 6, r[0], r[1])
        speed = 2 if state.速度 >= 4 else 1 if state.速度 >= 2 else 0
        for i in range(speed + 1):
            框.api_资源图("d", 3, 5, 228 + 16 * i, 76)
        for i in range(4):
            if state.音乐:
                框.api_资源图("d", 3, 5, 236 + 16 * i, 140)
            if state.音效:
                框.api_资源图("d", 3, 5, 236 + 16 * i, 172)
        if state.音乐:
            框.api_资源图("d", 3, 9, 213, 141)
        if state.音效:
            框.api_资源图("d", 3, 9, 213, 173)
        if state.动画:
            框.api_资源图("d", 3, 9, 245, 109)
        框.api_资源图("d", 3, 9, 245, 205)
        for i in range(8):
            if arg_动.正播放 == i + 1 and state.音乐:
                原生界面_类.api_填充(
                    框.画布, at(18, 226 + 15 * i, 177, 240 + 15 * i), 绘.api_RGB(0xFF0000)
                )
            文(框, self._原文.api_歌曲(i), 173, 292 + 15 * i, 5, 屏幕字样_类(12))
        if 框.按下 and self._确认 < 0:
            for r, frame in ((at(194, 314, 256, 344), 3), (at(266, 314, 328, 344), 4)):
                if 框.api_指针内(r):
                    框.api_资源图("d", 3, frame, r[0], r[1])
        if self._确认 >= 0:
            绘.api_弹框(
                arg_宿, "確定要重新遊戲嗎？" if self._确认 == 0 else "確定要結束遊戲嗎？", 186
            )
            for x, s in ((250, "是"), (334, "否")):
                框.api_资源图("d", 3, 14, x, 240)
                文(框, s, x + 28, 255, 2, 绘.白字)

            def 是() -> None:
                which, self._确认 = self._确认, -1
                if which == 0 and arg_动.重开:
                    arg_动.重开()
                elif which == 2 and arg_动.退出:
                    arg_动.退出()

            def 否() -> None:
                self._确认 = -1

            绘.api_命中(arg_宿, 58, (250, 240, 306, 271), 1, 是)
            绘.api_命中(arg_宿, 59, (0, 0, 640, 480), 4, 否)
            return

        def 速度() -> None:
            index = min(max((框.指针x - 228) // 16, 0), 2)
            state.速度 = 1 << index

        def 开音乐() -> None:
            state.音乐 = True

        def 开音效() -> None:
            state.音效 = True

        def 音乐() -> None:
            state.音乐 = not state.音乐

        def 音效() -> None:
            state.音效 = not state.音效

        def 动画() -> None:
            state.动画 = not state.动画

        def 歌曲() -> None:
            index = min(max((框.指针y - 285) // 15, 0), 7)
            if arg_动.试曲:
                arg_动.试曲(index + 1)

        for id, r, action in (
            (50, at(81, 9, 135, 41), 速度),
            (47, at(89, 74, 160, 105), 开音乐),
            (48, at(89, 106, 160, 137), 开音效),
            (53, at(4, 74, 89, 105), 音乐),
            (54, at(4, 106, 89, 137), 音效),
            (63, at(4, 42, 160, 73), 动画),
            (56, at(18, 226, 177, 346), 歌曲),
        ):
            绘.api_命中(arg_宿, id, r, 1, action)
        for i, id in enumerate((57, 61, 62)):

            def 大键(arg_i: int = i) -> None:
                if self._局内:
                    self._确认 = arg_i
                elif arg_动.说明:
                    arg_动.说明()

            绘.api_命中(
                arg_宿,
                id,
                bigrects[i],
                1,
                大键,
                i != 1 if self._局内 else i == 2 and arg_动.说明 is not None,
            )

        def 确定() -> None:
            arg_动.应用(state)
            arg_动.关闭()

        绘.api_命中(arg_宿, 52, at(190, 308, 261, 352), 2, arg_动.关闭)
        绘.api_命中(arg_宿, 55, at(262, 308, 336, 352), 1, 确定)
        绘.api_命中(arg_宿, 0, at(0, 0, 347, 363), -1, lambda: None)
        绘.api_命中(arg_宿, 51, (0, 0, 640, 480), 4, arg_动.关闭)
