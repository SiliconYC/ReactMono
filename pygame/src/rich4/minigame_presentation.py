# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ tools/screens/minigames.cpp；原时序/命中/场景合成。
# ◑ 导入
from dataclasses import dataclass
from typing import Callable

from rich4.artwork import 美术_类
from rich4.graphics import 图像_类
from rich4.minigames import (
    企鹅_类,
    图框_类,
    声音请求_类,
    天降_类,
    小游戏种类_类,
    小游戏阶段_类,
    气球_类,
)


# ◕ 功能
@dataclass(frozen=True)
class 小游戏结算_类:
    """
    完成时恰好提交一次真实分数和随机调用次数。

    更新日志：
    2026.10.23 - 对应native::minigames::Result。
    """

    分数: int
    随机次数: int


class 小游戏演出_类:
    """
    原小游戏屏幕、模态FLC、计时/数字/命中/声音和结果接口。

    更新日志：
    2026.10.23 - 对应MiniGames，测试机器人仅供开发验证。
    """

    def __init__(
        self,
        arg_美术: 美术_类,
        arg_种类: 小游戏种类_类,
        arg_种子: int,
        arg_角色: int = 0,
        arg_声音: Callable[[声音请求_类], None] | None = None,
        arg_机器人: bool = False,
    ) -> None:
        self.美术, self.种类, self.种子, self.角色 = (
            arg_美术,
            小游戏种类_类(arg_种类),
            arg_种子,
            (arg_角色 & 255) % 12,
        )
        self.声回调, self.循环音 = arg_声音, 0
        self.积余 = self.准备毫秒 = self.盖洞 = 0
        self.分数盖章, self.已结算 = False, False
        self.准备片, self.爆片 = None, None
        self.爆帧 = -1
        self.机器人, self.机器等待 = arg_机器人, 0
        self.命中图 = b""
        if self.种类 == 小游戏种类_类.企鹅:
            self.逻辑 = 企鹅_类(arg_种子)
            背 = self.美术.api_帧("p", 80, 0)
            self.命中图 = self.美术.api_解码("p", 81)
        elif self.种类 == 小游戏种类_类.气球:
            self.逻辑 = 气球_类(arg_种子)
            背 = self.美术.api_帧("p", 91, 0)
        else:
            框 = []
            for i in range(self.美术.api_帧数("p", 100 + self.角色)):
                图 = self.美术.api_帧("p", 100 + self.角色, i)
                框.append(图框_类(图.宽, 图.高, 图.原点x, 图.原点y))
            self.爆片 = self.美术.api_动画("d", 526)
            总 = self.爆片.帧数 * self.爆片.间隔毫秒
            self.逻辑 = 天降_类(arg_种子, self.角色, 框, (总 + 49) // 50)
            背 = self.美术.api_原图("p", 92, 640, 480)
        self.背景 = 图像_类(背.宽, 背.高, 背.像素.copy(), 背.原点x, 背.原点y, 背.不透明)

    def api_关闭(self) -> None:
        if self.循环音:
            if self.声回调:
                self.声回调(声音请求_类(2, self.循环音))
            self.循环音 = 0

    @staticmethod
    def _缩放(arg_画: 图像_类, arg_图: 图像_类, arg_x: int, arg_y: int, arg_缩: int) -> None:
        if not arg_缩 or not arg_图.宽 or not arg_图.高:
            return
        宽, 高 = arg_图.宽 * arg_缩 >> 16, arg_图.高 * arg_缩 >> 16
        左, 上 = arg_x - arg_图.原点x, arg_y - arg_图.原点y
        for y in range(max(0, 上), min(387, 上 + 高)):
            sy = ((y - 上) << 16) // arg_缩
            if sy >= arg_图.高:
                continue
            for x in range(max(0, 左), min(640, 左 + 宽)):
                sx = ((x - 左) << 16) // arg_缩
                if sx >= arg_图.宽:
                    continue
                i = sy * arg_图.宽 + sx
                可见 = arg_图.不透明[i] != 0 if arg_图.不透明 else arg_图.像素[i] != 0
                if 可见:
                    arg_画.像素[y * arg_画.宽 + x] = arg_图.像素[i]

    def _数字(self, arg_画: 图像_类, arg_文: str, arg_x: tuple[int, ...]) -> None:
        for x, c in zip(arg_x, arg_文):
            if "0" <= c <= "9":
                arg_画.api_绘制(self.美术.api_帧("p", 79, int(c)), x, 421, arg_强制不透明=True)

    def _大分(self, arg_画: 图像_类, arg_分: int) -> None:
        文 = str(arg_分)
        x = 353 - len(文) * 33
        for c in 文:
            if "0" <= c <= "9":
                arg_画.api_绘制(self.美术.api_帧("p", 79, 10 + int(c)), x, 150)
            x += 66

    def api_点击(self, arg_x: int, arg_y: int) -> None:
        if self.机器人 or not (0 <= arg_x < 640 and 0 <= arg_y < 480):
            return
        戏 = self.逻辑
        if isinstance(戏, 企鹅_类):
            if 戏.阶段 == 小游戏阶段_类.结算:
                戏.api_任意点击()
                return
            列, 行 = -1, -1
            if 0 <= arg_x < 640 and 0 <= arg_y < 480 and arg_y * 640 + arg_x < len(self.命中图):
                号 = self.命中图[arg_y * 640 + arg_x]
                if 号 and 戏.api_有效(号 % 9, 号 // 9):
                    列, 行 = 号 % 9, 号 // 9
            if 列 < 0:
                最 = 40 * 40 + 1
                for r in range(9):
                    for c in range(9):
                        if not 戏.api_有效(c, r):
                            continue
                        格 = 戏.格子[r][c]
                        dx, dy = 格.x - arg_x, (格.y - 8 - arg_y) * 2
                        if dx * dx + dy * dy < 最:
                            最, 列, 行 = dx * dx + dy * dy, c, r
            if 列 >= 0:
                戏.api_点击(列, 行)
        elif isinstance(戏, 气球_类):
            戏.api_点击(arg_x, arg_y)
        else:
            戏.api_目标(arg_x)

    def _自动操作(self) -> None:
        前 = self.机器等待
        self.机器等待 -= 1
        if 前 > 0:
            return
        戏 = self.逻辑
        if isinstance(戏, 企鹅_类):
            if not 戏.空闲:
                return
            for r in range(9):
                for c in range(9):
                    if 戏.格子[r][c].标志 & 15 > 1 and 戏.api_点击(c, r):
                        self.机器等待 = 3
                        return
        elif isinstance(戏, 气球_类):
            候 = [槽 for 槽 in 戏.槽 if 槽.x and not 槽.种类 & 0xF0 and 槽.y < 330]
            if 候:
                选 = max(候, key=lambda 槽: 槽.y)
                if 戏.api_点击(选.x, 选.y):
                    self.机器等待 = 6
        else:
            候 = [槽 for 槽 in 戏.槽 if 槽.x and 槽.位 & 15 != 4]
            if 候:
                戏.api_目标(max(候, key=lambda 槽: 槽.y).x)

    def api_帧(
        self, arg_毫秒: int, arg_指针x: int = -1, arg_按下: bool = False
    ) -> tuple[图像_类, 小游戏结算_类 | None]:
        戏, 毫秒 = self.逻辑, min(arg_毫秒, 100)
        if 毫秒 < 0:
            raise ValueError("小游戏显示时间不能倒退")
        if 戏.阶段 == 小游戏阶段_类.准备:
            if self.准备片 is None:
                self.准备片 = self.美术.api_动画("p", 78)
                self.准备片.api_下一帧()
                self.准备毫秒 = 0
            else:
                self.准备毫秒 += 毫秒
                间隔 = self.准备片.间隔毫秒
                if 间隔 <= 0:
                    raise ValueError("原准备片间隔必须为正")
                while self.准备毫秒 >= 间隔:
                    self.准备毫秒 -= 间隔
                    if not self.准备片.api_下一帧():
                        戏.api_开始()
                        self.准备片, self.积余 = None, 0
                        break
        elif 戏.阶段 != 小游戏阶段_类.完成:
            self.积余 += 毫秒
            tick = self.种类.api_间隔()
            while self.积余 >= tick and 戏.阶段 not in (小游戏阶段_类.准备, 小游戏阶段_类.完成):
                self.积余 -= tick
                戏.api_帧()
                for 声 in 戏.api_取声音():
                    if 声.操作 == 0:
                        if self.声回调:
                            self.声回调(声)
                    elif 声.操作 == 1:
                        if self.声回调:
                            self.声回调(声)
                        self.循环音 = 声.音效
                    elif self.循环音 == 声.音效:
                        if self.声回调:
                            self.声回调(声)
                        self.循环音 = 0
        if self.机器人:
            self._自动操作()
        elif isinstance(戏, 天降_类) and arg_按下 and arg_指针x >= 0:
            戏.api_目标(arg_指针x)
        画 = self._绘制()
        果 = None
        if 戏.阶段 == 小游戏阶段_类.完成 and not self.已结算:
            self.api_关闭()
            self.已结算 = True
            果 = 小游戏结算_类(戏.api_得分(), 戏.随机.次数)
        return 画, 果

    def _绘制(self) -> 图像_类:
        戏 = self.逻辑
        if isinstance(戏, 企鹅_类):
            while self.盖洞 < len(戏.洞):
                x, y = 戏.洞[self.盖洞]
                self.背景.api_绘制(self.美术.api_帧("p", 80, 9), x, y)
                self.盖洞 += 1
            if 戏.分数显示 and not self.分数盖章:
                self._大分(self.背景, 戏.api_得分())
                self.分数盖章 = True
        画 = 图像_类(640, 480, [0] * (640 * 480))
        画.api_绘制(self.背景, 0, 0, arg_强制不透明=True)
        for 精 in 戏.场景:
            图 = self.美术.api_帧(精.库, 精.条目, 精.帧)
            if 精.缩放:
                self._缩放(画, 图, 精.x, 精.y, 精.缩放)
            else:
                画.api_绘制(图, 精.x, 精.y, (0, 0, 640, 387))
        分 = 戏.api_得分()
        if isinstance(戏, 天降_类):
            if 戏.爆炸:
                需 = min(self.爆片.帧数 - 1, 戏.爆龄 * 50 // max(1, self.爆片.间隔毫秒))
                if self.爆帧 < 0:
                    self.爆片.api_倒带()
                    self.爆片.api_下一帧()
                    self.爆帧 = 0
                while self.爆帧 < 需 and self.爆片.api_下一帧():
                    self.爆帧 += 1
                画.api_绘制(self.爆片.api_图像(), 戏.爆x, 295)
            self._数字(画, f"{戏.剩余帧 // 2:03d}0", (49, 69, 94, 114))
            for 数, xs in zip(戏.接到[:4], ((185, 205), (276, 296), (367, 387), (458, 478))):
                self._数字(画, f"{数:02d}", xs)
            self._数字(画, f"{分:03d}", (549, 569, 589))
        elif isinstance(戏, 企鹅_类):
            self._数字(画, f"{戏.剩余帧:03d}0", (49, 69, 94, 114))
            for 数, xs in zip(
                (戏.发现[i] for i in (5, 3, 4, 2)), ((185, 205), (276, 296), (367, 387), (458, 478))
            ):
                self._数字(画, f"{数:02d}", xs)
            self._数字(画, f"{分:03d}", (549, 569, 589))
        else:
            self._数字(画, f"{戏.剩余帧:03d}0", (49, 69, 94, 114))
            self._数字(画, f"{分:04d}", (529, 549, 569, 589))
        if 戏.阶段 == 小游戏阶段_类.结算 and not isinstance(戏, 企鹅_类):
            self._大分(画, 分)
        if self.准备片:
            画.api_绘制(self.准备片.api_图像(), 0, 0)
        return 画
