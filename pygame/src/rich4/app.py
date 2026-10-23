# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import struct
from pathlib import Path

import pygame

from rich4.assets import 资源包_类
from rich4.graphics import 图像_类
from rich4.viewport import 视口_类


# ◕ 功能
class 资源预览_类:
    """
    首阶段真实资源验收窗口；尚无规则时明确标识为预览工具。

    更新日志：
    2026.10.23 - 建立 Pygame 原画布、事件循环、帧切换和缩放。
    """

    def __init__(
        self,
        arg_资源: Path,
        arg_条目: int,
        arg_帧: int,
    ) -> None:
        self.包 = 资源包_类(arg_资源)
        self.名称 = arg_资源.name
        self.条目 = arg_条目
        self.帧 = arg_帧
        self.运行 = True
        self.图: 图像_类
        self._读取()

    def _读取(self) -> None:
        数据 = self.包.api_解码(self.条目)
        if 数据[:4] in (b"SPR\0", b"SMP\0"):
            self.帧数 = int.from_bytes(数据[4:8], "little")
            self.图 = 图像_类.api_解码(数据, self.帧)
        elif len(数据) == 640 * 480 * 2:
            self.帧数 = 1
            self.帧 = 0
            self.图 = 图像_类(640, 480, list(struct.unpack("<307200H", 数据)))
        else:
            raise ValueError(f"{self.名称}:{self.条目} 不是 SPR/SMP 或 640×480 原始画面")
        self.表面 = pygame.image.frombytes(self.图.api_RGBA(), (self.图.宽, self.图.高), "RGBA")

    def api_画布(self) -> pygame.Surface:
        画布 = pygame.Surface((640, 480))
        画布.fill((0, 0, 0))
        # 预览器把精灵完整置中；游戏场景仍用 graphics 模块的原锚点规则。
        画布.blit(self.表面, ((640 - self.图.宽) // 2, (480 - self.图.高) // 2))
        return 画布

    def api_执行(self, arg_截图: Path | None = None, arg_帧上限: int = 0) -> None:
        pygame.display.init()
        窗口 = pygame.display.set_mode((640, 480), pygame.RESIZABLE)
        时钟 = pygame.time.Clock()
        计数 = 0
        try:
            while self.运行:
                视口 = 视口_类(*窗口.get_size())
                for 事件 in pygame.event.get():
                    if 事件.type == pygame.QUIT:
                        self.运行 = False
                    elif 事件.type == pygame.KEYDOWN:
                        if 事件.key == pygame.K_ESCAPE:
                            self.运行 = False
                        elif 事件.key in (pygame.K_LEFT, pygame.K_RIGHT):
                            self.帧 = (
                                self.帧 + (1 if 事件.key == pygame.K_RIGHT else -1)
                            ) % self.帧数
                            self._读取()
                    elif 事件.type == pygame.MOUSEBUTTONDOWN:
                        逻辑位置 = 视口.api_逻辑位置(事件.pos)
                        if 逻辑位置 is not None:
                            print(f"[信息] 画布位置 {逻辑位置}。", flush=True)
                pygame.display.set_caption(
                    f"Rich4 Pygame — Resource Preview — {self.名称}:{self.条目} "
                    f"frame {self.帧 + 1}/{self.帧数} — Left/Right, Esc"
                )
                画布 = self.api_画布()
                窗口.fill((0, 0, 0))
                左, 顶, 宽, 高 = 视口.矩形
                窗口.blit(pygame.transform.scale(画布, (宽, 高)), (左, 顶))
                pygame.display.flip()
                计数 += 1
                if arg_截图 is not None and 计数 == 1:
                    arg_截图.parent.mkdir(parents=True, exist_ok=True)
                    pygame.image.save(画布, arg_截图)
                if arg_帧上限 and 计数 >= arg_帧上限:
                    self.运行 = False
                时钟.tick(60)
        finally:
            pygame.quit()


def 主程序() -> None:
    参数 = argparse.ArgumentParser(description="Pygame 移植基础设施：真实素材预览，尚非完整游戏。")
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--archive", default="Panel.mkf")
    参数.add_argument("--entry", type=int, default=0)
    参数.add_argument("--frame", type=int, default=0)
    参数.add_argument("--screenshot", type=Path)
    参数.add_argument("--frames", type=int, default=0)
    选项 = 参数.parse_args()
    # 目录查找兼容用户原包大小写，歧义不静默选择。
    匹配 = [p for p in 选项.assets.iterdir() if p.name.casefold() == 选项.archive.casefold()]
    if len(匹配) != 1:
        raise ValueError(f"素材缺失或大小写歧义：{选项.archive}")
    资源预览_类(匹配[0], 选项.entry, 选项.frame).api_执行(选项.screenshot, 选项.frames)


# ◍ 运行
if __name__ == "__main__":
    主程序()
