# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定tools/screens/messages.cpp::Overlay/draw_text/draw_yes_no；台词由调用方外部读取。
# ◑ 导入
import struct
from collections import deque
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass, field
from enum import IntEnum
from time import monotonic_ns

from rich4.graphics import 图像_类
from rich4.native_frame import 画框_类
from rich4.native_ui import 原生界面_类, 文字样式_类


# ◕ 功能
class 消息种类_类(IntEnum):
    """
    原Item::Kind顺序，区别普通气泡与全屏新闻/命运。

    更新日志：
    2026.10.24 - 保留五种原消息类型。
    """

    气泡 = 0
    对话框 = 1
    新闻 = 2
    命运 = 3
    神明字幕 = 4


@dataclass
class 消息行_类:
    """
    原新闻受影响人物行，空文字表示仅绘制头像。

    更新日志：
    2026.10.24 - 人物及原头像帧与文字独立保存。
    """

    人物: int
    头像帧: int
    文字: str = ""


@dataclass
class 消息_类:
    """
    原Item按值消息数据；不持有规则状态或内置商业文字。

    更新日志：
    2026.10.24 - 声音0在消息层代表静音，与外部配音表编号0的读取语义分开。
    """

    种类: 消息种类_类 = 消息种类_类.气泡
    焦点: int | None = None
    人物: int = 0
    情绪: int = 0
    文字: str = ""
    图语: int = -1
    声音: int = 0
    最少毫秒: int = 1000
    等待声音: bool = False
    框x: int = 220
    照片: int = 0
    标题: str = ""
    行: list[消息行_类] = field(default_factory=list)


@dataclass
class 消息声音_类:
    """
    消息原语音播放/停止接口，播放返回实际片长毫秒。

    更新日志：
    2026.10.24 - 无音频回调时依原最短停留时长推进。
    """

    播放: Callable[[int], int] | None = None
    停止: Callable[[], None] | None = None


