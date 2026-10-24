# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/endgame.cpp；正式规则/存档/续图由主应用宿主处理。
# ◑ 导入
from copy import deepcopy

from rich4.endgame_replay import 再玩屏幕_类
from rich4.endgame_stage import 过关屏幕_类
from rich4.endgame_types import 再玩步骤_类, 结局动作_类, 结局种类_类, 过关资料_类
from rich4.flc import 动画_类
from rich4.graphics import 图像_类
from rich4.screen_draw import 屏幕宿主_类


# ◕ 功能
class 结局屏幕_类(再玩屏幕_类, 过关屏幕_类):
    """
    原EndgameScreen生命周期与单调时间推进；last_ticks按参考跨关闭保留。

    更新日志：
    2026.10.24 - 倒退或零时钟不推进、正常最多100毫秒，等待气泡保留原分支语义。
    """

    def __init__(self) -> None:
        self._上时 = 0
        self._步骤 = 再玩步骤_类.倒数
        self._电影帧 = 图像_类(0, 0, [])
        self._资料, self._随机状态 = 过关资料_类(), 1
        self._图牌 = [图像_类(0, 0, []) for _ in range(4)]
        self.api_关闭()

    def api_再玩(self) -> None:
        self.api_关闭()
        self._种类, self._步骤 = 结局种类_类.再玩, 再玩步骤_类.倒数

    def api_过关(self, arg_资料: 过关资料_类) -> None:
        self.api_关闭()
        self._种类, self._资料 = 结局种类_类.过关, deepcopy(arg_资料)
        self._随机状态 = (arg_资料.种子 or 1) % 2147483647 or 1

    def api_关闭(self) -> None:
        self._种类, self._已开始 = 结局种类_类.无, False
        self._倒数毫秒 = self._电影毫秒 = self._步毫秒 = 0
        self._电影: 动画_类 | None = None
        self._滚动 = self._跑x = self._跑y = 0
        self._向左 = False
        self._胜者帧 = self._财神帧 = 0
        self._面板y, self._面板速 = -80, 30
        self._已选, self._选余步, self._离开 = -1, 0, False
        self._底图: 图像_类 | None = None
        self._面板: 图像_类 | None = None

    def api_种类(self) -> 结局种类_类:
        return self._种类

    def api_活跃(self) -> bool:
        return self._种类 != 结局种类_类.无

    def api_退出按钮(self) -> int:
        if self._种类 == 结局种类_类.再玩:
            return 1100 if self._步骤 == 再玩步骤_类.倒数 else -1
        if self._种类 != 结局种类_类.过关 or not self._已开始 or self._已选 >= 0:
            return -1
        if not (self._资料.单人 and self._资料.已清 != 15):
            return 1105
        if self._面板y >= 360:
            for m in range(4):
                if not self._资料.已清 & (1 << m):
                    return 1101 + m
        return -1

    def api_绘制(self, arg_宿: 屏幕宿主_类, arg_等待: bool, arg_动作: 结局动作_类) -> None:
        if not self.api_活跃():
            return
        now = arg_宿.框.时钟
        elapsed = min(now - self._上时, 100) if self._上时 and now > self._上时 else 0
        self._上时 = now
        if self._种类 == 结局种类_类.再玩:
            self._画再玩(arg_宿, elapsed, arg_等待, arg_动作)
        else:
            self._画过关(arg_宿, elapsed, arg_等待, arg_动作)
