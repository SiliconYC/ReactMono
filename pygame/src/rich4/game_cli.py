# SPDX-License-Identifier: GPL-3.0-or-later
# 正式游戏入口；独立Python规则与原画布，缺省读取游戏自身的开放素材目录。
# ◑ 导入
import argparse
import os
import time
from pathlib import Path

from rich4.application import 游戏应用_类
from rich4.application_types import 应用设置_类
from rich4.application_window import 游戏窗口_类


# ◕ 功能
def 主程序() -> None:
    参数 = argparse.ArgumentParser(
        description="Pygame《大富翁4》：独立Python移植，完整体验仍在验收。"
    )
    参数.add_argument("--assets", type=Path, default=Path(__file__).resolve().parents[2] / "assets")
    参数.add_argument("--font", type=Path)
    参数.add_argument(
        "--save-dir",
        type=Path,
        default=Path(__file__).resolve().parents[2] / "userdata/saves",
    )
    参数.add_argument("--load", type=Path)
    参数.add_argument("--seed", type=int, default=int(time.time()) & 0xFFFFFFFF)
    参数.add_argument("--headless", action="store_true")
    参数.add_argument("--silent", action="store_true")
    参数.add_argument("--audio-device", help="明确指定SDL输出设备；缺省跟随系统默认")
    参数.add_argument("--frames", type=int, default=0)
    参数.add_argument("--screenshot", type=Path)
    参数.add_argument("--output", type=Path)
    选项 = 参数.parse_args()
    选项.assets = 选项.assets.resolve()
    if not (选项.assets / "manifest.json").is_file():
        参数.error("请先用import_open_assets.py将正版素材导入游戏自身的pygame/assets目录")
    选项.font = (选项.font or 选项.assets / "fonts/ui.ttc").resolve()
    if not 选项.font.is_relative_to(选项.assets):
        参数.error("字体必须位于游戏自身的素材目录内")
    if 选项.audio_device is not None:
        os.environ["RICH4_AUDIO_DEVICE"] = 选项.audio_device
    if 选项.headless:
        os.environ["SDL_VIDEODRIVER"] = "dummy"
        os.environ["SDL_AUDIODRIVER"] = "dummy"
    设置 = 应用设置_类(
        选项.assets,
        选项.font,
        选项.save_dir,
        种子=选项.seed,
        载入=选项.load,
        输出=选项.output,
        静音=选项.silent,
    )
    应用 = 游戏应用_类(设置)
    if not 选项.silent and not 应用.音频.api_音乐可用():
        print(f"[警告] 背景音乐不可用：{应用.音频.诊断}", flush=True)
    if 选项.load is not None:
        应用.api_读取(选项.load)
    游戏窗口_类(应用).api_运行(选项.frames, 选项.screenshot)


# ◍ 运行
if __name__ == "__main__":
    主程序()
