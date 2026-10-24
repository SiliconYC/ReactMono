# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import random
import shlex
import subprocess
import sys
from array import array
from pathlib import Path

from rich4.audio_capture import 音频捕获_类


# ◕ 功能
class 捕获差分_类:
    """
    直接原60秒限长/PCM16文件逐字节对照，合成数值只用于格式测试。

    更新日志：
    2026.10.24 - 覆盖远零取整边界和超过60秒；不把合成样本当正式声音。
    """

    @staticmethod
    def api_执行(
        arg_源码: Path,
        arg_构建: Path,
        arg_库: Path,
        arg_报告: Path,
    ) -> None:
        ref = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if ref != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本不符")
        subprocess.run(["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"], check=True)
        flags = shlex.split(
            subprocess.check_output(
                ["pkg-config", "--cflags", "--libs", "sdl3", "fluidsynth"], text=True
            )
        )
        tool = arg_构建.resolve() / "capture-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("capture_oracle.cpp")),
                str(arg_构建.resolve() / "librich4_core.a"),
                *flags,
                "-Wl,-rpath," + str(arg_库.resolve().parent),
                "-o",
                str(tool),
            ],
            check=True,
        )
        rng = random.Random(20261024)
        data = array("f", [0, -0.0, -2, -1, 1, 2])
        data.extend(v / 65534 for v in (-65533, -32767, -3, -1, 1, 3, 32767, 65533))
        data.extend(rng.uniform(-1.5, 1.5) for _ in range(100000))
        cases = [
            array("f"),
            data[:2],
            data[:17],
            data,
            data + array("f", [0.1234567]) * (48000 * 2 * 60),
        ]
        report = {
            "reference": ref,
            "status": "running",
            "scope": "synthetic float capture "
            "format and 60-second cap only; exact original WAV bytes, no listening proof",
            "cases": [],
            "runtime_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/audio_capture.py").read_bytes()
            ).hexdigest(),
        }
        try:
            for i, pcm in enumerate(cases):
                cpp, py = arg_构建 / f"capture-cpp-{i}.wav", arg_构建 / f"capture-py-{i}.wav"
                raw = array("f", pcm)
                if sys.byteorder != "little":
                    raw.byteswap()
                subprocess.run([str(tool), str(cpp)], input=raw.tobytes(), check=True)
                capture = 音频捕获_类(py)
                for start in range(0, len(pcm), 1024):
                    capture.api_追加(pcm[start : start + 1024])
                capture.api_写出()
                if cpp.read_bytes() != py.read_bytes():
                    raise ValueError(f"捕获{i}的原WAV字节不同")
                report["cases"].append(
                    {
                        "samples": len(pcm),
                        "retained": capture.数量,
                        "bytes": py.stat().st_size,
                        "sha256": hashlib.sha256(py.read_bytes()).hexdigest(),
                    }
                )
            report["status"] = "passed"
        except (ValueError, OSError) as error:
            report.update(status="failed", failure=str(error))
            raise
        finally:
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(report))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for key in ("source", "build", "library", "report"):
        参数.add_argument("--" + key, type=Path, required=True)
    选项 = 参数.parse_args()
    捕获差分_类.api_执行(选项.source, 选项.build, 选项.library, 选项.report)
