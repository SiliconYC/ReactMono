# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import math
import platform
from pathlib import Path
from statistics import median
from time import perf_counter_ns

from rich4.artwork import 美术_类
from rich4.game import 游戏会话_类
from rich4.graphics import 图像_类
from rich4.main_screen import 主屏幕_类
from rich4.main_screen_types import 主屏动作_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 字体_类
from rich4.world import 世界_类


# ◕ 功能
class 主屏基准_类:
    """
    原主屏三个视图的暖缓存CPU绘制测量，不把组件时间声称为完整窗口FPS。

    更新日志：
    2026.10.24 - 固定真实世界/字体和40帧输入；回调只供无点击的测量宿主记录。
    """

    @staticmethod
    def api_执行(
        arg_素材: Path,
        arg_字体: Path,
        arg_次数: int,
        arg_报告: Path,
    ) -> None:
        if arg_次数 < 5:
            raise ValueError("基准至少采样五帧")
        美术 = 美术_类(arg_素材)
        会 = 游戏会话_类(世界_类.api_从地图(美术.api_解码("m", 1)), 1)
        字 = 字体_类(arg_字体)
        记录 = []
        动作 = 主屏动作_类(
            *[lambda: 记录.append(0) for _ in range(10)],
            记录.append,
            lambda: 记录.append(100),
            记录.append,
            记录.append,
        )
        报 = {
            "scope": "warm MainScreen chrome CPU only; no board, SDL window, audio or gameplay FPS",
            "python": platform.python_version(),
            "platform": platform.platform(),
            "font_sha256": hashlib.sha256(arg_字体.read_bytes()).hexdigest(),
            "freetype_library": 字.库路径,
            "native_ui_source_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/native_ui.py").read_bytes()
            ).hexdigest(),
            "samples_per_view": arg_次数,
            "warmup_per_view": 5,
            "views": [],
        }
        try:
            for 模式 in range(3):
                屏 = 主屏幕_类(f"view={模式}")
                框 = 画框_类(图像_类(640, 480, [0] * 307200), 美术, 字, [])
                时长 = []
                for i in range(arg_次数 + 5):
                    框.按钮.clear()
                    框.时钟 = i * 16
                    开始 = perf_counter_ns()
                    屏.api_绘制(框, 会, 0, 动作)
                    dt = (perf_counter_ns() - 开始) / 1e6
                    if i >= 5:
                        时长.append(dt)
                报["views"].append(
                    {
                        "view": 模式,
                        "median_ms": median(时长),
                        "p95_ms": sorted(时长)[math.ceil(arg_次数 * 0.95) - 1],
                        "max_ms": max(时长),
                    }
                )
        finally:
            字.api_关闭()
        arg_报告.parent.mkdir(parents=True, exist_ok=True)
        arg_报告.write_text(json.dumps(报, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(报["views"]))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for 键 in ("assets", "font", "report"):
        参数.add_argument("--" + 键, type=Path, required=True)
    参数.add_argument("--samples", type=int, default=40)
    选项 = 参数.parse_args()
    主屏基准_类.api_执行(选项.assets, 选项.font, 选项.samples, 选项.report)
