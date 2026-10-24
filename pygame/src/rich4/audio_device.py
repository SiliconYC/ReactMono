# SPDX-License-Identifier: GPL-3.0-or-later
# Pygame同一SDL2库的公开音频接口；原SDL3设备供料语义见audio_feed.py。
# ◑ 导入
import ctypes as c

import pygame
from pygame._sdl2 import audio, sdl2

from rich4.audio_feed import 设备供料_类
from rich4.audio_sdl import SDL音频规格_类, 音频回调_型


# ◕ 功能
class 音频设备_类:
    """
    系统默认或明确指定的Pygame SDL2输出，保持48000Hz立体声F32。

    更新日志：
    2026.10.24 - 默认以NULL打开，不能把枚举首项冒充系统默认；CDLL暂停/关闭释放GIL。
    """

    def __init__(
        self,
        arg_供料: 设备供料_类,
        arg_设备名称: str | None = None,
    ) -> None:
        self._供料, self._错误 = arg_供料, None
        self._关闭 = False
        # 2.6.1 AudioDevice的文档允许None，实际Cython却要求str；直接使用同一
        # SDL2公开接口才能传NULL。不能另开一个枚举首项而忽略宿主默认输出。
        self._SDL = c.CDLL(audio.__file__)
        self._SDL.SDL_OpenAudioDevice.argtypes = [
            c.c_char_p,
            c.c_int,
            c.POINTER(SDL音频规格_类),
            c.POINTER(SDL音频规格_类),
            c.c_int,
        ]
        self._SDL.SDL_OpenAudioDevice.restype = c.c_uint32
        self._SDL.SDL_PauseAudioDevice.argtypes = [c.c_uint32, c.c_int]
        self._SDL.SDL_PauseAudioDevice.restype = None
        self._SDL.SDL_CloseAudioDevice.argtypes = [c.c_uint32]
        self._SDL.SDL_CloseAudioDevice.restype = None
        self._SDL.SDL_GetError.argtypes = []
        self._SDL.SDL_GetError.restype = c.c_char_p
        sdl2.init_subsystem(sdl2.INIT_AUDIO)
        self._回调引用 = 音频回调_型(self._回调)
        desired = SDL音频规格_类(
            frequency=48000,
            audioformat=audio.AUDIO_F32,
            numchannels=2,
            chunksize=512,
            callback=self._回调引用,
        )
        self._格式 = SDL音频规格_类()
        self.设备名称 = arg_设备名称
        self._编号 = self._SDL.SDL_OpenAudioDevice(
            arg_设备名称.encode("utf-8") if arg_设备名称 is not None else None,
            0,
            c.byref(desired),
            c.byref(self._格式),
            0,
        )
        if not self._编号:
            self._关闭 = True
            raise pygame.error(self._SDL.SDL_GetError().decode("utf-8", errors="replace"))
        self.api_暂停(False)

    def api_格式(self) -> tuple[int, int, int, int]:
        spec = self._格式
        return spec.frequency, spec.audioformat, spec.numchannels, spec.chunksize

    def _回调(
        self,
        arg_宿主: c.c_void_p,
        arg_指针: c.POINTER(c.c_uint8),
        arg_大小: int,
    ) -> None:
        buffer = memoryview(
            (c.c_uint8 * arg_大小).from_address(c.addressof(arg_指针.contents))
        ).cast("B")
        if self._错误 is not None:
            buffer[:] = bytes(arg_大小)
            return
        try:
            self._供料.api_填充(buffer)
        except Exception as error:
            # 外部C回调不能上抛；清掉未填缓冲，主线程检查必须重新抛出并进入恢复。
            self._错误 = error
            buffer[:] = bytes(arg_大小)

    def api_检查(self) -> None:
        if self._错误 is not None:
            raise RuntimeError("Pygame音频设备回调失败") from self._错误

    def api_暂停(self, arg_暂停: bool) -> None:
        if not self._关闭:
            self._SDL.SDL_PauseAudioDevice(self._编号, int(arg_暂停))

    def api_关闭(self) -> None:
        if not self._关闭:
            self.api_暂停(True)
            self._SDL.SDL_CloseAudioDevice(self._编号)
            self._关闭 = True
