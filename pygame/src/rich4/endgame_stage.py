# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/endgame.cpp::stage_tick/draw_stage_clear。
# ◑ 导入
from copy import deepcopy

from rich4.endgame_types import 结局动作_类, 结局种类_类
from rich4.screen_draw import 屏幕字样_类, 屏幕宿主_类, 屏幕绘图_类


# ◕ 功能
class 过关屏幕_类:
    """
    原50毫秒追逐/地图面板落下/未清地图续关，不自行更改游戏或存档。

    更新日志：
    2026.10.24 - std::minstd_rand独立表现状态；板块星号/勾选只改各自图片副本。
    """

    财神帧 = ((0, 1, 2, 3, 5, 6), (12, 13, 14, 15, 17, 18))

    def _过关步(self) -> None:
        self._滚动 += 2
        if self._滚动 >= 640:
            self._滚动 = 0
        if self._跑y == 0:
            self._随机状态 = self._随机状态 * 48271 % 2147483647
            self._跑y = self._随机状态 % 360 + 100
            self._向左 = not self._向左
            self._跑x = 740 if self._向左 else -100
        elif not self._向左:
            self._跑x += 10
            if self._跑x >= 740:
                self._跑y = 0
        else:
            self._跑x -= 10
            if self._跑x <= -100:
                self._跑y = 0
        self._胜者帧 = (self._胜者帧 + 1) & 0xFFFFFFFF
        self._财神帧 = (self._财神帧 + 1) % 6
        if self._面板y < 360:
            self._面板y += self._面板速
            self._面板速 -= 1
            if self._面板y > 360:
                self._面板y = 360
        if self._已选 >= 0 and self._选余步:
            self._选余步 -= 1
            if not self._选余步:
                self._离开 = True

    def _画过关(
        self,
        arg_宿: 屏幕宿主_类,
        arg_已过: int,
        arg_等待: bool,
        arg_动作: 结局动作_类,
    ) -> None:
        f, info = arg_宿.框, self._资料
        art = f.美术
        if not self._已开始:
            if arg_等待:
                return
            self._已开始, arg_已过 = True, 0
            self._底图 = art.api_原图("j", info.阶段 * 4 + info.地图, 640, 480)
            self._面板 = deepcopy(art.api_帧("j", 8, 20 if info.阶段 else 15))
            for m in range(4):
                self._图牌[m] = deepcopy(art.api_帧("j", 8, (16 if info.阶段 else 11) + m))
                if info.已清 & (1 << m):
                    self._图牌[m].api_绘制(art.api_帧("j", 8, 10), 32, 22)
                    self._面板.api_绘制(art.api_帧("j", 8, 10), 220, 28 + 40 * m)
        self._步毫秒 = (self._步毫秒 + arg_已过) & 0xFFFFFFFF
        if arg_宿.即时:
            self._面板y = 360
        while self._步毫秒 >= 50:
            self._步毫秒 -= 50
            self._过关步()
        if self._已选 >= 0 and (self._离开 or arg_宿.即时):
            self._种类 = 结局种类_类.无
            if arg_动作.下一图:
                arg_动作.下一图(self._已选)
            return
        f.画布.api_绘制(self._底图, -self._滚动, 0, arg_强制不透明=True)
        f.画布.api_绘制(self._底图, 640 - self._滚动, 0, arg_强制不透明=True)
        if self._跑y:
            entry = 100 + info.角色
            count = art.api_帧数("p", entry)
            steps = (count - 4) // 2 if count > 4 else 1
            self._胜者帧 %= steps
            frame = min((0 if self._向左 else steps) + self._胜者帧 + 5, count - 1 if count else 0)
            f.画布.api_绘制(
                art.api_帧("p", entry, frame), self._跑x + (90 if self._向左 else -90), self._跑y
            )
            f.画布.api_绘制(
                art.api_帧("p", 93, self.财神帧[int(self._向左)][self._财神帧]),
                self._跑x + (-90 if self._向左 else 90),
                self._跑y,
            )
        panel = info.单人 and info.已清 != 15
        if not panel:
            屏幕绘图_类.api_文字(
                f, "恭喜勝利過關！！", 320, 240, 2, 屏幕字样_类(48, 0xF0F0F0, 0x101010, 3)
            )

            def 返回() -> None:
                self._种类 = 结局种类_类.无
                if arg_动作.主菜单:
                    arg_动作.主菜单()

            屏幕绘图_类.api_命中(arg_宿, 1105, (0, 0, 640, 480), 2, 返回)
            return
        f.画布.api_绘制(self._面板, 320, self._面板y)
        if self._面板y < 360:
            return
        if self._已选 >= 0:
            f.画布.api_绘制(self._图牌[self._已选], 320, 300 + 40 * self._已选)
            f.按钮.clear()
            return
        for m in range(4):
            rect, cleared = (192, 280 + 40 * m, 448, 320 + 40 * m), bool(info.已清 & (1 << m))
            if not cleared and f.api_指针内(rect):
                f.画布.api_绘制(self._图牌[m], 320, 300 + 40 * m)

            def 选择(arg_m: int = m) -> None:
                self._已选, self._选余步 = arg_m, 10
                self._图牌[arg_m].api_绘制(art.api_帧("j", 8, 8), 214, 8)

            屏幕绘图_类.api_命中(arg_宿, 1101 + m, rect, 2, 选择, not cleared)
