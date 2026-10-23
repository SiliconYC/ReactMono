# ◑ 导入
import argparse
import hashlib
import json
import struct
import subprocess
import tempfile
import time
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.flc import 动画_类
from rich4.graphics import 图像_类


# ◕ 功能
class 资源差分_类:
    """
    C++ 仅作测试 oracle；二进制和商业解码内容不进入证据报告。

    更新日志：
    2026.10.23 - 全资源字节差分和每图形首尾帧 PPM 差分。
    """

    @staticmethod
    def api_执行(
        arg_源码: Path,
        arg_构建: Path,
        arg_素材: Path,
        arg_报告: Path,
    ) -> None:
        版本 = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if 版本 != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("C++ 基准版本错误")
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
            [
                "cmake",
                "--build",
                str(arg_构建),
                "--target",
                "rich4-tool",
                "--parallel",
                "6",
            ],
            check=True,
            capture_output=True,
        )
        工具 = arg_构建.resolve() / "asset-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("asset_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告: dict = {
            "reference": 版本,
            "oracle_sha256": hashlib.sha256(工具.read_bytes()).hexdigest(),
            "archives": [],
            "status": "running",
            "scope": "all entries and FLC decode; first/last SPR/SMP/FLC frames with origins/masks",
        }
        开始 = time.monotonic()
        try:
            for 名称 in [
                "Data.mkf",
                "Effect.mkf",
                "Panel.mkf",
                "Speaking.mkf",
                "help.mkf",
                "jump.mkf",
                "map.mkf",
            ]:
                文件 = arg_素材 / 名称
                包 = 资源包_类(文件)
                项目: dict = {
                    "archive": 名称,
                    "input_sha256": hashlib.sha256(文件.read_bytes()).hexdigest(),
                    "entries": [],
                    "frames_compared": 0,
                    "flc_frames_compared": 0,
                    "flc_frames_decoded": 0,
                }
                报告["archives"].append(项目)
                with tempfile.TemporaryDirectory(prefix="rich4-diff-") as 临时:
                    输出 = Path(临时)
                    subprocess.run([str(工具), str(文件), 临时], check=True, capture_output=True)
                    for 索引 in range(len(包.条目)):
                        python = 包.api_解码(索引)
                        cpp = (输出 / f"{索引}.bin").read_bytes()
                        if python != cpp:
                            raise ValueError(f"{名称}:{索引} 解码字节不同")
                        项目["entries"].append(
                            {
                                "index": 索引,
                                "bytes": len(python),
                                "sha256": hashlib.sha256(python).hexdigest(),
                            }
                        )
                        if python[:4] in (b"SPR\0", b"SMP\0"):
                            数量 = int.from_bytes(python[4:8], "little")
                            for 帧 in sorted({0, 数量 - 1}) if 数量 else []:
                                图 = 图像_类.api_解码(python, 帧)
                                路径 = 输出 / f"{索引}-{帧}.ppm"
                                if 图.api_PPM() != 路径.read_bytes():
                                    raise ValueError(f"{名称}:{索引}:{帧} PPM 像素不同")
                                自检 = struct.pack(
                                    "<4iI", 图.宽, 图.高, 图.原点x, 图.原点y, len(图.不透明)
                                )
                                自检 += struct.pack(f"<{len(图.像素)}H", *图.像素) + 图.不透明
                                if 自检 != (输出 / f"{索引}-{帧}.image").read_bytes():
                                    raise ValueError(f"{名称}:{索引}:{帧} 原点/掩码/原像素不同")
                                项目["frames_compared"] += 1
                        elif len(python) >= 128 and python[4:6] == b"\x12\xaf":
                            动画 = 动画_类(python)
                            while 动画.api_下一帧():
                                项目["flc_frames_decoded"] += 1
                                帧 = 动画.已解帧 - 1
                                if 帧 != 0 and 帧 + 1 != 动画.帧数:
                                    continue
                                图 = 动画.api_图像()
                                自检 = struct.pack(
                                    "<4iI", 图.宽, 图.高, 图.原点x, 图.原点y, len(图.不透明)
                                )
                                自检 += struct.pack(f"<{len(图.像素)}H", *图.像素) + 图.不透明
                                if 自检 != (输出 / f"{索引}-flc-{帧}.image").read_bytes():
                                    raise ValueError(f"{名称}:{索引}:FLC:{帧} 差分失败")
                                项目["flc_frames_compared"] += 1
                            if 动画.已解帧 != 动画.帧数:
                                raise ValueError(f"{名称}:{索引} FLC 帧不完整")
                print(
                    f"[完成] {名称}：{len(包.条目)} 条目、{项目['frames_compared']} 帧一致。",
                    flush=True,
                )
            报告["status"] = "passed"
        except (ValueError, OSError, subprocess.CalledProcessError) as 错误:
            报告["status"] = "failed"
            报告["error"] = str(错误)
            raise
        finally:
            报告["elapsed_seconds"] = round(time.monotonic() - 开始, 3)
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    资源差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.report)
