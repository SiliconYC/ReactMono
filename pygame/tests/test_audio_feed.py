# ◑ 导入
from array import array
from threading import RLock

from rich4.audio_capture import 音频捕获_类
from rich4.audio_feed import 设备供料_类
from rich4.audio_pcm import PCM混音_类


# ◕ 功能
def test_不整块设备请求保留整块余量且不提前续语音() -> None:
    core = PCM混音_类()
    core.api_起音(array("f", [0.1, -0.2]), True)
    core.api_排语音(1, array("f", [0.3, -0.4]))
    feed = 设备供料_类(core.api_混合, core._统计, RLock(), 音频捕获_类(None))
    parts = []
    for size in (136, 3960, 4096):
        buffer = bytearray(size)
        feed.api_填充(memoryview(buffer))
        parts.append(bytes(buffer))
    output = array("f")
    output.frombytes(b"".join(parts))
    assert len(output) == 2048 and core._统计.渲染帧 == 1024
    assert output[0] > 0 and output[1] < 0
    assert not any(output[2:1024])
    assert output[1024] > output[0] and output[1025] < output[1]
    assert not any(output[1026:])
    assert feed.余量 == 0


def test_真实预算计数和拒绝非帧对齐缓冲() -> None:
    import pytest

    core = PCM混音_类()
    clock = iter((0, 20000000))
    feed = 设备供料_类(core.api_混合, core._统计, RLock(), 音频捕获_类(None), lambda: next(clock))
    feed.api_填充(memoryview(bytearray(4096)))
    assert (core._统计.超时次数, core._统计.饥饿毫秒, core._统计.最长渲染微秒) == (1, 9, 20000)
    with pytest.raises(ValueError):
        feed.api_填充(memoryview(bytearray(7)))
