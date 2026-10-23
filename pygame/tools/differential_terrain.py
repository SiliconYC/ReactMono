# ◑ 导入
import argparse
import hashlib
import json
import random
import struct
import subprocess
import tempfile
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.graphics import 图像_类
from rich4.terrain import 地形_类, 地面_类


# ◕ 功能
class 地形差分_类:
    """
    真实GND总览及合成四边形完整像素/掩码对照，公开报告不含商业图像。

    更新日志：
    2026.10.23 - 八图GND与扫描器不同绕向/裁剪/边界测试。
    """

    @staticmethod
    def _输出(arg_图: 图像_类, arg_状态: int = 0) -> bytes:
        return (
            struct.pack("<III", arg_状态, len(arg_图.像素), len(arg_图.不透明))
            + struct.pack(f"<{len(arg_图.像素)}H", *arg_图.像素)
            + arg_图.不透明
        )

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_地图包: Path, arg_报告: Path) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("C++版本不符")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            [
                "cmake",
                "-S",
                str(arg_源码),
                "-B",
                str(arg_构建),
                "-DRICH4_BUILD_GAME=OFF",
                "-DRICH4_BUILD_VIEWER=OFF",
                "-DBUILD_TESTING=OFF",
            ],
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["cmake", "--build", str(arg_构建), "--target", "rich4_core", "--parallel", "6"],
            check=True,
            capture_output=True,
        )
        工具 = arg_构建.resolve() / "terrain-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("terrain_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告: dict = {
            "reference": 版本,
            "generator_seed": 2026102307,
            "scope": "raw GND overview and fixed-point rasterization; not board composition or UI",
            "status": "running",
            "grounds": [],
        }
        try:
            包 = 资源包_类(arg_地图包)
            with tempfile.TemporaryDirectory(prefix="rich4-terrain-") as 临时:
                路径 = Path(临时)
                for 图 in range(8):
                    数据 = 包.api_解码(图 * 2)
                    地 = 地面_类.api_解码(数据)
                    输入路径, 输出路径 = 路径 / "input.gnd", 路径 / "overview.bin"
                    输入路径.write_bytes(数据)
                    cpp = subprocess.run(
                        [str(工具), "--ground", str(输入路径), str(输出路径)],
                        text=True,
                        capture_output=True,
                        check=True,
                    )
                    if list(map(int, cpp.stdout.split())) != [
                        地.宽瓦片,
                        地.高瓦片,
                        地.保留,
                        地.api_瓦片数(),
                    ]:
                        raise ValueError(f"图{图} GND字段不同")
                    画面 = 地.api_总览()
                    字段 = (
                        struct.pack("<II", len(地.索引), len(地.纹理))
                        + struct.pack("<256H", *地.调色板)
                        + struct.pack(f"<{len(地.索引)}H", *地.索引)
                        + 地.纹理
                    )
                    输出 = 字段 + cls._输出(画面)
                    if 输出 != 输出路径.read_bytes():
                        raise ValueError(f"图{图} GND总览像素不同")
                    报告["grounds"].append(
                        {
                            "map": 图,
                            "tile_width": 地.宽瓦片,
                            "tile_height": 地.高瓦片,
                            "tiles": 地.api_瓦片数(),
                            "pixels": len(画面.像素),
                            "input_sha256": hashlib.sha256(数据).hexdigest(),
                            "overview_sha256": hashlib.sha256(输出).hexdigest(),
                        }
                    )
                    del 数据, 地, 画面, 输出, 字段
                    print(f"[完成] 图{图}真实GND字段和总览像素一致。", flush=True)
                生成 = random.Random(报告["generator_seed"])
                用例 = []
                for i in range(4000):
                    角 = tuple(
                        (生成.randrange(-100, 160), 生成.randrange(-100, 160)) for _ in range(4)
                    )
                    框 = ((0, 0, 64, 48), (-10, -10, 74, 58), (10, 10, 50, 40), (30, 30, 10, 10))[
                        i % 4
                    ]
                    用例.append((i % 2, 框, 角))
                for 角 in [
                    ((2, 2), (2, 40), (40, 40), (40, 2)),
                    ((2, 2), (40, 2), (40, 40), (2, 40)),
                    ((0, 0),) * 4,
                    ((-32768, 0), (0, 2), (2, 2), (2, 0)),
                    ((32767, -32768), (-32768, 32767), (20, 20), (30, 0)),
                ]:
                    用例.extend((掩码, (0, 0, 64, 48), 角) for 掩码 in (0, 1))
                输入 = (
                    "\n".join(
                        " ".join(map(str, [掩码, *框, *(数 for 点 in 角 for 数 in 点)]))
                        for 掩码, 框, 角 in 用例
                    )
                    + "\n"
                )
                输出路径 = 路径 / "quads.bin"
                cpp = subprocess.run(
                    [str(工具), "--quads", str(输出路径)],
                    input=输入,
                    text=True,
                    capture_output=True,
                    check=True,
                )
                if int(cpp.stdout) != len(用例):
                    raise ValueError("扫描器输出数量不同")
                调色 = [(i * 0x123 + 0x11) & 0x7FFF for i in range(256)]
                纹理 = bytes((x + y * 7) & 255 for y in range(32) for x in range(32))
                摘要, 拒绝 = hashlib.sha256(), 0
                with 输出路径.open("rb") as 文件:
                    for i, (掩码, 框, 角) in enumerate(用例):
                        图像 = 图像_类(
                            64,
                            48,
                            [0x7BDE] * (64 * 48),
                            不透明=bytes(int(i % 3 == 0) for i in range(64 * 48)) if 掩码 else b"",
                        )
                        状态 = 0
                        try:
                            地形_类.api_绘瓦片(图像, 纹理, 调色, 角, 框)
                        except ValueError:
                            状态 = 1
                        输出 = cls._输出(图像, 状态)
                        if 输出 != 文件.read(len(输出)):
                            raise ValueError(f"扫描器用例{i} 状态/像素/掩码不同，角={角}框={框}")
                        摘要.update(输出)
                        拒绝 += 状态
                    if 文件.read(1):
                        raise ValueError("扫描器输出有未消费尾字节")
                报告["quads"] = {
                    "cases": len(用例),
                    "rejected": 拒绝,
                    "input_sha256": hashlib.sha256(输入.encode()).hexdigest(),
                    "output_sha256": 摘要.hexdigest(),
                }
            报告["status"] = "passed"
        except (ValueError, IndexError, OSError, subprocess.CalledProcessError) as 错误:
            报告.update(status="failed", error=str(错误))
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--map", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    地形差分_类.api_执行(选项.source, 选项.build, 选项.map, 选项.report)
