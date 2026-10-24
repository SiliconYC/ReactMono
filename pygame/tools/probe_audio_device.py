# SPDX-License-Identifier: GPL-3.0-or-later
# 只验证设备契约；零样本不是正式游戏音频，也不算波形/听感验收。
# ◑ 导入
import argparse
import json
import os
import time
from pathlib import Path

from pygame._sdl2 import audio, sdl2


# ◕ 功能
class 音频设备探针_类:
    """
    Pygame原生SDL2 F32回调能力的独立进程探针。

    更新日志：
    2026.10.24 - 记录实际块大小；不把dummy成功说成真实音频播放。
    """

    @staticmethod
    def api_执行(arg_驱动: str, arg_报告: Path) -> None:
        os.environ["SDL_AUDIODRIVER"] = arg_驱动
        sdl2.init_subsystem(sdl2.INIT_AUDIO)
        sizes: list[int] = []

        def 回调(arg_设备: audio.AudioDevice, arg_缓存: memoryview) -> None:
            arg_缓存[:] = bytes(len(arg_缓存))
            sizes.append(len(arg_缓存))

        names = audio.get_audio_device_names(False)
        if not names:
            raise ValueError("没有Pygame音频输出设备")
        # 2.6.1绑定实际拒绝文档声称可用的None，显式选择已枚举的第一个设备。
        device = audio.AudioDevice(
            devicename=names[0],
            iscapture=False,
            frequency=48000,
            audioformat=audio.AUDIO_F32,
            numchannels=2,
            chunksize=512,
            allowed_changes=0,
            callback=回调,
        )
        try:
            device.pause(0)
            time.sleep(0.25)
            device.pause(1)
            report = {
                "status": "passed" if sizes and all(n == 4096 for n in sizes) else "failed",
                "scope": "zero PCM device-contract probe; no game audio/waveform/listening proof",
                "driver": arg_驱动,
                "callback_blocks": len(sizes),
                "bytes_per_block": sorted(set(sizes)),
                "frequency": device.frequency,
                "format": device.audioformat,
                "channels": device.numchannels,
            }
            arg_报告.parent.mkdir(parents=True, exist_ok=True)
            arg_报告.write_text(json.dumps(report, indent=2) + "\n")
            print(json.dumps(report))
            if report["status"] != "passed":
                raise ValueError("F32设备块契约不符")
        finally:
            device.close()


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--driver", default="dummy")
    参数.add_argument("--report", required=True, type=Path)
    选项 = 参数.parse_args()
    音频设备探针_类.api_执行(选项.driver, 选项.report)
