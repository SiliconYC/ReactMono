# ◑ 导入
import os
from pathlib import Path

import pytest

from rich4.audio_types import 音乐_类
from rich4.midi_player import MIDI播放器_类


# ◕ 功能
def test_缺音库保持原音乐栈与静音契约(tmp_path: Path) -> None:
    p = MIDI播放器_类(tmp_path, tmp_path / "missing.sf2")
    trace = []
    p.api_追踪(lambda a, b: trace.append((a, b)))
    assert not p.可用 and p.诊断
    assert p.api_文件() == "rich08.mid"
    p.api_推音乐(音乐_类.银行)
    p.api_换音乐(音乐_类.商店)
    assert p.上下文 == 音乐_类.商店 and len(p._栈) == 1
    p.api_推音乐(音乐_类.静音)
    assert p.api_文件() == "silence" and p.api_渲染块() is None
    p.api_弹音乐()
    p.api_弹音乐()
    p.api_弹音乐()
    assert p.上下文 is None and p.曲目 == 1
    p.api_选音乐(0)
    assert p.曲目 == 2 and p.api_文件() == "rich16.mid"
    with pytest.raises(ValueError):
        p.api_选音乐(9)
    p.api_音乐开关(False)
    p.api_音乐开关(False)
    assert trace[-1] == ("music_enabled", "off")
    assert trace.count(("music_enabled", "off")) == 1
    p.api_关闭()


@pytest.mark.assets
def test_真实MIDI静音暂停与延后恢复() -> None:
    names = ("RICH4_TEST_ASSETS", "RICH4_FLUIDSYNTH_LIBRARY", "RICH4_SOUNDFONT")
    if not all(os.environ.get(n) for n in names):
        pytest.skip("需要显式外部MIDI、FluidSynth与音库")
    p = MIDI播放器_类(Path(os.environ[names[0]]))
    try:
        assert p.可用 and p._合成 is not None
        samples = [p.api_渲染块() for _ in range(128)]
        assert any(s is not None and any(abs(v) > 0.000001 for v in s) for s in samples)
        tick = p.api_时刻()
        assert tick > 0
        p.api_音乐开关(False)
        assert p.api_渲染块() is None and p.api_时刻() == tick
        p.api_推音乐(音乐_类.银行)
        assert p._过期 and p.api_时刻() == 0
        p.api_弹音乐()
        assert p._过期 and p.api_时刻() == tick
        p.api_音乐开关(True)
        for _ in range(4):
            p.api_渲染块()
        # 原版先play后seek，新播放器文件尚未加载、total_ticks为0，seek失败被忽略。
        assert not p._过期 and 0 < p.api_时刻() < tick
        p.api_推音乐(音乐_类.静音)
        assert p.api_渲染块() is None
        p.api_选音乐(8)
        assert not p._栈 and p.上下文 is None and p.曲目 == 8
    finally:
        p.api_关闭()


def test_全禁用不读任何素材或SDK(tmp_path: Path) -> None:
    from rich4.audio import 音频_类

    p = 音频_类(tmp_path / 'not-an-asset-directory', False)
    try:
        assert not p.启用 and not p.api_音乐可用() and not p.诊断
        p.api_推音乐(音乐_类.银行)
        p.api_换音乐(音乐_类.静音)
        p.api_音乐开关(False)
        p.api_选音乐(0)
        p.api_弹音乐()
        assert p.api_音乐曲目() == 2 and p.api_音乐深度() == 0
        assert p.api_语音(9999) == 0
        p.api_播音(9999)
    finally:
        p.api_关闭()
