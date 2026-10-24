# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_audio.cpp::decode_wave的接口与校验；标准SDL3只负责WAV与重采样。
# ◑ 导入
import ctypes as c
import sys
from array import array
from pathlib import Path

from rich4.runtime_library import 本地运行库_类


# ◕ 功能
class 音频格式_类(c.Structure):
    """
    SDL3公开SDL_AudioSpec的原ABI。

    更新日志：
    2026.10.24 - 与Pygame设备ABI分开；不通过C++参考项目加载资源。
    """

    _fields_ = [("format", c.c_uint32), ("channels", c.c_int), ("freq", c.c_int)]


class 原波形_类:
    """
    标准SDL3整条WAV转换至48000Hz双声道F32；游戏混音由Python处理。

    更新日志：
    2026.10.24 - 保留原整条转换、缓冲释放和字节长度检查，禁止坏素材伪造静音。
    """

    def __init__(self, arg_库: Path | None = None) -> None:
        路 = 本地运行库_类.api_选择("SDL3", "RICH4_SDL3_LIBRARY", arg_库)
        if 路 is None:
            raise RuntimeError("缺少标准SDL3库；请安装SDL3或设置RICH4_SDL3_LIBRARY")
        self._库 = c.CDLL(路)
        self._库.SDL_GetVersion.argtypes, self._库.SDL_GetVersion.restype = [], c.c_int
        self._库.SDL_GetError.argtypes, self._库.SDL_GetError.restype = [], c.c_char_p
        self._库.SDL_IOFromConstMem.argtypes = [c.c_void_p, c.c_size_t]
        self._库.SDL_IOFromConstMem.restype = c.c_void_p
        self._库.SDL_LoadWAV_IO.argtypes = [
            c.c_void_p,
            c.c_bool,
            c.POINTER(音频格式_类),
            c.POINTER(c.c_void_p),
            c.POINTER(c.c_uint32),
        ]
        self._库.SDL_LoadWAV_IO.restype = c.c_bool
        self._库.SDL_ConvertAudioSamples.argtypes = [
            c.POINTER(音频格式_类),
            c.c_void_p,
            c.c_int,
            c.POINTER(音频格式_类),
            c.POINTER(c.c_void_p),
            c.POINTER(c.c_int),
        ]
        self._库.SDL_ConvertAudioSamples.restype = c.c_bool
        self._库.SDL_free.argtypes, self._库.SDL_free.restype = [c.c_void_p], None
        self.版本 = self._库.SDL_GetVersion()
        if not 3002000 <= self.版本 < 4000000:
            raise RuntimeError("WAV转换需要SDL3 3.2以上的公开ABI")

    def _错误(self, arg_步骤: str) -> ValueError:
        return ValueError(
            arg_步骤 + "：" + self._库.SDL_GetError().decode("utf-8", errors="replace")
        )

    def api_解码(self, arg_数据: bytes) -> array:
        source = c.create_string_buffer(arg_数据)
        stream = self._库.SDL_IOFromConstMem(source, len(arg_数据))
        if not stream:
            raise self._错误("打开原WAV失败")
        spec, wave, length = 音频格式_类(), c.c_void_p(), c.c_uint32()
        converted, converted_length = c.c_void_p(), c.c_int()
        try:
            if not self._库.SDL_LoadWAV_IO(
                stream, True, c.byref(spec), c.byref(wave), c.byref(length)
            ):
                raise self._错误("原WAV解码失败")
            if length.value > 2147483647:
                raise ValueError("原WAV超过SDL转换长度范围")
            target = 音频格式_类(0x8120 if sys.byteorder == "little" else 0x9120, 2, 48000)
            if not self._库.SDL_ConvertAudioSamples(
                c.byref(spec),
                wave,
                length.value,
                c.byref(target),
                c.byref(converted),
                c.byref(converted_length),
            ):
                raise self._错误("原WAV转F32失败")
            if converted_length.value <= 0 or converted_length.value % 8:
                raise ValueError("原WAV转换双声道采样长度不符")
            out = array("f")
            out.frombytes(c.string_at(converted, converted_length.value))
            return out
        finally:
            self._库.SDL_free(converted)
            self._库.SDL_free(wave)
