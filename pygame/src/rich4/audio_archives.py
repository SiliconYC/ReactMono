# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_audio.cpp::Impl/archive_loader/load_clip，Python独立读取MKF。
# ◑ 导入
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from rich4.artwork import 美术_类
from rich4.assets import 资源包_类
from rich4.open_archive import 开放档案_类


# ◕ 功能
class 音频档案_类:
    """
    自有启动线程一次打开Effect/Speaking；首次使用等待，失败保留并反复报告。

    更新日志：
    2026.10.24 - 两档案均成功才发布；回调不等待档案，不在后台解码所有WAV。
    """

    def __init__(self, arg_目录: Path) -> None:
        self._池 = ThreadPoolExecutor(max_workers=1, thread_name_prefix="rich4-audio-assets")
        self._任务 = self._池.submit(self._读取, arg_目录)
        self._包: tuple[资源包_类 | 开放档案_类, 资源包_类 | 开放档案_类] | None = None
        self._错误 = ""

    @staticmethod
    def _读取(arg_目录: Path) -> tuple[资源包_类 | 开放档案_类, 资源包_类 | 开放档案_类]:
        artwork = 美术_类(arg_目录)
        return artwork.api_包("e"), artwork.api_包("s")

    def api_包(self, arg_语音: bool) -> 资源包_类 | 开放档案_类:
        if self._错误:
            raise ValueError(self._错误)
        if self._包 is None:
            try:
                self._包 = self._任务.result()
            except (ValueError, OSError) as error:
                self._错误 = str(error)
                raise ValueError(self._错误) from error
        return self._包[int(arg_语音)]

    def api_关闭(self) -> None:
        self._池.shutdown(wait=True)
