# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import ctypes as c
import ctypes.util
import hashlib
import json
import statistics
import time
from pathlib import Path

from rich4.audio_pcm import PCM混音_类
from rich4.audio_player import PCM播放器_类


# ◕ 功能
class 音频性能_类:
    """
    同一真实Effect0的16效果重叠夹具，对照标准FMA的GIL策略；不作正式FPS结论。

    更新日志：
    2026.10.24 - 候选采样摘要也必须一致，原类绑定在测试后恢复。
    """

    @staticmethod
    def api_执行(arg_素材: Path, arg_报告: Path) -> None:
        player = PCM播放器_类(arg_素材)
        pcm = player._载入(False, 0)
        original = PCM混音_类._融合
        report = {
            "scope": "real Effect0, explicit 16-overlap offline fixture; not full game FPS",
            "runtime_sha256": hashlib.sha256(
                Path(__file__).parents[1].joinpath("src/rich4/audio_pcm.py").read_bytes()
            ).hexdigest(),
            "cases": {},
        }
        try:
            for cls in (c.CDLL, c.PyDLL):
                lib = cls(ctypes.util.find_library("m"))
                fused = lib.fmaf
                fused.argtypes, fused.restype = [c.c_float] * 3, c.c_float
                PCM混音_类._融合 = fused
                times, digest = [], hashlib.sha256()
                for _ in range(4):
                    core = PCM混音_类()
                    for _ in range(16):
                        core.api_起音(pcm, False)
                    for _ in range(8):
                        if len(core._片段) != 16:
                            raise ValueError("性能样本过短，未保持真实16效果重叠")
                        start = time.perf_counter_ns()
                        out = core.api_混合()
                        times.append((time.perf_counter_ns() - start) / 1000000)
                        digest.update(out.tobytes())
                report["cases"][cls.__name__] = {
                    "median_ms": statistics.median(times),
                    "max_ms": max(times),
                    "p95_ms": sorted(times)[int(len(times) * 0.95)],
                    "blocks": len(times),
                    "clip_samples": len(pcm),
                    "output_sha256": digest.hexdigest(),
                }
            if len({r["output_sha256"] for r in report["cases"].values()}) != 1:
                raise ValueError("FMA候选采样不同")
        finally:
            PCM混音_类._融合 = original
        arg_报告.parent.mkdir(parents=True, exist_ok=True)
        arg_报告.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps(report))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--report", type=Path, required=True)
    选项 = 参数.parse_args()
    音频性能_类.api_执行(选项.assets, 选项.report)
