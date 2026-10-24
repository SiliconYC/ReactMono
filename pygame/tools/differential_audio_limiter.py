# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import struct
import subprocess
import sys
from array import array
from pathlib import Path

from rich4.audio_limiter import 限幅器_类


# ◕ 功能
class 限幅差分_类:
    """
    原限幅器逐样本位模式、内部包络和释放系数对照。

    更新日志：
    2026.10.24 - 数值夹具不是商业音频，结果不当作真实WAV或听感通过。
    """

    @staticmethod
    def _位(arg_浮: float) -> int:
        return struct.unpack("<I", struct.pack("<f", arg_浮))[0]

    @staticmethod
    def _浮(arg_位: int) -> float:
        return struct.unpack("<f", struct.pack("<I", arg_位))[0]

    @classmethod
    def _命令(cls) -> list[tuple[str, bytes]]:
        commands = []
        seed = 1
        for rate in (0.0, 44100.0, 48000.0, 96000.0):
            for ceiling in (0.5, 0.891251, 1.0):
                for release in (0.0, 150.0):
                    commands.append(
                        (f"N {cls._位(rate)} {cls._位(ceiling)} {cls._位(release)}", b"")
                    )
                    patterns = [
                        [],
                        [0],
                        [0, 0x80000000],
                        [0x7FC01234, 0x7F800000, 0xFF800000],
                        [0x7F800001, 1, 0x80000001, 0],
                        [cls._位(v) for v in (ceiling, -ceiling, ceiling * 2, -ceiling / 2)],
                        [0x7F7FFFFF, 0xFF7FFFFF, 0, 0],
                    ]
                    for words in patterns:
                        commands.append((f"B {len(words)}", struct.pack(f"<{len(words)}I", *words)))
                    for _ in range(64):
                        words = []
                        for _ in range(1024):
                            seed = (1664525 * seed + 1013904223) & 0xFFFFFFFF
                            words.append(cls._位(((seed >> 8) / 8388608 - 1) * 4))
                        commands.append(("B 1024", struct.pack("<1024I", *words)))
                    commands += [("B 1024", bytes(4096))] * 32
        return commands

    @classmethod
    def api_执行(cls, arg_源码: Path, arg_构建: Path, arg_报告: Path) -> None:
        ref = subprocess.check_output(
            ["git", "-C", str(arg_源码), "rev-parse", "HEAD"], text=True
        ).strip()
        if ref != "3f4209a7dfb5b2f20799bf54e6c03c5faa11c557":
            raise ValueError("参考版本不符")
        subprocess.run(
            ["git", "-C", str(arg_源码), "diff", "--exit-code", "HEAD"],
            check=True,
            capture_output=True,
        )
        tool = arg_构建.resolve() / "audio-limiter-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-fno-access-control",
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("limiter_oracle.cpp")),
                "-o",
                str(tool),
            ],
            check=True,
        )
        proc = subprocess.Popen(
            [str(tool)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        own, digest, inputs = 限幅器_类(48000), hashlib.sha256(), hashlib.sha256()
        report = {
            "reference": ref,
            "status": "running",
            "commands": 0,
            "samples": 0,
            "scope": (
                "direct original Limiter: exact float32 sample/private-state bits; "
                "numeric signals only, not real audio playback"
            ),
            "runtime_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/audio_limiter.py").read_bytes()
            ).hexdigest(),
        }
        try:
            for index, (line, raw) in enumerate(cls._命令()):
                report.update(last_index=index, last_command=line)
                proc.stdin.write((line + "\n").encode() + raw)
                proc.stdin.flush()
                actual = proc.stdout.readline().decode().strip()
                if not actual:
                    raise ValueError("原限幅器提前结束：" + proc.stderr.read().decode())
                cpp = proc.stdout.read(int(actual.split()[-1]) * 4)
                op, *args = line.split()
                data = array("f")
                limited = 0
                if op == "N":
                    own = 限幅器_类(*map(cls._浮, map(int, args)))
                else:
                    data.frombytes(raw)
                    if sys.byteorder != "little":
                        data.byteswap()
                    limited = own.api_处理(data)
                expected = [
                    limited,
                    cls._位(own._上限),
                    cls._位(own._释放),
                    cls._位(own._包络),
                    cls._位(own.api_增益()),
                    len(data),
                ]
                if " ".join(map(str, expected)) != actual:
                    report.update(cpp=actual, python=expected)
                    raise ValueError(f"step={index} 限幅内部状态不同")
                if sys.byteorder != "little":
                    data.byteswap()
                if cpp != data.tobytes():
                    offset = next(i for i, (a, b) in enumerate(zip(cpp, data.tobytes())) if a != b)
                    raise ValueError(f"step={index} sample={offset // 4} 采样位不同")
                digest.update(actual.encode())
                digest.update(cpp)
                inputs.update((line + "\n").encode() + raw)
                report["commands"], report["samples"] = index + 1, report["samples"] + len(data)
            proc.stdin.close()
            if proc.wait():
                raise ValueError("原限幅器退出故障：" + proc.stderr.read().decode())
            report.update(
                status="passed", state_sha256=digest.hexdigest(), input_sha256=inputs.hexdigest()
            )
        except (ValueError, IndexError, OSError) as error:
            report.update(status="failed", failure=str(error))
            raise
        finally:
            if proc.poll() is None:
                proc.terminate()
                proc.wait()
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(report))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    for key in ("source", "build", "report"):
        参数.add_argument("--" + key, type=Path, required=True)
    选项 = 参数.parse_args()
    限幅差分_类.api_执行(选项.source, 选项.build, 选项.report)
