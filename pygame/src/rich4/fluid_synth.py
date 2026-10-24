# SPDX-License-Identifier: GPL-3.0-or-later
# 标准FluidSynth公开C接口；设置来自固定native_audio.cpp，不链接参考引擎。
# ◑ 导入
import ctypes as c
import os
from array import array
from pathlib import Path

from rich4.runtime_library import 本地运行库_类


# ◕ 功能
class Fluid合成_类:
    """
    样本时钟MIDI软件合成器；不建立任何FluidSynth设备驱动。

    更新日志：
    2026.10.24 - 保留48000Hz/gain0.28/无混响与合唱，指针绑定先于第一次调用。
    """

    def __init__(self, arg_音库: Path, arg_库: Path | None = None) -> None:
        path = 本地运行库_类.api_选择("fluidsynth", "RICH4_FLUIDSYNTH_LIBRARY", arg_库)
        if path is None:
            raise RuntimeError("缺少标准FluidSynth库；请设置RICH4_FLUIDSYNTH_LIBRARY")
        self._库 = c.CDLL(path)
        self._设置 = self._合成 = self._播放 = None
        self._内存: c.Array[c.c_char] | None = None
        # 指针返回必须显式声明；默认int在64位系统会截断地址。
        signatures = {
            "new_fluid_settings": ([], c.c_void_p),
            "delete_fluid_settings": ([c.c_void_p], None),
            "fluid_settings_setnum": ([c.c_void_p, c.c_char_p, c.c_double], c.c_int),
            "fluid_settings_setint": ([c.c_void_p, c.c_char_p, c.c_int], c.c_int),
            "fluid_settings_setstr": ([c.c_void_p, c.c_char_p, c.c_char_p], c.c_int),
            "new_fluid_synth": ([c.c_void_p], c.c_void_p),
            "delete_fluid_synth": ([c.c_void_p], None),
            "fluid_synth_sfload": ([c.c_void_p, c.c_char_p, c.c_int], c.c_int),
            "fluid_synth_system_reset": ([c.c_void_p], c.c_int),
            "fluid_synth_write_float": (
                [c.c_void_p, c.c_int, c.c_void_p, c.c_int, c.c_int, c.c_void_p, c.c_int, c.c_int],
                c.c_int,
            ),
            "new_fluid_player": ([c.c_void_p], c.c_void_p),
            "delete_fluid_player": ([c.c_void_p], None),
            "fluid_player_add_mem": ([c.c_void_p, c.c_void_p, c.c_size_t], c.c_int),
            "fluid_player_set_loop": ([c.c_void_p, c.c_int], c.c_int),
            "fluid_player_play": ([c.c_void_p], c.c_int),
            "fluid_player_seek": ([c.c_void_p, c.c_int], c.c_int),
            "fluid_player_get_current_tick": ([c.c_void_p], c.c_int),
            "fluid_player_get_status": ([c.c_void_p], c.c_int),
            "fluid_set_log_function": ([c.c_int, c.c_void_p, c.c_void_p], c.c_void_p),
            "fluid_version_str": ([], c.c_char_p),
        }
        for name, (args, result) in signatures.items():
            function = getattr(self._库, name)
            function.argtypes, function.restype = args, result
        self.版本 = self._库.fluid_version_str().decode()
        self._库.fluid_set_log_function(2, None, None)
        self._库.fluid_set_log_function(3, None, None)
        try:
            self._设置 = self._库.new_fluid_settings()
            if not self._设置:
                raise RuntimeError("cannot create FluidSynth settings")
            self._库.fluid_settings_setnum(self._设置, b"synth.sample-rate", 48000)
            self._库.fluid_settings_setnum(self._设置, b"synth.gain", 0.28)
            self._库.fluid_settings_setstr(self._设置, b"player.timing-source", b"sample")
            self._库.fluid_settings_setint(self._设置, b"synth.reverb.active", 0)
            self._库.fluid_settings_setint(self._设置, b"synth.chorus.active", 0)
            self._合成 = self._库.new_fluid_synth(self._设置)
            if (
                not self._合成
                or self._库.fluid_synth_sfload(self._合成, os.fsencode(arg_音库), 1) < 0
            ):
                raise ValueError("FluidSynth could not load MIDI soundbank: " + str(arg_音库))
        except (RuntimeError, ValueError):
            self.api_关闭()
            raise

    @property
    def 有播放器(self) -> bool:
        return bool(self._播放)

    def api_重置(self) -> None:
        self.api_停曲()
        self._库.fluid_synth_system_reset(self._合成)

    def api_停曲(self) -> None:
        if self._播放:
            self._库.delete_fluid_player(self._播放)
            self._播放 = None
        self._内存 = None

    def api_起曲(
        self,
        arg_文件: str,
        arg_数据: bytes,
        arg_循环: bool,
        arg_时刻: int,
    ) -> str:
        self._播放 = self._库.new_fluid_player(self._合成)
        self._内存 = c.create_string_buffer(arg_数据)
        if (
            not self._播放
            or self._库.fluid_player_add_mem(self._播放, self._内存, len(arg_数据)) != 0
        ):
            self.api_停曲()
            return "cannot load original MIDI " + arg_文件
        if arg_循环:
            self._库.fluid_player_set_loop(self._播放, -1)
        if self._库.fluid_player_play(self._播放) != 0:
            self.api_停曲()
            return "cannot start original MIDI " + arg_文件
        # 原先play后seek且忽略返回；新文件未加载时会拒绝，保留并在AUDIO.md记录。
        if arg_时刻 > 0:
            self._库.fluid_player_seek(self._播放, arg_时刻)
        return ""

    def api_时刻(self) -> int:
        return max(0, self._库.fluid_player_get_current_tick(self._播放)) if self._播放 else 0

    def api_状态(self) -> int:
        return self._库.fluid_player_get_status(self._播放) if self._播放 else -1

    def api_渲染块(self) -> array | None:
        if not self._播放:
            return None
        output = array("f", [0]) * 1024
        buffer = (c.c_float * 1024).from_buffer(output)
        if self._库.fluid_synth_write_float(self._合成, 512, buffer, 0, 2, buffer, 1, 2) != 0:
            self.api_停曲()
            raise RuntimeError("MIDI software rendering failed")
        return output

    def api_关闭(self) -> None:
        self.api_停曲()
        if self._合成:
            self._库.delete_fluid_synth(self._合成)
            self._合成 = None
        if self._设置:
            self._库.delete_fluid_settings(self._设置)
            self._设置 = None