class 消息层_类:
    """
    原Overlay模态消息队列、语音时钟、五类原美术及确认条。

    更新日志：
    2026.10.24 - 显式单调时钟替代SDL_GetTicks，退休与绘制仍由应用按原顺序调用。
    """

    近黑 = 原生界面_类.api_颜色(16, 16, 16)
    近白 = 原生界面_类.api_颜色(240, 240, 240)
    气泡字 = 文字样式_类(16, 近黑)
    框字 = 文字样式_类(16, 近白, True, True, False, 近黑)
    新闻字 = 文字样式_类(28, 近白, True, True, False, 近黑)
    新闻行字 = 文字样式_类(24, 近白, True, True, False, 近黑)
    神明字 = 文字样式_类(28, 32767, True, False, True, 近黑)

    def __init__(
        self,
        arg_声音: 消息声音_类,
        arg_时钟: Callable[[], int] = lambda: monotonic_ns() // 1_000_000,
    ) -> None:
        self.声音, self.时钟 = arg_声音, arg_时钟
        self._队列: deque[消息_类] = deque()
        self._已开始 = self._即时 = False
        self._截止 = 0
        self._最后气泡 = ""
        self._照片缓存: dict[int, 图像_类] = {}

    def api_活跃(self) -> bool:
        return bool(self._队列)

    def api_当前(self) -> 消息_类 | None:
        return self._队列[0] if self._队列 else None

    def api_焦点(self) -> int | None:
        return self._队列[0].焦点 if self._队列 else None

    def api_即时(self, arg_即时: bool) -> None:
        self._即时 = arg_即时

    def api_入队(self, arg_消息: 消息_类) -> None:
        if arg_消息.种类 == 消息种类_类.气泡:
            键 = str(arg_消息.声音)
            if 键 == self._最后气泡:
                return
            self._最后气泡 = 键
        self._队列.append(deepcopy(arg_消息))

    def api_清空(self) -> None:
        if self._已开始 and self.声音.停止:
            self.声音.停止()
        self._队列.clear()
        self._已开始 = False

    def api_跳过(self) -> None:
        if not self._队列:
            return
        if self.声音.停止:
            self.声音.停止()
        self._队列.popleft()
        self._已开始 = False

    def _开始(self, arg_时: int) -> None:
        self._已开始 = True
        项 = self._队列[0]
        声长 = self.声音.播放(项.声音) if 项.声音 and self.声音.播放 else 0
        self._截止 = (arg_时 + max(项.最少毫秒, 声长 if 项.等待声音 else 0)) & 0xFFFFFFFFFFFFFFFF

    def api_退休(self) -> None:
        if self._已开始 and self._队列 and (self._即时 or self.时钟() >= self._截止):
            self._队列.popleft()
            self._已开始 = False

    @staticmethod
    def api_文字(
        arg_框: 画框_类,
        arg_文: str,
        arg_x: int,
        arg_y: int,
        arg_模式: int,
        arg_式: 文字样式_类,
    ) -> None:
        宽, 高 = arg_框.字体.api_块范围(arg_文, arg_式)
        除 = 画框_类._零除
        if arg_模式 == 0:
            左, 顶 = arg_x, arg_y
        elif arg_模式 == 5:
            左, 顶 = arg_x, arg_y - 除(高, 2)
        else:
            左 = arg_x - 除(宽, 2)
            顶 = arg_y - (高 if arg_模式 == 7 else 除(高, 2))
        arg_框.字体.api_绘块(arg_框.画布, arg_文, 左, 顶, arg_式, arg_模式 in (4, 7))

    @staticmethod
    def api_确认条(
        arg_框: 画框_类,
        arg_x: int,
        arg_y: int,
        arg_是号: int,
        arg_是: Callable[[], None],
        arg_否号: int,
        arg_否: Callable[[], None],
    ) -> None:
        图 = arg_框.美术.api_帧("d", 440, 0)
        左, 顶 = arg_x - 图.宽 // 2, arg_y - 图.高 // 2
        是框 = 左 - 10, 顶 - 10, 左 + 图.宽 // 2, 顶 + 图.高 + 10
        否框 = 左 + 图.宽 // 2, 顶 - 10, 左 + 图.宽 + 10, 顶 + 图.高 + 10
        帧 = 1 if arg_框.api_指针内(是框) else 2 if arg_框.api_指针内(否框) else 0
        示 = arg_框.美术.api_帧("d", 440, 帧)
        arg_框.画布.api_绘制(示, 左 + 示.原点x, 顶 + 示.原点y, arg_强制不透明=True)
        arg_框.api_命中(arg_是号, 是框, arg_是)
        arg_框.api_命中(arg_否号, 否框, arg_否)

    @classmethod
    def api_确认框(
        cls,
        arg_框: 画框_类,
        arg_文: str,
        arg_是号: int,
        arg_是: Callable[[], None],
        arg_否号: int,
        arg_否: Callable[[], None],
    ) -> None:
        arg_框.画布.api_绘制(arg_框.美术.api_帧("d", 517, 5), 220, 140)
        cls.api_文字(arg_框, arg_文, 220, 140, 4, cls.框字)
        cls.api_确认条(arg_框, 220, 320, arg_是号, arg_是, arg_否号, arg_否)

    def api_绘制(self, arg_框: 画框_类) -> bool:
        时 = self.时钟()
        if not self._队列:
            return False
        if not self._已开始:
            self._开始(时)
        arg_框.按钮.clear()
        self._画项(arg_框, self._队列[0])
        arg_框.api_命中(900, (0, 0, 640, 480), self.api_跳过)
        return True

    def _照片(self, arg_框: 画框_类, arg_条: int) -> 图像_类:
        if arg_条 not in self._照片缓存:
            数据 = arg_框.美术.api_解码("d", arg_条)
            数 = min(388 * 251, len(数据) // 2)
            色 = list(struct.unpack_from(f"<{数}H", 数据))
            self._照片缓存[arg_条] = 图像_类(388, 251, 色 + [0] * (388 * 251 - 数))
        return self._照片缓存[arg_条]

    def _画项(self, arg_框: 画框_类, arg_项: 消息_类) -> None:
        画, 项, 美 = arg_框.画布, arg_项, arg_框.美术
        if 项.种类 == 消息种类_类.气泡:
            画.api_绘制(美.api_帧("d", 517, 6), 220, 130, (0, 40, 440, 260))
            画.api_绘制(美.api_帧("m", 27 + 项.人物, 项.情绪 + 1), 170, 130)
            if 项.图语 > 0:
                画.api_绘制(美.api_帧("d", 519, 项.图语 - 1), 240, 130)
            else:
                self.api_文字(arg_框, 项.文字, 200, 130, 5, self.气泡字)
        elif 项.种类 == 消息种类_类.对话框:
            画.api_绘制(美.api_帧("d", 517, 5), 项.框x, 140)
            self.api_文字(arg_框, 项.文字, 项.框x, 140, 4, self.框字)
        elif 项.种类 in (消息种类_类.新闻, 消息种类_类.命运):
            新闻 = 项.种类 == 消息种类_类.新闻
            图 = 美.api_帧("p", 66, 0 if 新闻 else 1)
            画.api_绘制(图, 图.原点x, 图.原点y, arg_强制不透明=True)
            画.api_绘制(self._照片(arg_框, 项.照片), 25, 44, arg_强制不透明=True)
            if 新闻:
                self.api_文字(arg_框, 项.标题, 24, 8, 0, self.新闻字)
                self.api_文字(arg_框, 项.文字, 24, 310, 0, self.新闻字)
                for k, 行 in enumerate(项.行):
                    脸 = 美.api_帧("m", 27 + 行.人物, 行.头像帧)
                    if not 行.文字:
                        画.api_绘制(脸, 390, 328 + 42 * k)
                    else:
                        self.api_文字(arg_框, 行.文字, 24, 346 + 32 * k, 0, self.新闻行字)
                        画.api_绘制(脸, 390, 358 + 32 * k)
            else:
                self.api_文字(arg_框, 项.文字, 24, 330, 0, self.新闻字)
                画.api_绘制(美.api_帧("m", 27 + 项.人物, 2), 390, 344)
        elif 项.种类 == 消息种类_类.神明字幕:
            self.api_文字(arg_框, 项.文字, 220, 460, 7, self.神明字)
