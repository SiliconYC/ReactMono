# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/monthly.cpp的lottery_tick/draw_lottery。
# ◑ 导入
from rich4.graphics import 图像_类
from rich4.monthly_common import 月报共用_类
from rich4.monthly_tables import 月表_类
from rich4.monthly_types import 月播_类, 月片_类
from rich4.native_frame import 画框_类
from rich4.screen_draw import 屏幕字样_类, 屏幕绘图_类


# ◕ 功能
class 月报开奖_类(月报共用_类):
    """
    原乐透主持人、笼/中奖影片、票面、气泡及脸部装饰状态机。

    更新日志：
    2026.10.24 - 原50ms计时节拍和无中奖/中奖分支，不改变已开奖号码或奖池。
    """

    def _开奖步(self, arg_框: 画框_类, arg_播: 月播_类) -> None:
        p, f = arg_播, arg_播.数据
        if not p.泡.显示:
            if p.状态 == 1:
                p.状态 = 2
                self._说(p, 22, 300, 47, -10, 0, 18)
            elif p.状态 == 2:
                p.状态, p.计数, p.布局 = 3, 1, 1
                p.眼 = p.嘴 = -1
                p.片 = 月片_类(解码=self._开片(arg_框, "p", 16), x=183, y=75, 叠加=False)
                if self.声音.播放:
                    self.声音.播放(57)
            elif p.状态 == 3:
                p.计数 = self._有号32(p.计数 + 1)
                if p.计数 == 20:
                    p.布局, p.眼, p.嘴 = 2, -1, -1
                if p.计数 >= 20:
                    if p.片.解码 is not None and p.片.解码.api_下一帧():
                        p.片.静帧 = p.片.解码.api_图像()
                    else:
                        p.球 = p.绿 = True
                        if 1 <= f.号码 <= 36 and f.票[f.号码 - 1] and f.赢家 >= 0:
                            p.状态 = 4
                            self._说(p, 22, 300, 47, -10, 0, 19)
                        else:
                            p.状态, p.计数 = 70, 0
            elif p.状态 == 70:
                p.计数 = self._有号32(p.计数 + 1)
                if p.计数 * 50 >= 500:
                    p.状态, p.布局 = 7, 4
                    p.眼 = p.嘴 = p.左 = -1
                    self._说(p, 23, 320, 200, 0, 0, 33)
            elif p.状态 == 4:
                p.状态, p.计数, p.布局, p.名牌 = 5, 1, 3, True
                p.眼 = p.嘴 = p.左 = -1
                p.次片 = 月片_类(解码=self._开片(arg_框, "p", 17), x=205, y=0)
                if self.声音.播放:
                    self.声音.播放(58)
                if self.声音.语音 and f.赢家 >= 0:
                    self.声音.语音(20 + self._角色(f, f.赢家))
            elif p.状态 == 5:
                p.计数 = self._有号32(p.计数 + 1)
                if p.计数 >= 31:
                    if p.次片.解码 is not None and p.次片.解码.api_下一帧():
                        p.次片.静帧 = p.次片.解码.api_图像()
                    else:
                        p.次片 = 月片_类()
                        p.片.静帧 = 图像_类(0, 0, [])
                        p.名牌 = p.绿 = False
                        p.状态 = 6
                        self._说(p, 22, 300, 47, -10, 0, 32)
            elif p.状态 == 6:
                p.布局, p.状态 = 0, 8
            elif p.状态 == 7:
                p.状态 = 8
                self._说(p, 23, 320, 200, 0, 0, 34)
            elif p.状态 == 8:
                p.布局, p.状态 = 0, 9
                p.眼 = p.嘴 = p.左 = -1
                self._说(p, 22, 300, 47, -10, 0, 35)
            elif p.状态 == 9:
                p.状态 = 10
                self._说(p, 22, 300, 47, -10, 0, 36)
            elif p.状态 == 10:
                p.关闭 = True
        if not (p.状态 <= 3 or p.状态 in (9, 10)):
            return
        if p.眨眼 >= 0:
            右, 左 = (8, 7, 8, 10), (16, 17, 16, 15)
            if p.眨眼 == 1:
                p.眼 = 右[p.眨步]
            else:
                p.左 = 左[p.眨步]
            p.眨步 += 1
            if p.眨步 == 4:
                p.眨眼 = -1
        else:
            r = self._装饰(p) >> 9
            if r in (0, 1):
                p.眨眼, p.眨步 = (1 if r == 0 else 2), 0
            elif r <= 3:
                p.眼 = 9 + (self._装饰(p) & 1)
            elif r <= 5:
                p.左 = 14 + (self._装饰(p) & 1)
        if p.泡.显示:
            if p.嘴时 > 0:
                p.嘴时 -= 1
                if p.嘴时 == 0:
                    p.嘴 = 11
            elif self._装饰(p) >> 11 < 4:
                p.嘴 = 12 + (self._装饰(p) & 1)
                p.嘴时 = 1 + self._装饰(p) % 15
        elif p.嘴 >= 0:
            p.嘴 = 11

    def _画开奖(self, arg_框: 画框_类, arg_播: 月播_类, arg_毫秒: int) -> bool:
        p, f = arg_播, arg_播.数据
        if p.点过 and p.泡.显示:
            p.泡.剩余毫秒 = 0
        if p.泡.显示:
            p.泡.剩余毫秒 -= min(p.泡.剩余毫秒, arg_毫秒)
        p.已过 = (p.已过 + arg_毫秒) & 0xFFFFFFFF
        while p.已过 >= p.节拍 and not p.关闭:
            p.已过 -= p.节拍
            if p.泡.显示 and p.泡.剩余毫秒 == 0:
                p.泡.显示 = False
            self._开奖步(arg_框, p)
        if p.关闭:
            return False
        self._贴(arg_框, "p", 15, 0, 0, 0, True)
        画, 美 = arg_框.画布, arg_框.美术
        if p.片.静帧.像素:
            画.api_绘制(p.片.静帧, p.片.x, p.片.y, arg_强制不透明=not p.片.叠加)
        十, 个 = f.号码 // 10, f.号码 % 10
        if p.绿:
            self._贴(arg_框, "d", 517, 8 + 十, 300, 220)
            self._贴(arg_框, "d", 517, 8 + 个, 340, 220)
        背 = 美.api_帧("p", 15, 0)
        if p.布局 == 0:
            self._贴(arg_框, "p", 15, 1, 472, 66)
            self._贴(arg_框, "p", 15, 3, 7, 66)
        elif p.布局 in (1, 2):
            self._贴(arg_框, "p", 15, 2, 418, 66)
            self._贴(arg_框, "p", 15, 3, 7, 66)
            if p.布局 == 2:
                屏幕绘图_类.api_局部(画, 背, (418, 171, 498, 251), 418, 171)
                屏幕绘图_类.api_局部(画, 美.api_帧("p", 15, 1), (0, 51, 38, 141), 472, 117)
        elif p.布局 == 3:
            self._贴(arg_框, "p", 15, 6, 0, 0)
            self._贴(arg_框, "p", 15, 5, 505, 66)
        elif p.布局 == 4:
            self._贴(arg_框, "p", 15, 3, 7, 66)
            self._贴(arg_框, "p", 15, 21, 52, 89, True)
            self._贴(arg_框, "p", 15, 4, 489, 116)
        if p.布局 in (0, 1, 2):
            for 帧, x, y in ((p.眼, 512, 102), (p.嘴, 512, 119), (p.左, 52, 89)):
                if 帧 >= 0:
                    self._贴(arg_框, "p", 15, 帧, x, y, True)
        举 = p.布局 == 3
        self._文(
            arg_框,
            "累積獎金",
            91 if 举 else 77,
            19 if 举 else 193,
            2,
            屏幕字样_类(20, 0x4F35B1, 0, 2),
        )
        self._文(
            arg_框,
            "$" + self._钱(f.奖池),
            91 if 举 else 77,
            56 if 举 else 228,
            2,
            屏幕字样_类(20, 0xFF0000, 0, 2),
        )
        if p.球:
            self._贴(arg_框, "p", 15, 37 + 十, 286, 405)
            self._贴(arg_框, "p", 15, 37 + 个, 358, 405)
        for 面, i in enumerate(self._槽(f)):
            px, py = 月表_类.票位[面]
            屏幕绘图_类.api_暗化(画, (px, py, px + 296, py + 60), -16)
            self._贴(arg_框, "p", 15, 25 + self._角色(f, i), px + 20, py + 30)
            号码 = [n + 1 for n, v in enumerate(f.票) if v == i + 1]
            for j, n in enumerate(号码[:12]):
                y = py + 30 if len(号码) <= 6 else py + 15 if j < 6 else py + 45
                x = px + 54 + 40 * (j % 6)
                self._贴(arg_框, "p", 13, n // 10, x, y)
                self._贴(arg_框, "p", 13, n % 10, x + 16, y)
        if p.名牌:
            self._贴(arg_框, "p", 15, 24, 320, 200)
            if f.赢家 >= 0:
                self._文(
                    arg_框,
                    self._姓名(f, f.赢家),
                    320,
                    180,
                    2,
                    屏幕字样_类(28, 0xFF0000, 0x400000, 3),
                )
        if p.次片.静帧.像素:
            画.api_绘制(p.次片.静帧, p.次片.x, p.次片.y)
        self._贴泡(arg_框, p, 15)
        return True
