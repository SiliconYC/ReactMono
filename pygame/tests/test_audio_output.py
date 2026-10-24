# ◑ 导入
import os
import subprocess
import sys

import pytest


# ◕ 功能
@pytest.mark.parametrize("arg_设备名称", (None, "System audio output device"))
def test_实际SDL默认或指定输出设备供料与关闭(arg_设备名称: str | None) -> None:
    script = """
import time
from array import array
from threading import RLock
from rich4.audio_capture import 音频捕获_类
from rich4.audio_device import 音频设备_类
from rich4.audio_feed import 设备供料_类
from rich4.audio_pcm_types import PCM统计_类
feed = 设备供料_类(lambda: array('f', [0.125] * 1024), PCM统计_类(), RLock(), 音频捕获_类(None))
device = 音频设备_类(feed, arg_设备名称=DEVICE)
try:
    time.sleep(0.12)
    device.api_暂停(True)
    device.api_检查()
    assert feed.回调次数 > 0
    assert device.api_格式() == (48000, 33056, 2, 512)
finally:
    device.api_关闭()
    device.api_关闭()
""".replace("DEVICE", repr(arg_设备名称))
    env = {**os.environ, "SDL_AUDIODRIVER": "dummy"}
    result = subprocess.run(
        [sys.executable, "-c", script], capture_output=True, text=True, env=env, timeout=15
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_不存在的实际输出明确失败不选择其它设备() -> None:
    script = """
from array import array
from threading import RLock
import pygame
from rich4.audio_capture import 音频捕获_类
from rich4.audio_device import 音频设备_类
from rich4.audio_feed import 设备供料_类
from rich4.audio_pcm_types import PCM统计_类
feed = 设备供料_类(lambda: array('f', [0.] * 1024), PCM统计_类(), RLock(), 音频捕获_类(None))
try:
    音频设备_类(feed, arg_设备名称='not-an-output-device')
except pygame.error:
    print('invalid-device-rejected')
else:
    raise ValueError('无效输出被静默换成其它设备')
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env={**os.environ, "SDL_AUDIODRIVER": "dummy"},
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "invalid-device-rejected" in result.stdout


def test_实际SDL回调错误经主线程重新抛出且可关闭() -> None:
    script = """
import time
from array import array
from threading import RLock
from rich4.audio_capture import 音频捕获_类
from rich4.audio_device import 音频设备_类
from rich4.audio_feed import 设备供料_类
from rich4.audio_pcm_types import PCM统计_类

def fail() -> array:
    raise ValueError('injected-render-failure')

feed = 设备供料_类(fail, PCM统计_类(), RLock(), 音频捕获_类(None))
device = 音频设备_类(feed)
try:
    deadline = time.monotonic() + 2
    while True:
        try:
            device.api_检查()
        except RuntimeError as error:
            assert isinstance(error.__cause__, ValueError)
            assert str(error.__cause__) == 'injected-render-failure'
            break
        if time.monotonic() > deadline:
            raise ValueError('回调错误没有传回主线程')
        time.sleep(0.01)
finally:
    device.api_关闭()
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        env={**os.environ, "SDL_AUDIODRIVER": "dummy"},
        timeout=15,
    )
    assert result.returncode == 0, result.stdout + result.stderr
