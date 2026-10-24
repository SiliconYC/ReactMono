# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_game.cpp::Application::run；Pygame窗口只适配原640×480画布和SDL事件。
# ◑ 导入
import json
from pathlib import Path

import pygame

from rich4.application import 游戏应用_类
from rich4.viewport import 视口_类


# ◕ 功能
class 游戏窗口_类:
    """
    960×720可缩放Pygame窗口、原画布黑边/最近邻、先绘制再输入再推进。

    更新日志：
    2026.10.24 - 固定步长和帧上限仅为开发验收；正常流程始终真实时钟。
    2026.10.24 - 创建窗口失败或音频退出报错时仍关闭应用、字体和显示设备。
    """

    def __init__(self, arg_应用: 游戏应用_类) -> None:
        self.应用 = arg_应用

    def api_诊断(self, arg_原因: str) -> None:
        app = self.应用
        if app.设置.输出 is None or app.会话 is None:
            return
        app.设置.输出.mkdir(parents=True, exist_ok=True)
        (app.设置.输出 / "failure-world.DAT").write_bytes(app.会话.世界.api_导出())
        (app.设置.输出 / "failure.json").write_text(
            json.dumps(
                {
                    "resumable_save": False,
                    "reason": arg_原因,
                    "phase": int(app.会话.阶段),
                    "random_state": app.会话.随机.状态,
                    "completed_days": app.会话.完成天数,
                    "decision": app.会话.待决策.提示 if app.会话.待决策 is not None else "",
                },
                ensure_ascii=False,
                indent=2,
            )
            + "\n"
        )

    def api_运行(
        self,
        arg_帧上限: int = 0,
        arg_截图: Path | None = None,
        arg_固定毫秒: int = 0,
    ) -> None:
        app = self.应用
        try:
            pygame.display.init()
            pygame.display.set_caption("大富翁 4")
            window = pygame.display.set_mode((960, 720), pygame.RESIZABLE)
            last = pygame.time.get_ticks()
            frames = 0
            while app.运行:
                now = pygame.time.get_ticks()
                image = app.api_绘制(now)
                surface = pygame.image.frombytes(image.api_RGBA(), (640, 480), "RGBA")
                viewport = 视口_类(*window.get_size())
                left, top, width, height = viewport.矩形
                window.fill((0, 0, 0))
                window.blit(pygame.transform.scale(surface, (width, height)), (left, top))
                pygame.display.flip()
                events = []
                for event in pygame.event.get():
                    if event.type in (
                        pygame.MOUSEMOTION,
                        pygame.MOUSEBUTTONDOWN,
                        pygame.MOUSEBUTTONUP,
                    ):
                        x, y = event.pos
                        # 与SDL逻辑坐标转换一样保留黑边外坐标，不能把拖出视口当成没有事件。
                        logical = int((x - left) * 640 / width), int((y - top) * 480 / height)
                        event = pygame.event.Event(event.type, {**event.dict, "pos": logical})
                    events.append(event)
                app.api_输入(events)
                tick = pygame.time.get_ticks()
                elapsed = (
                    arg_固定毫秒
                    if arg_固定毫秒
                    else min((tick - last) & 0xFFFFFFFFFFFFFFFF, 100) * app.速度
                )
                last = tick
                app.api_推进(elapsed)
                frames += 1
                if arg_截图 is not None and frames == 1:
                    arg_截图.parent.mkdir(parents=True, exist_ok=True)
                    pygame.image.save(surface, arg_截图)
                if arg_帧上限 and frames >= arg_帧上限:
                    app.运行 = False
                if not arg_固定毫秒:
                    pygame.time.wait(8)
            if app.会话 is not None and app.会话.api_可保存() and not app.设置.验证天数:
                app.api_写存档(app.api_槽路径(0))
        except Exception as error:
            # 对应原std::exception边界，只增加诊断后原样抛出，不跳过规则或假装恢复。
            self.api_诊断(str(error))
            raise
        finally:
            try:
                app.api_关闭()
            finally:
                pygame.quit()
