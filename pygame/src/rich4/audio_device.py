# SPDX-License-Identifier: GPL-3.0-or-later
# 标准Pygame SDL2 AudioDevice；原SDL3设备供料语义见audio_feed.py。
# ◑ 导入
import ctypes as c

from pygame._sdl2 import audio, sdl2

from rich4.audio_feed import 设备供料_类


# ◕ 功能
class 音频设备_类:
    """
    Pygame原生48000Hz立体声F32输出，显式关闭回调后才销毁宿主。

    更新日志：
    2026.10.24 - SDL总生命周期归应用pygame.quit；这里只关闭自己打开的设备。
    """

    def __init__(self, arg_供料: 设备供料_类) -> None:
        self._供料, self._错误 = arg_供料, None
        self._关闭 = False
        # 2.6.1的pause/close持有GIL并等待回调，回调又要GIL；通过同一SDL2公开
        # pause接口释放GIL，确认设备暂停后才让Pygame.close清理自己的deviceid。
        self._SDL = c.CDLL(audio.__file__)
        self._SDL.SDL_PauseAudioDevice.argtypes = [c.c_uint32, c.c_int]
        self._SDL.SDL_PauseAudioDevice.restype = None
        sdl2.init_subsystem(sdl2.INIT_AUDIO)
        names = audio.get_audio_device_names(False)
        if not names:
            raise RuntimeError("没有Pygame音频输出设备")
        self._设备 = audio.AudioDevice(
            devicename=names[0],
            iscapture=False,
            frequency=48000,
            audioformat=audio.AUDIO_F32,
            numchannels=2,
            chunksize=512,
            allowed_changes=0,
            callback=self._回调,
        )
        self.api_暂停(False)

    def _回调(self, arg_设备: audio.AudioDevice, arg_缓冲: memoryview) -> None:
        if self._错误 is not None:
            arg_缓冲[:] = bytes(len(arg_缓冲))
            return
        try:
            # Pygame传入Cython _memoryviewslice，先取标准buffer视图再cast。
            self._供料.api_填充(memoryview(arg_缓冲))
        except Exception as error:
            # 外部C回调不能上抛；清掉未填缓冲，主线程检查必须重新抛出并进入恢复。
            # 这是失败边界，不将后续静音计为成功播放，也不吞掉程序错误。
            self._错误 = error
            arg_缓冲[:] = bytes(len(arg_缓冲))

    def api_检查(self) -> None:
        if self._错误 is not None:
            raise RuntimeError("Pygame音频设备回调失败") from self._错误

    def api_暂停(self, arg_暂停: bool) -> None:
        self._SDL.SDL_PauseAudioDevice(self._设备.deviceid, int(arg_暂停))

    def api_关闭(self) -> None:
        if not self._关闭:
            self.api_暂停(True)
            self._设备.close()
            self._关闭 = True
