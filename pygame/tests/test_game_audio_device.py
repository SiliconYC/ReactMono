# ◑ 导入
import json
import os
import subprocess
import sys
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
