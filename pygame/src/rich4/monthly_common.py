# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/monthly.cpp的共用辅助和股利表。
# ◑ 导入
import logging
from collections.abc import Callable
from dataclasses import dataclass

from rich4.flc import 动画_类
from rich4.game_types import 月报_类
from rich4.monthly_types import 月播_类, 月泡_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类
from rich4.original_text import 原版文字_类
from rich4.screen_draw import 屏幕字样_类, 屏幕绘图_类
from rich4.world import 世界_类


# ◕ 功能
@dataclass
class 月报声音_类:
    """
    原一次音/语音接口，语音返回实际长度以驱动气泡等待。

    更新日志：
    2026.10.24 - 屏幕只请求播放，不参与核心随机或结算。
    """

    播放: Callable[[int], None] | None = None
    语音: Callable[[int], int] | None = None


class 月报共用_类:
    """
    原人物列表、装饰随机、贴图/文字/影片与股利表，只读原月结数据。

    更新日志：
    2026.10.24 - 长对白从外部PE读取，损坏影片依原不阻断屏幕并记录故障。
    """

    声音: 月报声音_类
    原文: 原版文字_类
    黑字 = 屏幕字样_类(16, 0x101010, 0, 2)
    泡字 = 屏幕字样_类(20, 0x101010, 0, 2)
    _文 = staticmethod(屏幕绘图_类.api_文字)
    _钱 = staticmethod(屏幕绘图_类.api_货币)

    @staticmethod
    def _槽(arg_数据: 月报_类) -> list[int]:
        return [i for i in range(4) if (arg_数据.活跃 >> i) & 1]

    @staticmethod
    def _角色(arg_数据: 月报_类, arg_槽: int) -> int:
        if not 0 <= arg_槽 < len(arg_数据.人物):
            raise IndexError("原月报人物槽越界")
        return arg_数据.人物[arg_槽] % 12

    @classmethod
    def _姓名(cls, arg_数据: 月报_类, arg_槽: int) -> str:
        return 画框_类.人名[cls._角色(arg_数据, arg_槽)]

    @staticmethod
    def _装饰(arg_播: 月播_类) -> int:
        arg_播.种子 = (arg_播.种子 * 1103515245 + 12345) & 0xFFFFFFFF
        return (arg_播.种子 >> 16) & 32767

    @staticmethod
    def _有号32(arg_数: int) -> int:
        n = arg_数 & 0xFFFFFFFF
        return n - (1 << 32) if n & (1 << 31) else n

    @staticmethod
    def _贴(
        arg_框: 画框_类,
        arg_库: str,
        arg_条: int,
        arg_帧: int,
        arg_x: int,
        arg_y: int,
        arg_不透明: bool = False,
    ) -> None:
        arg_框.画布.api_绘制(
            arg_框.美术.api_帧(arg_库, arg_条, arg_帧), arg_x, arg_y, arg_强制不透明=arg_不透明
        )

    @staticmethod
    def _开片(arg_框: 画框_类, arg_库: str, arg_条: int) -> 动画_类 | None:
        try:
            数据 = arg_框.美术.api_解码(arg_库, arg_条)
            if len(数据) < 128 or 数据[4:6] != b"\x12\xaf":
                return None
            return 动画_类(数据)
        except (ValueError, OSError, IndexError, RuntimeError) as 错:
            logging.getLogger(__name__).warning("跳过损坏月报影片：%s", 错)
            return None

    def _说(
        self,
        arg_播: 月播_类,
        arg_条帧: int,
        arg_x: int,
        arg_y: int,
        arg_dx: int,
        arg_dy: int,
        arg_声音: int,
        arg_文: str | None = None,
    ) -> None:
        文 = self.原文.api_配音(arg_声音).文字 if arg_文 is None else arg_文
        泡 = 月泡_类(arg_条帧, arg_x, arg_y, arg_dx, arg_dy, 文, 2000, True)
        arg_播.泡 = 泡
        if self.声音.语音:
            泡.剩余毫秒 = max(2000, self.声音.语音(arg_声音) & 0xFFFFFFFF)

    def _贴泡(self, arg_框: 画框_类, arg_播: 月播_类, arg_条: int) -> None:
        泡 = arg_播.泡
        if not 泡.显示:
            return
        图 = arg_框.美术.api_帧("p", arg_条, 泡.条帧)
        arg_框.画布.api_绘制(图, 泡.x, 泡.y)
        左, 顶 = 泡.x - 图.原点x, 泡.y - 图.原点y
        self._文(arg_框, 泡.文字, 左 + 图.宽 // 2 + 泡.dx, 顶 + 图.高 // 2 + 泡.dy, 4, self.泡字)

    def _画股利(self, arg_框: 画框_类, arg_世: 世界_类, arg_播: 月播_类, arg_毫秒: int) -> bool:
        p, f = arg_播, arg_播.数据
        p.已过 = (p.已过 + arg_毫秒) & 0xFFFFFFFF
        while p.已过 >= p.节拍:
            p.已过 -= p.节拍
            p.计数 = self._有号32(p.计数 + 1)
        原生界面_类.api_填充(arg_框.画布, (0, 0, 640, 480), 0)
        self._贴(arg_框, "p", 76, 0, 24, 24, True)
        self._文(arg_框, "上市公司分紅", 320, 49, 2, 屏幕字样_类(28, 0xF0F0F0, 0x101010, 3))
        self._文(arg_框, "人名", 128, 106, 6, 屏幕字样_类(12, 0x101010, 0, 2))
        self._文(arg_框, "公司", 42, 118, 5, 屏幕字样_类(12, 0x101010, 0, 2))
        列 = [0] * 4
        for n, i in enumerate(self._槽(f)):
            列[i] = n
            self._文(arg_框, self._姓名(f, i), 184 + 98 * n, 112, 2, self.黑字)
        self._文(arg_框, "本月盈餘", 566, 112, 2, self.黑字)
        self._文(arg_框, "紅  利", 86, 428, 2, self.黑字)
        总 = [0] * 4
        图 = arg_世.头.阶段 * 4 + arg_世.头.地图
        y = 116
        for 行 in f.股利:
            idx = 图 * 12 + 行.股票
            if 0 <= idx < 96:
                self._文(arg_框, self.原文.api_股票(idx), 86, 24 + y, 2, self.黑字)
            for i in self._槽(f):
                self._文(arg_框, self._钱(行.派发[i]), 222 + 98 * 列[i], 24 + y, 6, self.黑字)
                总[i] += 行.派发[i]
            self._文(arg_框, self._钱(行.盈余), 596, 24 + y, 6, self.黑字)
            y += 24
        for i in self._槽(f):
            self._文(arg_框, self._钱(总[i]), 222 + 98 * 列[i], 428, 6, self.黑字)
        return not p.点过 and p.计数 < 3
