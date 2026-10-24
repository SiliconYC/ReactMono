# ◑ 导入
import json
import os
import subprocess
import sys
import time
from array import array
from pathlib import Path

import pytest


# ◕ 功能
@pytest.mark.assets
def test_真实回调缓冲暂停退出与原声音(tmp_path: Path) -> None:
    names = (
        "RICH4_TEST_ASSETS",
        "RICH4_SDL3_LIBRARY",
        "RICH4_FLUIDSYNTH_LIBRARY",
        "RICH4_SOUNDFONT",
    )
    if not all(os.environ.get(n) for n in names):
        pytest.skip("需显式外部声音/MIDI、SDL3、FluidSynth和音库")
    tool = Path(__file__).parents[1] / "tools/probe_game_audio.py"
    subprocess.run(
        [
            sys.executable,
            str(tool),
            "--assets",
            os.environ[names[0]],
            "--driver",
            "dummy",
            "--output",
            str(tmp_path),
        ],
        check=True,
        capture_output=True,
        timeout=30,
    )
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["status"] == "passed"
    assert report["statistics"]["效果启动"] == 19
    assert report["statistics"]["语音启动"] == 3
    assert report["callback_blocks"] > 100 and report["bank_available"]
    assert report["captured_frames"] == report["statistics"]["渲染帧"]
    assert report["callback_independent_progress_pass"]
    assert len(report["no_main_update_window_frames"]) == 4
    assert all(n > 0 for n in report["no_main_update_window_frames"])


@pytest.mark.assets
def test_dummy慢回调仍独立推进且真实性能失败不能被掩盖(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import importlib.util

    from rich4.device_audio import 设备音频_类

    if not all(os.environ.get(n) for n in (
        "RICH4_TEST_OPEN_ASSETS", "RICH4_SDL3_LIBRARY", "RICH4_FLUIDSYNTH_LIBRARY",
    )):
        pytest.skip("需项目内真实声音/MIDI/音库和标准运行库")
    tool = Path(__file__).parents[1] / "tools/probe_game_audio.py"
    spec = importlib.util.spec_from_file_location("game_audio_probe_test", tool)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    original = 设备音频_类.api_渲染块

    def 慢回调(self: 设备音频_类, arg_音乐: array | None = None) -> array:
        # 只注入调度延迟，实际PCM/MIDI与原音量、队列和采样一个也不替换。
        time.sleep(0.02)
        return original(self, arg_音乐)

    with monkeypatch.context() as local:
        local.setattr(设备音频_类, "api_渲染块", 慢回调)
        module.游戏音频探针_类.api_执行(
            Path(os.environ["RICH4_TEST_OPEN_ASSETS"]), "dummy", tmp_path
        )
    report = json.loads((tmp_path / "report.json").read_text())
    assert report["status"] == "passed" and report["callback_independent_progress_pass"]
    assert all(n > 0 for n in report["no_main_update_window_frames"])
    assert report["dummy_nominal_rate_80_percent_pass"] is False
    assert report["real_time_budget_pass"] is False
    assert report["statistics"]["超时次数"] > 0
    assert report["captured_frames"] == report["statistics"]["渲染帧"]
