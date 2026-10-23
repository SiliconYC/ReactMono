# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ tools/native_frame.hpp::Artwork与screens/draw.cpp::raw_picture。
# ◑ 导入
import struct
from pathlib import Path

from rich4.assets import 资源包_类
from rich4.graphics import 图像_类


# ◕ 功能
class 美术_类:
    """
    外部原MKF延迟读取和解帧缓存，不提供替代图片或内置商业资源。

    更新日志：
    2026.10.23 - 对应原生Artwork，供正式Pygame各屏复用。
    """

    文件名 = {
        "d": "data.mkf",
        "p": "panel.mkf",
        "m": "map.mkf",
        "e": "effect.mkf",
        "s": "speaking.mkf",
        "j": "jump.mkf",
        "h": "help.mkf",
    }

    def __init__(self, arg_目录: Path) -> None:
        self.目录 = arg_目录
        self.包: dict[str, 资源包_类] = {}
        self.数据: dict[tuple[str, int], bytes] = {}
        self.帧: dict[tuple[str, int, int], 图像_类] = {}

    def api_包(self, arg_库: str) -> 资源包_类:
        if arg_库 not in self.包:
            名 = self.文件名.get(arg_库, "help.mkf")
            路 = next(
                (p for p in self.目录.iterdir() if p.is_file() and p.name.lower() == 名), None
            )
            if 路 is None:
                raise ValueError(f"缺少原版资源：{名}")
            self.包[arg_库] = 资源包_类(路)
        return self.包[arg_库]

    def api_解码(self, arg_库: str, arg_条: int) -> bytes:
        键 = arg_库, arg_条
        if 键 not in self.数据:
            self.数据[键] = self.api_包(arg_库).api_解码(arg_条)
        return self.数据[键]

    def api_帧(self, arg_库: str, arg_条: int, arg_帧: int) -> 图像_类:
        键 = arg_库, arg_条, arg_帧
        if 键 not in self.帧:
            self.帧[键] = 图像_类.api_解码(self.api_解码(arg_库, arg_条), arg_帧)
        return self.帧[键]

    def api_帧数(self, arg_库: str, arg_条: int) -> int:
        数据 = self.api_解码(arg_库, arg_条)
        try:
            资源包_类.api_检查范围(0, 12, len(数据))
            签, 数, 偏 = struct.unpack_from("<4sII", 数据)
            if 签 not in (b"SPR\0", b"SMP\0") or 数 > (len(数据) - 12) // 12 or 偏 < 12 + 数 * 12:
                return 0
            资源包_类.api_检查范围(偏, 512 if 签 == b"SPR\0" else 0, len(数据))
            偏 += 512 if 签 == b"SPR\0" else 0
            for i in range(数):
                大 = struct.unpack_from("<I", 数据, 12 + i * 12 + 8)[0]
                资源包_类.api_检查范围(偏, 大, len(数据))
                偏 += 大
            return 数
        except ValueError:
            return 0

    def api_原图(self, arg_库: str, arg_条: int, arg_宽: int, arg_高: int) -> 图像_类:
        数据 = self.api_解码(arg_库, arg_条)
        数 = min(arg_宽 * arg_高, len(数据) // 2)
        色 = [v & 0x7FFF for v in struct.unpack_from(f"<{数}H", 数据)]
        return 图像_类(arg_宽, arg_高, 色 + [0] * (arg_宽 * arg_高 - 数))
