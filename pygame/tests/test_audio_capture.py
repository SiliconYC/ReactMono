# ◑ 导入
import struct
import wave
from array import array
from pathlib import Path

from rich4.audio_capture import 音频捕获_类


# ◕ 功能
def test_原F32乘法后远零取整及PCM16头(tmp_path: Path) -> None:
    path = tmp_path / "capture.wav"
    capture = 音频捕获_类(path)
    samples = array("f", [-2, -1, -0.5, 0, 0.5, 1, 2, 0])
    capture.api_追加(samples)
    capture.api_写出()
    with wave.open(str(path), "rb") as f:
        assert (f.getnchannels(), f.getsampwidth(), f.getframerate()) == (2, 2, 48000)
        assert f.getnframes() == 4
        assert struct.unpack("<8h", f.readframes(4)) == (
            -32767,
            -32767,
            -16384,
            0,
            16384,
            32767,
            32767,
            0,
        )


def test_六十秒上限不增长缓存(tmp_path: Path) -> None:
    capture = 音频捕获_类(tmp_path / "limit.wav")
    size = len(capture._样本)
    block = array("f", [0.125]) * (size - 2)
    capture.api_追加(block)
    capture.api_追加(array("f", [0.25, -0.25, 1, -1]))
    assert capture.数量 == size == 48000 * 2 * 60
    assert len(capture._样本) == size
    assert capture._样本[-2:] == array("f", [0.25, -0.25])


def test_未配置捕获不分配录音缓存() -> None:
    capture = 音频捕获_类(None)
    capture.api_追加(array("f", [1, -1]))
    capture.api_写出()
    assert capture.数量 == 0 and not capture._样本
