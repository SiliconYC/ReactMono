# ◑ 导入
import argparse
import hashlib
import json
import random
import struct
import subprocess
import tempfile
from pathlib import Path

from rich4.graphics import 图像_类


# ◕ 功能
class 绘图差分_类:
    """
    合成整数图像的逐字节裁剪/不透明/自拷贝对照，不含商业像素。

    更新日志：
    2026.10.23 - 连续段复制优化覆盖同/异掩码、黑色、极端锚点与空尺寸。
    """

    @staticmethod
    def api_执行(arg_源码: Path, arg_构建: Path, arg_报告: Path) -> None:
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
        工具 = arg_构建.resolve() / "blit-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("blit_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        生成 = random.Random(2026102309)
        用例 = []
        for _ in range(10000):
            标志 = [生成.randrange(2), 生成.randrange(2), 生成.randrange(3), 生成.randrange(3)]
            尺寸 = [生成.randrange(11) for _ in range(4)]
            原点 = [生成.randrange(-8, 9) for _ in range(2)]
            锚点 = [
                生成.choice([-2147483648, 2147483647, 生成.randrange(-12, 13)]) for _ in range(2)
            ]
            if 生成.randrange(3):
                锚点 = [生成.randrange(-12, 13) for _ in range(2)]
            框 = 生成.choice([(0, 0, 10, 10), (-10, -10, 20, 20), (1, 2, 8, 9), (5, 5, 4, 4)])
            用例.append([*标志, *尺寸, *原点, *锚点, *框, 生成.randrange(65536)])
        输入 = "\n".join(" ".join(map(str, 行)) for 行 in 用例) + "\n"
        报告 = {
            "reference": 版本,
            "generator_seed": 2026102309,
            "status": "running",
            "scope": "synthetic raw RGB555 blit and mask outputs, including aliasing",
        }
        try:
            with tempfile.TemporaryDirectory(prefix="rich4-blit-") as 临时:
                路径 = Path(临时) / "outputs.bin"
                cpp = subprocess.run(
                    [str(工具), str(路径)], input=输入, text=True, capture_output=True, check=True
                )
                if int(cpp.stdout) != len(用例):
                    raise ValueError("blit输出数量不同")
                摘要 = hashlib.sha256()
                with 路径.open("rb") as 文件:
                    for 序, 行 in enumerate(用例):
                        (
                            自身,
                            不透明,
                            源掩,
                            目掩,
                            源宽,
                            源高,
                            宽,
                            高,
                            原x,
                            原y,
                            x,
                            y,
                            左,
                            顶,
                            右,
                            底,
                            种子,
                        ) = 行
                        源 = 图像_类(
                            源宽,
                            源高,
                            [
                                0 if i % 5 == 0 else (i * 129 + 种子 * 73) & 0xFFFF
                                for i in range(源宽 * 源高)
                            ],
                            原x,
                            原y,
                            bytes(源掩 if i % 3 else 0 for i in range(源宽 * 源高))
                            if 源掩
                            else b"",
                        )
                        图 = 图像_类(
                            宽,
                            高,
                            [(i * 257 + 种子 * 29) & 0xFFFF for i in range(宽 * 高)],
                            不透明=bytes(目掩 if i % 4 else 0 for i in range(宽 * 高))
                            if 目掩
                            else b"",
                        )
                        if 自身:
                            源 = 图
                            图.原点x, 图.原点y = 原x, 原y
                        状态 = 0
                        try:
                            图.api_绘制(源, x, y, (左, 顶, 右, 底), bool(不透明))
                        except (ValueError, IndexError):
                            状态 = 1
                        输出 = struct.pack("<III", 状态, len(图.像素), len(图.不透明))
                        输出 += struct.pack(f"<{len(图.像素)}H", *图.像素) + 图.不透明
                        if 输出 != 文件.read(len(输出)):
                            raise ValueError(f"blit用例{序}/{行}像素或掩码不同")
                        摘要.update(输出)
                    if 文件.read(1):
                        raise ValueError("blit有剩余字节")
                报告.update(
                    status="passed",
                    cases=len(用例),
                    input_sha256=hashlib.sha256(输入.encode()).hexdigest(),
                    output_sha256=摘要.hexdigest(),
                )
        except (ValueError, IndexError, OSError, subprocess.CalledProcessError) as 错误:
            报告.update(status="failed", error=str(错误))
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        print(f"[完成] {len(用例)}个blit像素/掩码/自拷贝用例一致。")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    绘图差分_类.api_执行(选项.source, 选项.build, 选项.report)
