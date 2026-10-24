# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定native_audio.cpp的MIDI列表、上下文栈及采样时钟恢复。
# ◑ 导入
import os
import sys
from array import array
from collections.abc import Callable
from pathlib import Path

from rich4.audio_types import 音乐_类
from rich4.fluid_synth import Fluid合成_类


# ◕ 功能
class MIDI播放器_类:
    """
    原八首歌单和十八上下文；调用者在设备与主线程间共用锁。

    更新日志：
    2026.10.24 - MIDI一次预读，回调不读文件；缺音库仅使音乐不可用，不替代假声音。
    """

    歌单 = ("rich08.mid", *(f"rich{i}.mid" for i in range(16, 23)))
    上下文文件 = (
        "silence",
        *(f"midi{i:02}.mid" for i in range(1, 14)),
        "midi14-1.mid",
        "midi14-2.mid",
        "midi15.mid",
        "midi16.mid",
    )

    def __init__(
        self,
        arg_素材: Path,
        arg_音库: Path | None = None,
        arg_库: Path | None = None,
        arg_初始化: bool = True,
    ) -> None:
        self.开关, self.曲目, self.上下文 = True, 1, None
        self._过期, self._恢复 = False, 0
        self._栈: list[tuple[音乐_类 | None, int, int]] = []
        self._缓存: dict[str, bytes] = {}
        self._追踪: Callable[[str, str], None] | None = None
        self._待日志: list[tuple[str, str]] = []
        self._渲染错误, self.诊断 = "", ""
        self._合成: Fluid合成_类 | None = None
        if not arg_初始化:
            return
        bank = arg_音库 if arg_音库 is not None else Path(os.environ.get("RICH4_SOUNDFONT", ""))
        if str(bank) == "." and sys.platform == "darwin":
            bank = Path(
                "/System/Library/Components/CoreAudio.component/Contents/Resources/"
                "gs_instruments.dls"
            )
        if not bank.is_file():
            self.诊断 = (
                "MIDI soundbank unavailable; set RICH4_SOUNDFONT to a General MIDI SF2/DLS file"
            )
            return
        files = {p.name.lower(): p for p in arg_素材.iterdir() if p.is_file()}
        for name in self.歌单:
            self._缓存[name] = self._读取(files, name, arg_素材)
        for name in self.上下文文件[1:]:
            try:
                self._缓存[name] = self._读取(files, name, arg_素材)
            except (OSError, ValueError) as error:
                # 原可选上下文缺失时只该屏幕静音，诊断保留最后失败；歌单必须齐全。
                self.诊断 = str(error)
        try:
            self._合成 = Fluid合成_类(bank, arg_库)
        except ValueError as error:
            self.诊断 = str(error)
            return
        error = self._起曲()
        if error:
            self.api_关闭()
            raise RuntimeError(error)

    @staticmethod
    def _读取(arg_文件: dict[str, Path], arg_名称: str, arg_目录: Path) -> bytes:
        if arg_名称 not in arg_文件:
            raise ValueError("missing audio asset: " + str(arg_目录 / arg_名称))
        path = arg_文件[arg_名称]
        length = path.stat().st_size
        if length > 16 * 1024 * 1024:
            raise ValueError("invalid MIDI size: " + str(path))
        data = path.read_bytes()
        if len(data) != length:
            raise ValueError("truncated MIDI: " + str(path))
        return data

    @property
    def 可用(self) -> bool:
        return self._合成 is not None

    def api_追踪(self, arg_追踪: Callable[[str, str], None] | None) -> None:
        self._追踪 = arg_追踪

    def _日志(self, arg_事件: str, arg_详情: str) -> None:
        if self._追踪 is not None:
            self._追踪(arg_事件, arg_详情)

    def api_文件(self) -> str:
        return (
            self.上下文文件[int(self.上下文)]
            if self.上下文 is not None
            else self.歌单[self.曲目 - 1]
        )

    def api_时刻(self) -> int:
        if self._过期:
            return self._恢复
        return self._合成.api_时刻() if self._合成 is not None else 0

    def _起曲(self, arg_时刻: int = 0) -> str:
        if self._合成 is None:
            return ""
        self._合成.api_重置()
        if not self.开关:
            self._过期, self._恢复 = True, arg_时刻
            return ""
        self._过期 = False
        name = self.api_文件()
        if self.上下文 == 音乐_类.静音 or name not in self._缓存:
            return ""
        return self._合成.api_起曲(name, self._缓存[name], self.上下文 is not None, arg_时刻)

    def _要求起曲(self, arg_时刻: int = 0) -> None:
        error = self._起曲(arg_时刻)
        if error:
            raise RuntimeError(error)

    def _推(self, arg_音乐: 音乐_类, arg_保存: bool) -> None:
        self._日志("music_push" if arg_保存 else "music_replace", self.上下文文件[arg_音乐])
        if arg_保存 or not self._栈:
            self._栈.append((self.上下文, self.曲目, self.api_时刻()))
        self.上下文 = arg_音乐
        self._要求起曲()

    def api_推音乐(self, arg_音乐: 音乐_类) -> None:
        self._推(arg_音乐, True)

    def api_换音乐(self, arg_音乐: 音乐_类) -> None:
        self._推(arg_音乐, False)

    def api_弹音乐(self) -> None:
        if not self._栈:
            return
        self.上下文, self.曲目, tick = self._栈.pop()
        self._日志("music_pop", self.api_文件())
        self._要求起曲(tick)

    def api_选音乐(self, arg_曲目: int) -> None:
        if not 0 <= arg_曲目 <= 8:
            raise ValueError("normal MIDI playlist selection must be 0 through 8")
        self.曲目 = self.曲目 % 8 + 1 if arg_曲目 == 0 else arg_曲目
        self.上下文 = None
        self._栈.clear()
        self._日志("music_select", self.api_文件())
        self._要求起曲()

    def api_音乐开关(self, arg_开关: bool) -> None:
        if self.开关 == arg_开关:
            return
        self.开关 = arg_开关
        error = self._起曲(self._恢复) if arg_开关 and self._过期 else ""
        self._日志("music_enabled", "on" if arg_开关 else "off")
        if error:
            raise RuntimeError(error)

    def api_渲染块(self) -> array | None:
        synth = self._合成
        if not self.开关 or synth is None or not synth.有播放器:
            return None
        if synth.api_状态() == 3 and self.上下文 is None:
            self.曲目 = self.曲目 % 8 + 1
            self._待日志.append(("music_next", self.api_文件()))
            error = self._起曲()
            if error:
                self._渲染错误 = error
        try:
            return synth.api_渲染块()
        except RuntimeError as error:
            # 原渲染失败只停MIDI，音效/语音仍继续；主线程update统一报告。
            self._渲染错误 = str(error)
            return None

    def api_关闭(self) -> None:
        if self._合成 is not None:
            self._合成.api_关闭()
            self._合成 = None
