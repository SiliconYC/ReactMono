# SPDX-License-Identifier: GPL-3.0-or-later
# 原资源渲染验收工具；角色位置是显式取样点，不执行或替代任何游戏回合。
# ◑ 导入
import argparse
import hashlib
import json
import time
from pathlib import Path
from typing import TextIO

import pygame

from rich4.board_models import 场景_类, 玩家精灵_类, 相机_类
from rich4.board_renderer import 棋盘绘制_类
from rich4.graphics import 图像_类
from rich4.viewport import 视口_类


# ◕ 功能
class 棋盘预览_类:
    """
    独立Pygame窗口核验平移/旋转/精灵帧，明确不呈现未实现的游戏UI。

    更新日志：
    2026.10.23 - 读取真实八图、原角色帧及键鼠日志；采样时序不作为游戏动画验收。
    """

    def __init__(self, arg_素材: Path, arg_地图: int, arg_角色: int) -> None:
        if not 0 <= arg_角色 < 12:
            raise ValueError("角色必须为0..11")
        self.素材, self.地图, self.角色 = arg_素材, arg_地图, arg_角色
        self.帧, self.取样 = 0, False
        self._载入()

    def _载入(self) -> None:
        self.绘制 = 棋盘绘制_类(self.素材, self.地图)
        中心 = self.绘制.api_节点位置(51)
        if 中心 is None:
            raise ValueError("地图缺少验收取样节点51")
        self.相机 = 相机_类(中心)
        self.玩家 = 玩家精灵_类(位置=中心, 角色=self.角色, 走动=True, 活跃=True)
        self.场景 = 场景_类(玩家=[self.玩家])

    def _按键(self, arg_键: int) -> bool:
        if arg_键 in (pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            x, y = self.相机.中心
            x += -32 if arg_键 == pygame.K_LEFT else 32 if arg_键 == pygame.K_RIGHT else 0
            y += -32 if arg_键 == pygame.K_UP else 32 if arg_键 == pygame.K_DOWN else 0
            self.相机.中心 = x, y
        elif arg_键 in (pygame.K_q, pygame.K_e):
            self.相机.旋转 = (self.相机.旋转 + (1 if arg_键 == pygame.K_e else -1)) & 7
        elif pygame.K_0 <= arg_键 <= pygame.K_7:
            self.相机.旋转 = arg_键 - pygame.K_0
        elif arg_键 == pygame.K_f:
            self.帧 = (self.帧 + 1) & 255
        elif arg_键 == pygame.K_SPACE:
            self.取样 = not self.取样
        elif arg_键 == pygame.K_HOME:
            self.相机.中心 = self.玩家.位置
        elif arg_键 == pygame.K_TAB:
            self.地图 = (self.地图 + 1) % 8
            self._载入()
        else:
            return False
        return True

    def _画布(self) -> pygame.Surface:
        图 = 图像_类(640, 480, [0] * (640 * 480))
        self.玩家.动画帧 = self.帧
        self.绘制.api_绘制(图, self.场景, self.相机)
        return pygame.image.frombytes(图.api_RGBA(), (640, 480), "RGBA")

    def api_执行(
        self, arg_截图: Path | None, arg_帧上限: int, arg_日志: Path | None, arg_间隔: int = 120
    ) -> None:
        if arg_间隔 <= 0 or arg_帧上限 < 0:
            raise ValueError("采样间隔必须为正，窗口帧上限不能为负")
        日志: TextIO | None = None
        if arg_日志:
            arg_日志.parent.mkdir(parents=True, exist_ok=True)
            日志 = arg_日志.open("w")
        pygame.display.init()
        pygame.display.set_caption("Rich4 Pygame — Board Verification (not gameplay)")
        窗口 = pygame.display.set_mode((640, 480), pygame.RESIZABLE)
        时钟 = pygame.time.Clock()
        运行, 重绘, 计数, 首帧 = True, True, 0, True
        上次 = time.monotonic()
        待记录: list[dict] = [{"event": "ready"}]
        try:
            画布: pygame.Surface | None = None
            while 运行:
                视口 = 视口_类(*窗口.get_size())
                for 事件 in pygame.event.get():
                    if 事件.type == pygame.QUIT:
                        运行 = False
                        待记录.append({"event": "close"})
                    elif 事件.type == pygame.KEYDOWN:
                        if 事件.key == pygame.K_ESCAPE:
                            运行 = False
                            待记录.append({"event": "key", "key": "escape"})
                        elif self._按键(事件.key):
                            重绘 = True
                            待记录.append({"event": "key", "key": pygame.key.name(事件.key)})
                    elif 事件.type == pygame.VIDEORESIZE:
                        重绘 = True
                    elif 事件.type == pygame.MOUSEBUTTONDOWN:
                        待记录.append({"event": "click", "logical": 视口.api_逻辑位置(事件.pos)})
                现在 = time.monotonic()
                if self.取样 and (现在 - 上次) * 1000 >= arg_间隔:
                    self.帧 = (self.帧 + 1) & 255
                    上次, 重绘 = 现在, True
                if 重绘:
                    画布 = self._画布()
                    重绘 = False
                if 画布 is None:
                    raise RuntimeError("棋盘画布尚未建立")
                pygame.display.set_caption(
                    f"Rich4 Pygame — Board Verification — map {self.地图} view {self.相机.旋转} "
                    f"frame {self.帧} — Arrows/Q/E/F/Tab/Esc"
                )
                窗口.fill((0, 0, 0))
                左, 顶, 宽, 高 = 视口.矩形
                窗口.blit(pygame.transform.scale(画布, (宽, 高)), (左, 顶))
                pygame.display.flip()
                if 日志 and 待记录:
                    摘要 = hashlib.sha256(pygame.image.tobytes(画布, "RGBA")).hexdigest()
                    for 项 in 待记录:
                        项.update(
                            map=self.地图,
                            view=self.相机.旋转,
                            center=self.相机.中心,
                            frame=self.帧,
                            canvas_sha256=摘要,
                        )
                        日志.write(json.dumps(项, ensure_ascii=False) + "\n")
                    日志.flush()
                待记录.clear()
                if 首帧 and arg_截图:
                    arg_截图.parent.mkdir(parents=True, exist_ok=True)
                    pygame.image.save(画布, arg_截图)
                首帧 = False
                计数 += 1
                if arg_帧上限 and 计数 >= arg_帧上限:
                    运行 = False
                时钟.tick(60)
        finally:
            if 日志:
                日志.close()
            pygame.quit()


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser(description="原棋盘渲染验收；没有游戏回合或正式UI。")
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--map", type=int, default=0)
    参数.add_argument("--character", type=int, default=10)
    参数.add_argument("--screenshot", type=Path)
    参数.add_argument("--frames", type=int, default=0)
    参数.add_argument("--log", type=Path)
    参数.add_argument("--sample-ms", type=int, default=120)
    选项 = 参数.parse_args()
    棋盘预览_类(选项.assets, 选项.map, 选项.character).api_执行(
        选项.screenshot, 选项.frames, 选项.log, 选项.sample_ms
    )
