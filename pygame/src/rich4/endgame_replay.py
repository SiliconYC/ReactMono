# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/endgame.cpp::draw_play_again。
# ◑ 导入
from rich4.endgame_types import 再玩步骤_类, 结局动作_类, 结局种类_类
from rich4.flc import 动画_类
from rich4.screen_draw import 屏幕宿主_类, 屏幕绘图_类


# ◕ 功能
class 再玩屏幕_类:
    """
    原再玩倒数、同意台词等待和Data556倒闭影片。

    更新日志：
    2026.10.24 - 原即时重放可跳电影；正式模式保持输入阻塞和声音101。
    """

    def _画再玩(
        self,
        arg_宿: 屏幕宿主_类,
        arg_已过: int,
        arg_等待: bool,
        arg_动作: 结局动作_类,
    ) -> None:
        f = arg_宿.框
        if self._步骤 == 再玩步骤_类.倒数:
            if not self._已开始:
                if arg_等待:
                    return
                self._已开始, arg_已过 = True, 0
            self._倒数毫秒 = (self._倒数毫秒 + arg_已过) & 0xFFFFFFFF
            counter = 10 - self._倒数毫秒 // 1000
            if counter <= 0:
                self._步骤, self._种类 = 再玩步骤_类.完成, 结局种类_类.无
                if arg_动作.再玩完成:
                    arg_动作.再玩完成(False)
                return
            f.画布.api_绘制(f.美术.api_帧("p", 112, 0), 320, 120)
            f.画布.api_绘制(f.美术.api_帧("p", 112, counter), 320, 350)

            def 同意() -> None:
                self._步骤 = 再玩步骤_类.台词
                if arg_动作.同意:
                    arg_动作.同意()

            屏幕绘图_类.api_命中(arg_宿, 1100, (0, 0, 640, 480), -1, 同意)
            return
        if self._步骤 == 再玩步骤_类.台词:
            if arg_等待:
                return
            self._步骤, self._电影毫秒 = 再玩步骤_类.电影, 0
            if not arg_宿.即时:
                try:
                    self._电影 = 动画_类(f.美术.api_解码("d", 556))
                    if self._电影.api_下一帧():
                        self._电影帧 = self._电影.api_图像()
                    else:
                        self._电影 = None
                except (ValueError, IndexError, OSError):
                    # 原倒闭影片不可解时完成原返回路径，不提供替代影片。
                    self._电影 = None
                if self._电影 is not None:
                    arg_宿.声音(101)
        if self._步骤 == 再玩步骤_类.电影:
            if self._电影 is not None:
                self._电影毫秒 = (self._电影毫秒 + arg_已过) & 0xFFFFFFFF
                delay = max(1, self._电影.间隔毫秒)
                while self._电影 is not None and self._电影毫秒 >= delay:
                    self._电影毫秒 -= delay
                    if self._电影.api_下一帧():
                        self._电影帧 = self._电影.api_图像()
                    else:
                        self._电影 = None
            if self._电影 is not None:
                f.画布.api_绘制(self._电影帧, 0, 40)
                f.按钮.clear()
                return
            self._步骤, self._种类 = 再玩步骤_类.完成, 结局种类_类.无
            if arg_动作.再玩完成:
                arg_动作.再玩完成(True)
