# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_audio.cpp的异步档案、设备、捕获与销毁顺序。
# ◑ 导入
import os
from array import array
from contextlib import ExitStack
from pathlib import Path

from rich4.audio import 音频_类
from rich4.audio_archives import 音频档案_类
from rich4.audio_capture import 音频捕获_类
from rich4.audio_device import 音频设备_类
from rich4.audio_feed import 设备供料_类


# ◕ 功能
class 设备音频_类(音频_类):
    """
    正式Pygame音频宿主：后台开MKF、主线程解码、设备独立拉取PCM/MIDI。

    更新日志：
    2026.10.24 - 退出先停止设备；构造失败也关闭已创建的自有资源，不静默假成功。
    """

    def __init__(
        self,
        arg_素材: Path,
        arg_启用: bool = True,
        arg_音库: Path | None = None,
        arg_SDL库: Path | None = None,
        arg_Fluid库: Path | None = None,
        arg_捕获: Path | None = None,
    ) -> None:
        self._设备: 音频设备_类 | None = None
        self._档案: 音频档案_类 | None = None
        self._已关闭 = False
        with ExitStack() as cleanup:
            if arg_启用:
                self._档案 = 音频档案_类(arg_素材)
                cleanup.callback(self._档案.api_关闭)
            super().__init__(arg_素材, arg_启用, arg_音库, arg_SDL库, arg_Fluid库)
            cleanup.callback(super().api_关闭)
            path = arg_捕获
            if path is None and os.environ.get("RICH4_AUDIO_CAPTURE"):
                path = Path(os.environ["RICH4_AUDIO_CAPTURE"])
            self._捕获 = 音频捕获_类(path if arg_启用 else None)
            self._供料 = 设备供料_类(self.api_渲染块, self._混音._统计, self._锁, self._捕获)
            if arg_启用:
                self._设备 = 音频设备_类(
                    self._供料, arg_设备名称=os.environ.get("RICH4_AUDIO_DEVICE") or None
                )
                cleanup.callback(self._设备.api_关闭)
            cleanup.pop_all()

    def _载入(self, arg_语音: bool, arg_编号: int) -> array:
        key = arg_语音, arg_编号
        if key not in self._样本:
            if self._档案 is None or self._波形 is None:
                raise RuntimeError("未启用的设备音频不能载入样本")
            archive = self._档案.api_包(arg_语音)
            self._样本[key] = self._波形.api_解码(archive.api_解码(arg_编号))
        return self._样本[key]

    def api_暂停设备(self, arg_暂停: bool) -> None:
        if self._设备 is not None:
            self._设备.api_暂停(arg_暂停)

    def api_更新(self) -> None:
        super().api_更新()
        if self._设备 is not None:
            self._设备.api_检查()

    def api_排队字节(self) -> int:
        with self._锁:
            return self._供料.余量

    def api_关闭(self) -> None:
        if self._已关闭:
            return
        self._已关闭 = True
        if self._设备 is not None:
            self._设备.api_关闭()
        try:
            self._捕获.api_写出()
        finally:
            try:
                if self._档案 is not None:
                    self._档案.api_关闭()
            finally:
                super().api_关闭()
