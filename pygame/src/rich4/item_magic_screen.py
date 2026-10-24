# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定items.cpp魔法屋/Panel20电影；施法只回答实际规则选项。
# ◑ 导入
import logging

from rich4.flc import 动画_类
from rich4.game import 游戏会话_类
from rich4.game_types import 决策_类, 决策种类_类
from rich4.item_paint import 物品绘图_类
from rich4.item_screen_types import 物品宿主_类
from rich4.item_service_types import 施法电影_类, 电脑施法_类, 魔法屏幕状态_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类
from rich4.original_text import 原版文字_类


# ◕ 功能
class 魔法屏幕_类:
    """
    原十二类别/效果、掩码点击、人类与电脑施法、渐进电影和延迟回应。

    更新日志：
    2026.10.24 - 显式保留原casting=1哨兵分支，真实差分确认后记录边界。
    """

    效果 = (
        ("變賣所有卡片", 9, 208, 167, 322, 91),
        ("抽取命運三張", 10, 510, 150, 414, 82),
        ("立刻坐牢三天", 7, 545, 88, 453, 157),
        ("原地停留一回合", 7, 568, 147, 509, 242),
        ("存入所有現金", 7, 550, 234, 458, 314),
        ("就地加蓋房屋", 7, 510, 320, 415, 387),
        ("得一張卡片", 7, 422, 320, 322, 394),
        ("向後轉", 6, 134, 318, 239, 393),
        ("變賣所有道具", 6, 92, 250, 188, 316),
        ("就地拆除房屋", 6, 72, 130, 131, 222),
        ("住院檢查三天", 6, 77, 85, 184, 161),
        ("拍賣當格土地", 9, 122, 154, 225, 83),
    )
    _魔法: 魔法屏幕状态_类
    _施法: 电脑施法_类 | None
    _原文: 原版文字_类 | None

    def _魔法台词(self, arg_号: int) -> str:
        if self._原文 is None:
            raise ValueError("魔法屏幕需要外部原版台词")
        return self._原文.api_配音(arg_号).文字

    def _魔法组(self, arg_号: int) -> str:
        return self._魔法台词(46 + arg_号)

    def api_画魔法(
        self,
        arg_框: 画框_类,
        arg_会: 游戏会话_类,
        arg_决: 决策_类,
        arg_宿: 物品宿主_类,
    ) -> None:
        now, 绘, 界 = self._现在(arg_框), 物品绘图_类, 原生界面_类
        if not self._魔法.活跃:
            self._魔法 = 魔法屏幕状态_类(活跃=True, 打开=now)
        if not self._魔法罩:
            try:
                self._魔法罩 = arg_框.美术.api_解码("p", 19)
            except (ValueError, OSError, IndexError):
                pass
        绘.api_图(arg_框, "p", 18, 0, 0, 0, True)

        def 气泡(arg_文: str) -> None:
            绘.api_图(arg_框, "p", 18, 8, 320, 384)
            绘.api_中(arg_框, arg_文, 320, 384, 18, 界.api_颜色(250, 240, 210))

        if arg_决.种类 == 决策种类_类.魔法类别:
            self.截图名 = "magic-category"
            self._只说一次("magic-category", (37,))
            绘.api_图(arg_框, "p", 18, 1, 241, 140)
            panel = 18, 300, 622, 474
            界.api_填充(arg_框.画布, panel, 界.api_颜色(74, 34, 12))
            界.api_边框(arg_框.画布, panel, 界.api_颜色(232, 196, 96))
            界.api_边框(arg_框.画布, (21, 303, 619, 471), 界.api_颜色(150, 96, 40))
            line = self._魔法台词(37).replace("\n", "") + "請選出施法的對象："
            绘.api_中(arg_框, line, 320, 318, 16, 界.api_颜色(250, 240, 210))
            for group in range(12):
                x, y = 68 + group % 6 * 100, 366 + group // 6 * 70
                cell = x - 48, y - 34, x + 48, y + 34
                index = self._选项(arg_决, group)
                绘.api_图(arg_框, "p", 18, 11 + group, x, y - 10)
                绘.api_中(
                    arg_框,
                    self._魔法组(group),
                    x,
                    y + 25,
                    13,
                    界.api_颜色(250, 240, 210) if index is not None else 界.api_颜色(120, 100, 80),
                )
                if index is None:
                    for yy in range(cell[1], cell[3]):
                        for xx in range(cell[0], cell[2]):
                            pos = yy * arg_框.画布.宽 + xx
                            arg_框.画布.像素[pos] = (arg_框.画布.像素[pos] >> 1) & 0x3DEF
                    continue
                if arg_框.按下 and arg_框.api_指针内(cell):
                    绘.api_下沉(arg_框.画布, cell)

                def 选组(arg_g: int = group, arg_i: int = index) -> None:
                    self._魔法.类别 = arg_g
                    arg_宿.回答(arg_i)

                arg_框.api_命中(210 + index, cell, 选组)
            return
        group = self._魔法.类别

        def 回答效果(arg_值: int) -> None:
            index = self._选项(arg_决, arg_值)
            if index is not None:
                self._魔法 = 魔法屏幕状态_类()
                arg_宿.回答(index)

        def 安排效果(arg_值: int) -> None:
            index = self._选项(arg_决, arg_值)
            if index is not None and not self._魔法.已安排:
                self._魔法.已安排 = True

                def 执行() -> None:
                    self._魔法 = 魔法屏幕状态_类()
                    arg_宿.回答(index)

                self._延迟.append(执行)

        self.截图名 = (
            "magic-casting"
            if self._魔法.施法时
            else "magic-selected"
            if self._魔法.选中 >= 0
            else "magic-effect"
        )
        if self._魔法.施法时:
            effect = self._魔法.选中
            if self._魔法.施法时 > 1 and now >= ((self._魔法.施法时 + 1000) & 0xFFFFFFFFFFFFFFFF):
                self.截图名 = "magic-movie"
                playing, self._魔法.电影 = self._画施法电影(
                    arg_框, self._魔法.电影, (now - self._魔法.施法时 - 1000) & 0xFFFFFFFFFFFFFFFF
                )
                if not playing:
                    安排效果(effect)
            else:
                绘.api_图(arg_框, "p", 18, 2, 182, 142)
                if 0 <= group < 12:
                    绘.api_图(arg_框, "p", 18, 11 + group, 326, 296)
                气泡(self._魔法台词(41))
                self._只说一次("magic-cast", (41,))
            index = self._选项(arg_决, effect)
            if index is not None:
                arg_框.api_命中(210 + index, (0, 0, 640, 480), lambda: 回答效果(effect))
            return
        绘.api_图(arg_框, "p", 18, 1, 241, 140)
        if 0 <= group < 12:
            绘.api_图(arg_框, "p", 18, 11 + group, 326, 296)
            self._只说一次("magic-effect" + str(group), (46 + group, 40))

        def 选择(arg_值: int) -> None:
            if not 0 <= arg_值 <= 11:
                return
            if self._魔法.选中 == arg_值:
                self._魔法.施法时 = 1
                return
            self._魔法.选中 = arg_值
            if self.声音:
                self.声音(39)

        def 提示(arg_文: str) -> None:
            rect = 150, 444, 490, 476
            界.api_填充(arg_框.画布, rect, 界.api_颜色(74, 34, 12))
            界.api_边框(arg_框.画布, rect, 界.api_颜色(232, 196, 96))
            绘.api_中(arg_框, arg_文, 320, 460, 16, 界.api_颜色(250, 240, 210))

        if self._魔法.选中 >= 0:
            effect = self._魔法.选中
            text, plate, lx, ly, ix, iy = self.效果[effect]
            绘.api_图(arg_框, "p", 18, 23 + effect, ix, iy)
            绘.api_图(arg_框, "p", 18, plate, lx, ly)
            绘.api_中(
                arg_框, text, lx, ly, 14, 界.api_颜色(224, 224, 224), True, 界.api_颜色(32, 32, 32)
            )
            提示(text + "？再點一次就施法")
        else:
            提示(
                (self._魔法组(group) if 0 <= group < 12 else "")
                + "："
                + self._魔法台词(40)
                + "請點選魔法"
            )
        for i, o in enumerate(arg_决.选项):
            if not 0 <= o.值 <= 11:
                continue
            x, y = self.效果[o.值][4:]
            arg_框.api_命中(210 + i, (x - 24, y - 24, x + 24, y + 24), lambda v=o.值: 选择(v))
        reselect = self._选项(arg_决, -1)
        if reselect is not None:
            arg_框.api_按钮(
                210 + reselect, (520, 440, 630, 472), "重選對象", lambda: arg_宿.回答(reselect)
            )

        def 掩码选择() -> None:
            x, y = arg_框.指针x, arg_框.指针y
            if not 0 <= x < 640 or not 0 <= y < 480 or len(self._魔法罩) < 307200:
                return
            value = self._魔法罩[y * 640 + x]
            if 1 <= value <= 12:
                选择(value - 1)
            elif value == 13:
                self._魔法.选中 = -1

        arg_框.api_命中(299, (0, 0, 640, 480), 掩码选择)
        if self._魔法.施法时 == 1:
            self._魔法.施法时 = now

    def _画施法电影(
        self,
        arg_框: 画框_类,
        arg_态: 施法电影_类 | None,
        arg_经过: int,
    ) -> tuple[bool, 施法电影_类 | None]:
        try:
            if arg_态 is None:
                arg_态 = 施法电影_类(动画_类(arg_框.美术.api_解码("p", 20)))
            movie = arg_态.解码
            delay, count = max(movie.间隔毫秒, 1), max(movie.帧数, 1)
            index = min(arg_经过 // delay, count - 1)
            while movie.已解帧 <= index and movie.api_下一帧():
                arg_态.图像 = movie.api_图像()
            if not arg_态.已响:
                arg_态.已响 = True
                if self.声音:
                    self.声音(59)
            if arg_态.图像.像素:
                arg_框.画布.api_绘制(arg_态.图像, 0, 0, arg_强制不透明=True)
            return arg_经过 < delay * count, arg_态
        except (ValueError, IndexError, OSError) as error:
            logging.getLogger(__name__).warning("魔法电影按原跳过：%s", error)
            return False, arg_态

    def api_开始电脑施法(self, arg_组: int, arg_效果: int) -> None:
        if 0 <= arg_组 < 12 and 0 <= arg_效果 < 12:
            self._施法 = 电脑施法_类(arg_组, arg_效果)

    def api_电脑施法中(self) -> bool:
        return self._施法 is not None

    def api_画电脑施法(self, arg_框: 画框_类) -> None:
        if self._施法 is None:
            return
        now, state, 绘, 界 = self._现在(arg_框), self._施法, 物品绘图_类, 原生界面_类
        if not state.开始:
            state.开始 = max(now, 1)
        elapsed = (now - state.开始) & 0xFFFFFFFFFFFFFFFF
        self.截图名 = "magic-computer"
        playing = True
        if elapsed < 1500:
            绘.api_图(arg_框, "p", 18, 0, 0, 0, True)
            绘.api_图(arg_框, "p", 18, 2, 182, 142)
            绘.api_图(arg_框, "p", 18, 11 + state.类别, 326, 296)
            绘.api_图(arg_框, "p", 18, 8, 320, 384)
            text = self._魔法组(state.类别) + "\n\n" + self.效果[state.效果][0]
            绘.api_中(arg_框, text, 320, 384, 18, 界.api_颜色(250, 240, 210))
        else:
            self.截图名 = "magic-computer-movie"
            playing, state.电影 = self._画施法电影(arg_框, state.电影, elapsed - 1500)

        def 跳过() -> None:
            self._施法 = None

        arg_框.api_命中(1660, (0, 0, 640, 480), 跳过)
        if not playing:
            self._施法 = None
