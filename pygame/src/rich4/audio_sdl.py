# SPDX-License-Identifier: GPL-3.0-or-later
# SDL2公开SDL_AudioSpec ABI；只使用Pygame同一SDL库，不装载其它游戏引擎。
# ◑ 导入
import ctypes as c

# ◕ 功能
音频回调_型 = c.CFUNCTYPE(None, c.c_void_p, c.POINTER(c.c_uint8), c.c_int)


class SDL音频规格_类(c.Structure):
    """
    SDL2音频格式与回调指针，保留C字段顺序和对齐。

    更新日志：
    2026.10.24 - 绕开Pygame2.6.1把默认设备None错误拒绝的绑定限制。
    """

    _fields_ = [
        ("frequency", c.c_int),
        ("audioformat", c.c_uint16),
        ("numchannels", c.c_uint8),
        ("silence", c.c_uint8),
        ("chunksize", c.c_uint16),
        ("padding", c.c_uint16),
        ("size", c.c_uint32),
        ("callback", 音频回调_型),
        ("userdata", c.c_void_p),
    ]
