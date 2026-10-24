# SPDX-License-Identifier: GPL-3.0-or-later
# ◑ 导入
import argparse
import hashlib
import json
import os
import time
import wave
from dataclasses import asdict
from pathlib import Path

import pygame

from rich4.audio_types import 循环通道_类, 音乐_类
from rich4.device_audio import 设备音频_类


# ◕ 功能
class 游戏音频探针_类:
    """
    实际Pygame设备持续播放外部原声音、MIDI和上下文；保留真实性能/捕获证据。

    更新日志：
    2026.10.24 - 主线程暂停一秒也要求设备推进；不声称真人听感或完整游戏通过。
    2026.10.25 - dummy是回调后再等待的软件时钟；连续推进与原80%吞吐/真实预算分开记录。
    """

    @staticmethod
    def api_执行(
        arg_素材: Path,
        arg_驱动: str,
        arg_输出: Path,
    ) -> None:
        os.environ["SDL_AUDIODRIVER"] = arg_驱动
        arg_输出.mkdir(parents=True, exist_ok=True)
        capture = arg_输出 / "device.wav"
        report = {
            "status": "running",
            "driver": arg_驱动,
            "scope": "real original PCM/MIDI through Pygame callback; capture and timing; "
            "no human listening or full application proof",
            "trace": [],
        }
        player: 设备音频_类 | None = None
        try:
            player = 设备音频_类(arg_素材, arg_捕获=capture)
            player.api_追踪(lambda a, b: report["trace"].append([a, b]))
            if not player.api_音乐可用():
                raise ValueError("实际MIDI探针需要可用外部音库：" + player.诊断)
            begin = time.monotonic()
            events = [
                (0.05, lambda: player.api_播音(0)),
                (0.25, lambda: player.api_语音(127)),
                (0.5, lambda: player.api_排语音(128)),
                (0.75, lambda: player.api_播循环(44, 循环通道_类.步行)),
                (1, lambda: player.api_播循环(32, 循环通道_类.炸弹)),
                (1.25, lambda: player.api_推音乐(音乐_类.银行)),
                (1.75, lambda: player.api_换音乐(音乐_类.商店)),
                (2.25, player.api_弹音乐),
                (2.5, lambda: player.api_音乐开关(False)),
                (2.75, lambda: player.api_选音乐(8)),
                (3, lambda: player.api_音乐开关(True)),
                (3.25, player.api_停全部循环),
            ]
            position = 0
            while time.monotonic() - begin < 3.75:
                now = time.monotonic() - begin
                while position < len(events) and now >= events[position][0]:
                    events[position][1]()
                    position += 1
                player.api_更新()
                time.sleep(0.005)
            before = player.api_统计().渲染帧
            last, windows = before, []
            quiet_begin = time.monotonic()
            for _ in range(4):
                time.sleep(0.25)
                after = player.api_统计().渲染帧
                windows.append(after - last)
                last = after
            quiet_seconds = time.monotonic() - quiet_begin
            report["main_thread_one_second_sleep_audio_frames"] = after - before
            report["no_main_update_window_frames"] = windows
            report["no_main_update_elapsed_seconds"] = quiet_seconds
            independent = all(n > 0 for n in windows)
            nominal = after - before >= 48000 * quiet_seconds * 0.8
            report["callback_independent_progress_pass"] = independent
            report["dummy_nominal_rate_80_percent_pass"] = nominal if arg_驱动 == "dummy" else None
            report["hardware_nominal_rate_80_percent_pass"] = (
                nominal if arg_驱动 != "dummy" else None
            )
            if not independent:
                raise ValueError("主线程不更新时音频回调停止推进")
            # SDL2 dummy每次callback之后再SDL_Delay一个缓冲周期，不能拿它冒充硬件时钟。
            # 原80%指标和所有超预算统计仍保留；真实设备继续把80%作为失败门槛。
            if arg_驱动 != "dummy" and not nominal:
                raise ValueError("真实设备在主线程不更新时未达到80%名义采样推进")
            # 真实解码后在不释放GIL的普通Python忙循环中观测调度，计数不决定通过。
            before_busy = player.api_统计().渲染帧
            busy_end = time.monotonic() + 1
            work = 0
            while time.monotonic() < busy_end:
                work = (work + 1) & 0xFFFFFFFF
            report["main_thread_one_second_busy_audio_frames"] = (
                player.api_统计().渲染帧 - before_busy
            )
            player.api_更新()
            player.api_角色声音(0, 0)
            for _ in range(16):
                player.api_播音(0)
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                player.api_更新()
                time.sleep(0.005)
            player.api_暂停设备(True)
            player.api_更新()
            report.update(
                statistics=asdict(player.api_统计()),
                real_time_budget_pass=player.api_统计().超时次数 == 0,
                callback_blocks=player._供料.回调次数,
                elapsed_seconds=time.monotonic() - begin,
                pygame_version=pygame.version.ver,
                sdl_version=pygame.get_sdl_version(),
                device_format={
                    k: v
                    for k, v in zip(
                        ("frequency", "format", "channels", "frames"),
                        player._设备.api_格式(),
                        strict=True,
                    )
                },
                archive_loader_done=player._档案._任务.done(),
                bank_available=player.api_音乐可用(),
                output_device=player._设备.设备名称,
                default_output=player._设备.设备名称 is None,
                runtime_sha256={
                    n: hashlib.sha256(
                        Path(__file__).parents[1].joinpath("src/rich4", n).read_bytes()
                    ).hexdigest()
                    for n in (
                        "device_audio.py",
                        "audio_device.py",
                        "audio_sdl.py",
                        "audio_feed.py",
                        "audio_archives.py",
                        "audio_capture.py",
                        "audio_pcm.py",
                        "audio.py",
                        "audio_player.py",
                        "audio_limiter.py",
                        "wave_decoder.py",
                        "midi_player.py",
                        "fluid_synth.py",
                    )
                },
            )
            player.api_关闭()
            with wave.open(str(capture), "rb") as audio:
                report["captured_frames"] = audio.getnframes()
                if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) != (
                    2,
                    2,
                    48000,
                ):
                    raise ValueError("设备捕获WAV格式错误")
                if audio.getnframes() * 2 != player._捕获.数量:
                    raise ValueError("设备捕获采样数不符")
            if player.api_统计().非零采样 == 0 or player.api_统计().语音启动 < 2:
                raise ValueError("设备没有播放实际声音")
            report.update(
                status="passed", capture_sha256=hashlib.sha256(capture.read_bytes()).hexdigest()
            )
        except (ValueError, RuntimeError, pygame.error) as error:
            report.update(status="failed", failure=str(error))
            raise
        finally:
            if player is not None:
                report["final_statistics"] = asdict(player.api_统计())
                report["final_callback_blocks"] = player._供料.回调次数
                player.api_关闭()
            pygame.quit()
            (arg_输出 / "report.json").write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n"
            )
        print(json.dumps(report, ensure_ascii=False))


# ◍ 运行
if __name__ == "__main__":
    参数 = argparse.ArgumentParser()
    参数.add_argument("--assets", type=Path, required=True)
    参数.add_argument("--driver", default="dummy")
    参数.add_argument("--output", type=Path, required=True)
    选项 = 参数.parse_args()
    游戏音频探针_类.api_执行(选项.assets, 选项.driver, 选项.output)
