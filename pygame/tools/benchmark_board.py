# ◑ 导入
import argparse
import hashlib
import json
import platform
import statistics
import time
from pathlib import Path

from rich4.board_models import 场景_类, 玩家精灵_类, 相机_类
from rich4.board_renderer import 棋盘绘制_类
from rich4.graphics import 图像_类


# ◕ 功能
class 棋盘性能_类:
    """
    单独运行的CPU合成+RGBA微基准，不把结果称为实际窗口帧率。

    更新日志：
    2026.10.23 - 区分固定相机、瓦片内分数移动与跨瓦片移动，预热角色资源。
    """

    @staticmethod
    def api_执行(arg_素材: Path, arg_地图: int, arg_样本: int, arg_报告: Path) -> None:
        if arg_样本 < 20:
            raise ValueError("性能样本至少20帧")
        绘 = 棋盘绘制_类(arg_素材, arg_地图)
        中 = 绘.api_节点位置(51)
        if 中 is None:
            raise ValueError("地图缺少节点51")
        基x, 基y = 中[0] // 32 * 32, 中[1] // 32 * 32
        人 = 玩家精灵_类(位置=中, 角色=10, 走动=True, 活跃=True)
        场 = 场景_类(玩家=[人])
        图 = 图像_类(640, 480, [0x1234] * (640 * 480))
        for i in range(8):
            人.动画帧 = i
            绘.api_绘制(图, 场, 相机_类(中))
            图.api_RGBA()
        源目录 = Path(__file__).resolve().parents[1] / "src/rich4"
        报告 = {
            "scope": "CPU board composition plus RGBA only; not pygame display/input/audio FPS",
            "python": platform.python_version(),
            "machine": platform.machine(),
            "map": arg_地图,
            "source_sha256": {
                名: hashlib.sha256((源目录 / 名).read_bytes()).hexdigest()
                for 名 in ["board_renderer.py", "terrain.py", "graphics.py"]
            },
            "samples": arg_样本,
            "modes": {},
        }
        for 模式 in ["stationary", "fractional_moving", "tile_crossing"]:
            帧时 = []
            CPU时 = []
            for i in range(arg_样本):
                位置 = (
                    中
                    if 模式 == "stationary"
                    else (
                        (基x + i % 32, 基y + 31 - i % 32)
                        if 模式 == "fractional_moving"
                        else (基x + i * 4, 基y + i * 4)
                    )
                )
                人.位置, 人.动画帧 = 位置, i % 8
                起 = time.perf_counter()
                CPU起 = time.process_time()
                绘.api_绘制(图, 场, 相机_类(位置))
                图.api_RGBA()
                CPU时.append(time.process_time() - CPU起)
                帧时.append(time.perf_counter() - 起)
            报告["modes"][模式] = {
                "mean_seconds": round(statistics.mean(帧时), 6),
                "p95_seconds": round(sorted(帧时)[min(len(帧时) - 1, int(len(帧时) * 0.95))], 6),
                "max_seconds": round(max(帧时), 6),
                "mean_process_cpu_seconds": round(statistics.mean(CPU时), 6),
                "all_seconds": [round(秒, 6) for 秒 in 帧时],
            }
        arg_报告.parent.mkdir(parents=True, exist_ok=True)
        arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        print(
            json.dumps(
                {
                    名: {键: 值 for 键, 值 in 项.items() if 键 != "all_seconds"}
                    for 名, 项 in 报告["modes"].items()
                },
                ensure_ascii=False,
            )
        )


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--map", type=int, default=0)
    参数.add_argument("--samples", type=int, default=60)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    棋盘性能_类.api_执行(选项.assets, 选项.map, 选项.samples, 选项.report)
