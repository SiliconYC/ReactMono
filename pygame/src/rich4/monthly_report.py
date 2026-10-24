# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/monthly.cpp的report_tick/draw_report。
# ◑ 导入
from rich4.graphics import 图像_类
from rich4.monthly_common import 月报共用_类
from rich4.monthly_tables import 月表_类
from rich4.monthly_types import 月播_类, 月片_类
from rich4.native_frame import 画框_类
from rich4.screen_draw import 屏幕字样_类


# ◕ 功能
class 月报结算_类(月报共用_类):
    """
    原月底银行报告、悲情/冠军、聚光与十二人物反应影片状态机。

    更新日志：
    2026.10.24 - 仅读取已结算数据，保留点击清泡/跳片/跳下一等待的组合语义。
    """

    @staticmethod
    def _女士姿(arg_播: 月播_类, arg_模式: int) -> None:
        p = arg_播
        p.女士 = arg_模式
        p.眼 = p.嘴 = p.眨眼 = -1
        p.嘴时 = 0

    def _排队(self, arg_播: 月播_类) -> None:
        p = arg_播
        self._女士姿(p, 0)
        p.列队, p.卡片 = True, False
        p.聚光 = p.隐藏 = -1
        p.奖, p.欢颜 = 0, False
        p.片.静帧 = 图像_类(0, 0, [])

    def _反应(self, arg_框: 画框_类, arg_播: 月播_类, arg_槽: int, arg_冠军: bool) -> None:
        p, f = arg_播, arg_播.数据
        c = self._角色(f, arg_槽)
        row = 月表_类.反应[c]
        slots = self._槽(f)
        i = slots.index(arg_槽) if arg_槽 in slots else 0
        n = min(max(len(slots), 2), 4) - 2
        p.片 = 月片_类(解码=self._开片(arg_框, "d", (416 if arg_冠军 else 417) + 2 * c))
        m = p.片
        m.x = 月表_类.排x[n][i] + row[0 if arg_冠军 else 3]
        m.y = 330 + row[1 if arg_冠军 else 4]
        m.次数 = max(1, (row[2 if arg_冠军 else 5] >> 8) & 255)
        m.运行 = m.解码 is not None
        if m.运行 and m.解码.api_下一帧():
            m.静帧 = m.解码.api_图像()

    def _月报步(self, arg_框: 画框_类, arg_播: 月播_类) -> None:
        p, f = arg_播, arg_播.数据
        if not p.泡.显示 and not p.片.运行:
            if p.状态 == 1:
                self._女士姿(p, 1)
                p.状态 = 2
                self._说(p, 1, 190, 10, 0, -30, 93)
            elif p.状态 == 2:
                p.欢颜, p.卡片, p.略等待, p.计数, p.排过 = True, True, False, 0, False
                p.状态 = 15 if f.悲情 < 0 or f.悲情 == f.冠军 else 5
            elif p.状态 in (5, 15):
                p.计数 = self._有号32(p.计数 + 1)
                if p.略等待:
                    p.计数 = max(p.计数, 30)
                if p.计数 >= 20 and not p.排过:
                    self._排队(p)
                    p.排过 = True
                if p.计数 >= 30:
                    p.略等待 = False
                    if p.状态 == 5:
                        self._女士姿(p, 2)
                        p.状态 = 6
                        self._说(p, 1, 190, 10, 0, -30, 95)
                    else:
                        self._女士姿(p, 4)
                        p.状态 = 16
                        self._说(p, 1, 190, 10, 0, -30, 109)
                    if self.声音.播放:
                        self.声音.播放(27)
            elif p.状态 == 6:
                p.聚光 = f.悲情
                self._女士姿(p, 3)
                p.状态 = 7
                self._说(p, 1, 190, 10, 0, -30, 96 + self._角色(f, f.悲情), self._姓名(f, f.悲情))
                if self.声音.播放:
                    self.声音.播放(60)
            elif p.状态 == 7:
                self._女士姿(p, 2)
                p.奖, p.隐藏, p.状态 = 1, f.悲情, 8
                self._反应(arg_框, p, f.悲情, False)
            elif p.状态 == 8:
                self._女士姿(p, 4)
                p.状态 = 9
            elif p.状态 == 9:
                p.状态, p.计数, p.排过 = 15, 19, False
                self._说(p, 3, 190, 10, 20, 0, 108)
            elif p.状态 == 16:
                p.聚光 = f.冠军
                self._女士姿(p, 5)
                p.状态 = 17
                self._说(p, 1, 190, 10, 0, -30, 110 + self._角色(f, f.冠军), self._姓名(f, f.冠军))
                if self.声音.播放:
                    self.声音.播放(28)
            elif p.状态 == 17:
                p.女士, p.奖, p.隐藏, p.状态 = -1, 2, f.冠军, 18
                self._反应(arg_框, p, f.冠军, True)
            elif p.状态 == 18:
                self._女士姿(p, 6)
                p.状态 = 19
            elif p.状态 == 19:
                p.状态, p.计数 = 22, 10
                self._说(p, 4, 213, 37, 20, 0, 122)
            elif p.状态 == 22:
                p.计数 = self._有号32(p.计数 - 1)
                if p.计数 <= 0 or p.略等待:
                    p.关闭 = True
        if p.女士 < 0:
            return
        pose = 月表_类.女士[p.女士]
        if p.眨眼 >= 0:
            if p.眨步 < 3:
                p.眼 = pose.眼帧[p.眨步]
                p.眨步 += 1
            else:
                p.眼, p.眨眼 = (25 if p.女士 == 1 else -1), -1
        else:
            r = self._装饰(p) >> 10
            if r == 0 and pose.眼帧[0] >= 0:
                p.眨眼, p.眨步 = 1, 0
            elif r == 1 and p.女士 == 1:
                p.眼 = 25 + (self._装饰(p) & 1)
        if pose.嘴开 < 0:
            return
        if p.嘴时 > 0:
            p.嘴时 -= 1
            if p.嘴时 == 0:
                p.嘴 = pose.嘴停
        elif p.泡.显示 and self._装饰(p) & 3 == 0:
            p.嘴 = -1 if p.女士 == 0 and self._装饰(p) & 1 else pose.嘴开
            p.嘴时 = 1 + (self._装饰(p) & 7)

    def _画月报(self, arg_框: 画框_类, arg_播: 月播_类, arg_毫秒: int) -> bool:
        p, f, m = arg_播, arg_播.数据, arg_播.片
        if p.点过:
            if p.泡.显示:
                p.泡.显示 = False
            if m.运行:
                m.运行, m.解码 = False, None
            p.略等待 = True
        if p.泡.显示:
            p.泡.剩余毫秒 -= min(p.泡.剩余毫秒, arg_毫秒)
        if m.运行:
            m.已过 = (m.已过 + arg_毫秒) & 0xFFFFFFFF
            delay = max(20, m.解码.间隔毫秒)
            while m.运行 and m.已过 >= delay:
                m.已过 -= delay
                if m.解码.api_下一帧():
                    m.静帧 = m.解码.api_图像()
                else:
                    m.次数 = (m.次数 - 1) & 0xFFFFFFFF
                    if m.次数 > 0:
                        m.解码.api_倒带()
                        if m.解码.api_下一帧():
                            m.静帧 = m.解码.api_图像()
                    else:
                        m.运行 = False
        p.已过 = (p.已过 + arg_毫秒) & 0xFFFFFFFF
        while p.已过 >= p.节拍 and not p.关闭:
            p.已过 -= p.节拍
            if p.泡.显示 and p.泡.剩余毫秒 == 0:
                p.泡.显示 = False
            self._月报步(arg_框, p)
        if p.关闭:
            return False
        slots = self._槽(f)
        n = min(max(len(slots), 2), 4) - 2
        self._贴(arg_框, "p", 25, 0, 0, 0, True)
        for i, slot in enumerate(slots):
            if slot == p.聚光:
                self._贴(arg_框, "p", 25, 月表_类.光帧[n][i], 月表_类.光x[n][i], 0, True)
        if p.女士 >= 0:
            pose = 月表_类.女士[p.女士]
            self._贴(arg_框, "p", 25, pose.帧, pose.x, pose.y)
            if p.眼 >= 0:
                self._贴(arg_框, "p", 25, p.眼, pose.眼x, pose.眼y)
            if p.嘴 >= 0:
                self._贴(arg_框, "p", 25, p.嘴, pose.嘴x, pose.嘴y)
        card, loan = 屏幕字样_类(18, 0x101010, 0, 2), 屏幕字样_类(18, 0xFF0000, 0, 2)
        for i, slot in enumerate(slots):
            figure = 3 * self._角色(f, slot) + (49 if p.欢颜 and not p.列队 else 47)
            if p.列队:
                if slot == p.隐藏:
                    continue
                图 = arg_框.美术.api_帧("p", 25, figure)
                arg_框.画布.api_绘制(图, 月表_类.排x[n][i], 330 - 图.高 + 图.原点y)
                continue
            y = 月表_类.列y[n][i]
            self._贴(arg_框, "p", 25, figure, 600, y)
            if not p.卡片:
                continue
            cx, cy = 360, y - 36
            self._贴(arg_框, "p", 25, 11 + i, cx, cy)
            self._文(arg_框, "存款：", cx + 4, cy + 6, 0, card)
            self._文(arg_框, self._钱(f.存款[slot]), cx + 154, cy + 6, 1, card)
            self._文(arg_框, "利息：", cx + 4, cy + 46, 0, card)
            if (f.贷款 >> slot) & 1:
                self._文(arg_框, "貸款中", cx + 154, cy + 46, 1, loan)
            else:
                self._文(arg_框, self._钱(f.利息[slot]), cx + 154, cy + 46, 1, card)
        if p.奖:
            self._贴(arg_框, "p", 25, 2, 440, 405, True)
            style = 屏幕字样_类(16, 0x101010, 0, 2)
            slot = f.悲情 if p.奖 == 1 else f.冠军
            self._文(arg_框, "獲獎原因：", 320, 370, 0, style)
            if p.奖 == 1:
                self._文(arg_框, "本月意外損失：", 320, 388, 0, style)
                self._文(arg_框, self._钱(self._有号32(f.支出[slot])), 560, 388, 1, style)
                self._文(arg_框, "本月意外之財：", 320, 406, 0, style)
                self._文(arg_框, self._钱(self._有号32(f.收入[slot])), 560, 406, 1, style)
                self._文(arg_框, "本月倒楣天數：", 320, 424, 0, style)
                self._文(arg_框, f"{f.倒霉天[slot]}天", 560, 424, 1, style)
            else:
                self._文(arg_框, "現金：", 320, 388, 0, style)
                self._文(arg_框, self._钱(f.现金[slot]), 560, 388, 1, style)
                self._文(arg_框, "存款：", 320, 406, 0, style)
                self._文(arg_框, self._钱(f.余额[slot]), 560, 406, 1, style)
                self._文(arg_框, "總資產：", 320, 424, 0, style)
                self._文(arg_框, self._钱(f.总资产[slot]), 560, 424, 1, style)
        # C++成员赋值仍保持movie引用有效；Python状态步可能换对象，须取当前影片。
        m = p.片
        if m.静帧.像素:
            arg_框.画布.api_绘制(m.静帧, m.x, m.y)
        self._贴泡(arg_框, p, 25)
        return True
