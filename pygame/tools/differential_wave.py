# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import io
import json
import shlex
import subprocess
import sys
import wave
from pathlib import Path

from rich4.artwork import 美术_类
from rich4.wave_decoder import 原波形_类


# ◕ 功能
class 波形差分_类:
    """
    实际原decode_wave与Python的标准SDL3接口逐采样比较，输出只保留摘要。

    更新日志：
    2026.10.24 - 真实外部音效/全部语音、空条目/截断拒绝与合成PCM输入分开记录。
    """

    def __init__(self, arg_素材: Path, arg_库: Path) -> None:
        self.美术, self.波形 = 美术_类(arg_素材), 原波形_类(arg_库)

    def _命令(self) -> list[tuple[str, bytes]]:
        groups = []
        for lib in ("e", "s"):
            groups += [(f"W {lib} {n} -1", b"") for n in range(len(self.美术.api_包(lib).条目))]
        for lib, indexes in (("e", (0, 25, 26, 101)), ("s", (0, 127, 1050, 1373))):
            for n in indexes:
                data = self.美术.api_解码(lib, n)
                for cut in (0, 1, 4, 11, 12, 20, 43, 44, 100, max(len(data) - 1, 0)):
                    groups.append((f"W {lib} {n} {cut}", b""))
        for channels in (1, 2):
            for width in (1, 2, 3, 4):
                for rate in (8000, 11025, 22050, 44100, 48000):
                    stream = io.BytesIO()
                    with wave.open(stream, "wb") as f:
                        f.setnchannels(channels)
                        f.setsampwidth(width)
                        f.setframerate(rate)
                        f.writeframes(
                            bytes((i * 97 + i // 11) & 255 for i in range(128 * width * channels))
                        )
                    data = stream.getvalue()
                    groups.append((f"D {len(data)}", data))
        for data in (b"", b"x", b"RIFF", b"RIFF" + bytes(40)):
            groups.append((f"D {len(data)}", data))
        return groups

    @classmethod
    def api_执行(
        cls, arg_源码: Path, arg_构建: Path, arg_素材: Path, arg_库: Path, arg_报告: Path
    ) -> None:
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
        flags = shlex.split(
            subprocess.check_output(
                ["pkg-config", "--cflags", "--libs", "sdl3", "fluidsynth"], text=True
            )
        )
        versions = subprocess.check_output(
            ["pkg-config", "--modversion", "sdl3", "fluidsynth"], text=True
        ).splitlines()
        tool = arg_构建.resolve() / "wave-oracle"
        subprocess.run(
            [
                "c++",
                "-std=c++20",
                "-O2",
                "-I",
                str(arg_源码 / "include"),
                "-I",
                str(arg_源码 / "tools"),
                str(Path(__file__).with_name("wave_oracle.cpp")),
                str(arg_构建.resolve() / "librich4_core.a"),
                *flags,
                "-Wl,-rpath," + str(arg_库.resolve().parent),
                "-o",
                str(tool),
            ],
            check=True,
        )
        own, digest, inputs = cls(arg_素材, arg_库), hashlib.sha256(), hashlib.sha256()
        proc = subprocess.Popen(
            [str(tool), str(arg_素材)],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        report = {
            "reference": ref,
            "status": "running",
            "commands": 0,
            "samples": 0,
            "accepted": 0,
            "rejected": 0,
            "full_wave_accepted": 0,
            "libraries": versions,
            "python_sdl3_version": own.波形.版本,
            "scope": (
                "actual original decode_wave vs independent Python SDL3 binding; "
                "real external WAV and synthetic PCM/truncation; exact F32 samples, "
                "not mixer/device/listening proof"
            ),
            "runtime_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/wave_decoder.py").read_bytes()
            ).hexdigest(),
        }
        try:
            for index, (line, raw) in enumerate(own._命令()):
                report.update(last_index=index, last_command=line)
                proc.stdin.write((line + "\n").encode() + raw)
                proc.stdin.flush()
                actual = proc.stdout.readline().decode().strip()
                if not actual:
                    raise ValueError("原波形转换提前结束：" + proc.stderr.read().decode())
                ok, count = map(int, actual.split())
                cpp = proc.stdout.read(count * 4)
                if len(cpp) != count * 4:
                    raise ValueError("原波形采样输出截断")
                op, *args = line.split()
                if op == "W":
                    lib, n, cut = args
                    raw = own.美术.api_解码(lib, int(n))
                    if int(cut) >= 0:
                        raw = raw[: int(cut)]
                    elif raw.startswith(b"RIFF"):
                        if not ok:
                            raise ValueError(f"原有效WAV未成功转换：{line}")
                        report["full_wave_accepted"] += 1
                success, py = True, b""
                try:
                    samples = own.波形.api_解码(raw)
                    if sys.byteorder != "little":
                        samples.byteswap()
                    py = samples.tobytes()
                except ValueError:
                    success = False
                if success != bool(ok) or cpp != py:
                    report.update(
                        cpp_success=ok,
                        python_success=success,
                        cpp_bytes=len(cpp),
                        python_bytes=len(py),
                    )
                    if success and ok:
                        offset = next((i for i, (a, b) in enumerate(zip(cpp, py)) if a != b), -1)
                        report["first_sample_difference"] = offset // 4
                    raise ValueError(f"step={index} WAV转换不同")
                digest.update(actual.encode())
                digest.update(cpp)
                inputs.update((line + "\n").encode() + raw)
                report["commands"] = index + 1
                report["samples"] += count
                report["accepted" if ok else "rejected"] += 1
            proc.stdin.close()
            code, error = proc.wait(), proc.stderr.read().decode()
            if code or error:
                raise ValueError("原波形退出故障：" + error)
            report.update(
                status="passed", state_sha256=digest.hexdigest(), input_sha256=inputs.hexdigest()
            )
        except (ValueError, IndexError, AttributeError, OSError) as error:
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
    for key in ("source", "build", "assets", "library", "report"):
        参数.add_argument("--" + key, type=Path, required=True)
    选项 = 参数.parse_args()
    波形差分_类.api_执行(选项.source, 选项.build, 选项.assets, 选项.library, 选项.report)
