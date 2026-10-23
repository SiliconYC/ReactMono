# ◑ 导入
import argparse
import hashlib
import json
import subprocess
import tempfile
from pathlib import Path

from rich4.graphics import 图像_类


# ◕ 功能
class 颜色差分_类:
    """
    穷举原16位色域，对照固定C++转换；SPR掩码透明另外按图形接口测试。

    更新日志：
    2026.10.23 - 验证查表优化不改变555→565→RGB888整数缩放。
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
        工具 = arg_构建.resolve() / "color-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                str(Path(__file__).with_name("color_oracle.cpp")),
                str(arg_构建 / "librich4_core.a"),
                "-o",
                str(工具),
            ],
            check=True,
            capture_output=True,
        )
        报告 = {
            "reference": 版本,
            "status": "running",
            "scope": "all uint16 opaque RGB555 conversions; alpha mask contract tested separately",
        }
        try:
            with tempfile.TemporaryDirectory(prefix="rich4-color-") as 临时:
                路径 = Path(临时) / "colors.bin"
                subprocess.run([str(工具), str(路径)], check=True, capture_output=True)
                输出 = 图像_类(256, 256, list(range(65536))).api_RGBA()
                if 输出 != 路径.read_bytes():
                    raise ValueError("16位颜色穷举与C++不同")
                报告.update(
                    status="passed",
                    cases=65536,
                    bytes=len(输出),
                    output_sha256=hashlib.sha256(输出).hexdigest(),
                )
        except (ValueError, OSError, subprocess.CalledProcessError) as 错误:
            报告.update(status="failed", error=str(错误))
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(报告, ensure_ascii=False, indent=2) + "\n")
        print("[完成] 全65536个原16位颜色与C++一致。")


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--source", type=Path, required=True)
    参数.add_argument("--build", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    颜色差分_类.api_执行(选项.source, 选项.build, 选项.report)
