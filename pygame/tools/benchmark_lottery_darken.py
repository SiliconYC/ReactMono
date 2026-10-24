# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import platform
import statistics
import time
from array import array
from pathlib import Path
from sys import byteorder

from rich4.graphics import 图像_类
from rich4.screen_draw import 屏幕绘图_类


# ◕ 功能
class 票面暗化基准_类:
    """
    原四块彩票面板的暗化CPU核基准，重置输入不计时，不等同完整游戏FPS。

    更新日志：
    2026.10.24 - 记录实现与输出哈希，区分预热与十次正式样本。
    """

    @staticmethod
    def api_执行(arg_报告: Path, arg_次数: int = 10) -> None:
        if arg_次数 < 2:
            raise ValueError("基准至少两次样本")
        原 = [(i * 1103515245) & 65535 for i in range(307200)]
        画 = 图像_类(640, 480, 原.copy())
        耗时 = []
        for n in range(arg_次数 + 5):
            画.像素[:] = 原
            起 = time.perf_counter_ns()
            for x, y in ((16, 340), (16, 410), (328, 340), (328, 410)):
                屏幕绘图_类.api_暗化(画, (x, y, x + 296, y + 60), -16)
            if n >= 5:
                耗时.append((time.perf_counter_ns() - 起) / 1e6)
        像 = array("H", 画.像素)
        if byteorder != "little":
            像.byteswap()
        报 = {
            "samples": len(耗时),
            "warmup": 5,
            "median_ms": statistics.median(耗时),
            "p95_ms": sorted(耗时)[min(len(耗时) - 1, (len(耗时) * 95 + 99) // 100 - 1)],
            "platform": platform.platform(),
            "python": platform.python_version(),
            "scope": (
                "four real lottery ticket rectangles, kernel CPU only, patterned RGB555 "
                "input reset each frame; not full game FPS"
            ),
            "source_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/screen_draw.py").read_bytes()
            ).hexdigest(),
            "state_sha256": hashlib.sha256(像.tobytes()).hexdigest(),
        }
        arg_报告.parent.mkdir(parents=True, exist_ok=True)
        arg_报告.write_text(json.dumps(报, indent=2) + "\n")
        print(json.dumps(报))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--report", type=Path, required=True)
    参数.add_argument("--samples", type=int, default=10)
    选项 = 参数.parse_args()
    票面暗化基准_类.api_执行(选项.report, 选项.samples)
