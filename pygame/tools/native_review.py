# SPDX-License-Identifier: GPL-3.0-or-later
# 本地桌面验收只观察原应用输入/状态，不投递合成事件或替代任何游戏规则。
# ◑ 导入
import argparse
import json
import os
import time
from dataclasses import asdict
from pathlib import Path

import pygame

from rich4.application import 游戏应用_类
from rich4.application_types import 应用设置_类
from rich4.application_window import 游戏窗口_类


# ◕ 功能
class 桌面验收_类(游戏应用_类):
    """
    运行正式真实时钟窗口，记录SDL收到的原生按键/按钮与自然世界状态变化。

    更新日志：
    2026.10.24 - 日志只写调用方本地路径，不将程序内截图或事件记录称为真人验收。
    """

    def __init__(self, arg_设置: 应用设置_类, arg_日志: Path) -> None:
        arg_日志.parent.mkdir(parents=True, exist_ok=True)
        self._日志 = arg_日志.open("a", encoding="utf-8")
        self._记录已关 = False
        self._上状态: tuple[int, ...] | None = None
        try:
            super().__init__(arg_设置)
        except BaseException:
            self._日志.close()
            raise
        self._行(
            json.dumps(
                {
                    "event": "initialized",
                    "seed": arg_设置.种子,
                    "music_available": self.音频.api_音乐可用(),
                    "audio_enabled": self.声效,
                    "audio_device": self.音频._设备.设备名称 if self.音频._设备 else None,
                    "time_ns": time.time_ns(),
                }
            )
        )

    def _行(self, arg_内容: str) -> None:
        self._日志.write(arg_内容 + "\n")
        self._日志.flush()

    def api_输入(self, arg_事件: list[pygame.event.Event]) -> None:
        for event in arg_事件:
            if event.type in (pygame.KEYDOWN, pygame.KEYUP):
                self._行(
                    json.dumps(
                        {
                            "event": "native-key",
                            "type": event.type,
                            "key": event.key,
                            "ticks": pygame.time.get_ticks(),
                        }
                    )
                )
            elif event.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP):
                self._行(
                    json.dumps(
                        {
                            "event": "native-pointer",
                            "type": event.type,
                            "button": event.button,
                            "logical_pos": event.pos,
                            "ticks": pygame.time.get_ticks(),
                        }
                    )
                )
            elif event.type == pygame.WINDOWSHOWN:
                self._行(
                    json.dumps(
                        {
                            "event": "window-shown",
                            "size": pygame.display.get_window_size(),
                            "driver": pygame.display.get_driver(),
                            "ticks": pygame.time.get_ticks(),
                        }
                    )
                )
        super().api_输入(arg_事件)

    def api_推进(self, arg_毫秒: int) -> None:
        super().api_推进(arg_毫秒)
        if self.会话 is None:
            return
        session = self.会话
        state = (
            session.完成天数,
            session.世界.头.当前玩家,
            int(session.阶段),
            session.随机.状态,
            session.世界.玩家[session.世界.头.当前玩家].记录.节点,
        )
        if state != self._上状态:
            self._上状态 = state
            self._行(
                json.dumps({"event": "world", "state": state, "ticks": pygame.time.get_ticks()})
            )

    def api_关闭(self) -> None:
        if self._记录已关:
            return
        try:
            super().api_关闭()
            self._行(
                json.dumps(
                    {
                        "event": "closed",
                        "audio": asdict(self.音频.api_统计()),
                        "font_closed": self.字体._库.value is None,
                    }
                )
            )
        finally:
            self._记录已关 = True
            self._日志.close()


def 主程序() -> None:
    参数 = argparse.ArgumentParser(description="真实桌面游戏及原生输入观察日志。")
    for name in ("assets", "font", "save-dir", "log"):
        参数.add_argument("--" + name, type=Path, required=True)
    参数.add_argument("--load", type=Path)
    参数.add_argument("--screenshot", type=Path)
    参数.add_argument("--seed", type=int, default=int(time.time()) & 0xFFFFFFFF)
    参数.add_argument("--frames", type=int, default=0)
    参数.add_argument("--silent", action="store_true")
    参数.add_argument("--audio-device")
    选项 = 参数.parse_args()
    if 选项.audio_device is not None:
        os.environ["RICH4_AUDIO_DEVICE"] = 选项.audio_device
    应用 = 桌面验收_类(
        应用设置_类(选项.assets, 选项.font, 选项.save_dir, 种子=选项.seed, 静音=选项.silent),
        选项.log,
    )
    if 选项.load is not None:
        应用.api_读取(选项.load)
    游戏窗口_类(应用).api_运行(选项.frames, 选项.screenshot)


# ◍ 运行
if __name__ == "__main__":
    主程序()
