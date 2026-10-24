# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/intro.cpp；AVI占位与Loading400毫秒沿用参考，不声称官方时长。
# ◑ 导入
import sys
from collections.abc import Callable, Sequence
from copy import deepcopy
from dataclasses import dataclass

from rich4.artwork import 美术_类
from rich4.flc import 动画_类
from rich4.graphics import 图像_类
from rich4.screen_draw import 屏幕绘图_类


# ◕ 功能
@dataclass
class 开局镜头_类:
    """
    原Shot的底图、影片位置、起始/指定帧声音与静图停留时间。

    更新日志：
    2026.10.24 - 底图可共享，只暗化独立等待者副本。
    """

    底图: 图像_类
    影片: int = -1
    x: int = 0
    y: int = 0
    起声: int = -1
    帧声: int = -1
    响帧: int = 0
    停留毫秒: int = 0


class 开局演出_类:
    """
    真实Jump开门、按出场顺序跳机与降落伞渐进电影，不触碰规则世界。

    更新日志：
    2026.10.24 - 每次最多推进100毫秒，跨镜头传余量；跳过结束整个开场。
    """

    def __init__(self, arg_美术: 美术_类) -> None:
        self.美术 = arg_美术
        self._镜头: list[开局镜头_类] = []
        self._索引 = 0
        self._电影: 动画_类 | None = None
        self._帧 = 图像_类(0, 0, [])
        self._已过, self._间隔 = 0, 100
        self._已开始 = self._已响 = False

    def api_开始(self, arg_角色: Sequence[int]) -> None:
        self._镜头.clear()
        self._索引, self._电影, self._已开始 = 0, None, False
        try:
            self._镜头.append(开局镜头_类(self.美术.api_原图("d", 601, 640, 480), 停留毫秒=400))
            plane = self.美术.api_帧("j", 45, 0)

            def 底图() -> 图像_类:
                image = 图像_类(640, 480, [0] * 307200)
                image.api_绘制(plane, 0, 0, arg_强制不透明=True)
                return image

            door = 底图()
            self._镜头.append(开局镜头_类(door, 46, 180, 60, 25))
            for i in range(1, len(arg_角色) + 1):
                still = door
                if i < len(arg_角色):
                    still = 底图()
                    wait = deepcopy(self.美术.api_帧("j", 45, 3 + arg_角色[i] % 12))
                    屏幕绘图_类.api_暗化(wait, (0, 0, wait.宽, wait.高), -20)
                    still.api_绘制(wait, 270, 220)
                    still.api_绘制(self.美术.api_帧("j", 45, 2), 150, 60)
                self._镜头.append(开局镜头_类(still, 47 + arg_角色[i - 1] % 12, 帧声=26, 响帧=20))
            sky = 图像_类(640, 480, [0] * 307200)
            sky.api_绘制(self.美术.api_帧("j", 45, 1), 0, 0, arg_强制不透明=True)
            self._镜头 += [开局镜头_类(sky, 59 + ch % 12) for ch in arg_角色]
        except (ValueError, IndexError, OSError) as 错:
            # 原start坏资源时跳过全部开场；不伪造影片或让加载停在不完整镜头。
            print(f"[警告] 开场已跳过：{错}", file=sys.stderr)
            self._镜头.clear()

    def api_活跃(self) -> bool:
        return self._索引 < len(self._镜头)

    def api_跳过(self) -> None:
        self._索引, self._电影 = len(self._镜头), None

    def _开始镜头(self) -> None:
        shot = self._镜头[self._索引]
        self._电影, self._已过, self._已响, self._已开始 = None, 0, False, True
        if shot.影片 >= 0:
            self._电影 = self.美术.api_动画("j", shot.影片)
            self._间隔 = self._电影.间隔毫秒 or 100
            if self._电影.api_下一帧():
                self._帧 = self._电影.api_图像()

    def api_绘制(
        self,
        arg_画布: 图像_类,
        arg_已过: int,
        arg_声音: Callable[[int], None] | None,
    ) -> None:
        if not self.api_活跃():
            return

        def 响(arg_号: int) -> None:
            if arg_号 >= 0 and arg_声音 is not None:
                arg_声音(arg_号)

        try:
            elapsed = min(arg_已过 & 0xFFFFFFFF, 100)
            if not self._已开始:
                self._开始镜头()
                响(self._镜头[self._索引].起声)
                elapsed = 0
            self._已过 = (self._已过 + elapsed) & 0xFFFFFFFF
            while True:
                shot = self._镜头[self._索引]
                length = (
                    (max(1, self._电影.帧数) * self._间隔) & 0xFFFFFFFF
                    if self._电影 is not None
                    else shot.停留毫秒
                )
                if self._已过 < length:
                    break
                carry = self._已过 - length
                self._索引 += 1
                if not self.api_活跃():
                    self._电影 = None
                    return
                self._开始镜头()
                响(self._镜头[self._索引].起声)
                self._已过 = carry
            shot = self._镜头[self._索引]
            if self._电影 is not None:
                frame = self._已过 // self._间隔
                while self._电影.已解帧 <= frame and self._电影.api_下一帧():
                    self._帧 = self._电影.api_图像()
                if not self._已响 and shot.帧声 >= 0 and frame >= shot.响帧:
                    响(shot.帧声)
                    self._已响 = True
            arg_画布.api_绘制(shot.底图, 0, 0, arg_强制不透明=True)
            if self._电影 is not None:
                arg_画布.api_绘制(self._帧, shot.x, shot.y)
        except (ValueError, IndexError, OSError) as 错:
            print(f"[警告] 开场已跳过：{错}", file=sys.stderr)
            self.api_跳过()
