# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/graphics.cpp 和 src/assets.cpp::parse_graphics。
# ◑ 导入
import re
import struct
from array import array
from dataclasses import dataclass
from functools import cache, lru_cache
from sys import byteorder

from rich4.assets import 资源包_类


# ◕ 功能
@dataclass
class 图像_类:
    """
    保留 RGB555 与独立透明掩码，显示边界才转换为 RGBA。

    更新日志：
    2026.10.23 - 对应 Image/decode_frame/blit/to_argb8888；颜色LUT保留原绿通道缩放。
    """

    宽: int
    高: int
    像素: list[int]
    原点x: int = 0
    原点y: int = 0
    不透明: bytes = b""

    def __post_init__(self) -> None:
        if not 0 <= self.宽 <= 32767 or not 0 <= self.高 <= 32767:
            raise ValueError("图像尺寸越界")
        数量 = self.宽 * self.高
        if 数量 > 32 * 1024 * 1024 or 数量 != len(self.像素):
            raise ValueError("图像尺寸与存储不符或超过上限")
        if self.不透明 and len(self.不透明) != 数量:
            raise ValueError("透明掩码与尺寸不符")

    @classmethod
    def api_解码(cls, arg_数据: bytes, arg_帧: int) -> "图像_类":
        资源包_类.api_检查范围(0, 12, len(arg_数据))
        签名, 数量, 偏移 = struct.unpack_from("<4sII", arg_数据)
        if 签名 not in (b"SPR\0", b"SMP\0"):
            raise ValueError("不是 SPR/SMP")
        if 数量 > (len(arg_数据) - 12) // 12 or 偏移 < 12 + 数量 * 12:
            raise ValueError("图像表截断或与内容重叠")
        if not 0 <= arg_帧 < 数量:
            raise IndexError("帧索引越界")
        资源包_类.api_检查范围(偏移, 512 if 签名 == b"SPR\0" else 0, len(arg_数据))
        调色板 = struct.unpack_from("<256H", arg_数据, 偏移) if 签名 == b"SPR\0" else ()
        偏移 += 512 if 调色板 else 0
        目标: tuple[int, int, int, int, int, int] | None = None
        for 帧 in range(数量):
            宽, 高, x, y, 大小 = struct.unpack_from("<hhhhI", arg_数据, 12 + 帧 * 12)
            资源包_类.api_检查范围(偏移, 大小, len(arg_数据))
            if 帧 == arg_帧:
                目标 = (宽, 高, x, y, 大小, 偏移)
            偏移 += 大小
        if 目标 is None:
            raise IndexError("帧不存在")
        宽, 高, x, y, 大小, 偏移 = 目标
        if 宽 < 0 or 高 < 0 or 宽 * 高 > 32 * 1024 * 1024:
            raise ValueError("图像尺寸越界")
        if 调色板 and 大小 == 宽 * 高:
            索引 = arg_数据[偏移 : 偏移 + 大小]
            return cls(宽, 高, [调色板[i] for i in 索引], x, y, bytes(i != 0 for i in 索引))
        if not 调色板 and 大小 == 宽 * 高 * 2:
            return cls(宽, 高, list(struct.unpack_from(f"<{宽 * 高}H", arg_数据, 偏移)), x, y)
        raise ValueError("帧不是支持的原始 16 位或索引 8 位图像")

    @staticmethod
    @cache
    def _通道表() -> tuple[bytes, bytes, bytes, bytes, bytes, bytes]:
        return (
            bytes(((值 >> 2) & 31) * 255 // 31 for 值 in range(256)),
            bytes((值 & 31) * 255 // 31 for 值 in range(256)),
            bytes(值 >> 5 for 值 in range(256)),
            bytes((值 & 3) << 3 for 值 in range(256)),
            bytes((值 & 31) * 510 // 63 for 值 in range(256)),
            bytes([0] + [255] * 255),
        )

    def api_RGBA(self, arg_透明: bool = False) -> bytes:
        数 = len(self.像素)
        越界 = False
        try:
            原 = array("H", self.像素)
        except OverflowError:
            原 = array("H", (色 & 0xFFFF for 色 in self.像素))
            越界 = True
        if byteorder != "little":
            原.byteswap()
        原字节 = 原.tobytes()
        低, 高 = 原字节[::2], 原字节[1::2]
        红表, 蓝表, 低绿表, 高绿表, 绿表, 透明表 = self._通道表()
        # 合并每字节中的不相交绿位；大整数或运算无跨字节进位，避免逐像素Python调用。
        绿位 = (
            int.from_bytes(低.translate(低绿表), "little")
            | int.from_bytes(高.translate(高绿表), "little")
        ).to_bytes(数, "little")
        输出 = bytearray(数 * 4)
        输出[0::4], 输出[1::4], 输出[2::4] = (
            高.translate(红表),
            绿位.translate(绿表),
            低.translate(蓝表),
        )
        if self.不透明:
            if len(self.不透明) < 数:
                raise IndexError("RGBA掩码短于像素")
            输出[3::4] = self.不透明[:数].translate(透明表)
        elif arg_透明:
            色键 = (
                bytes(0 if 色 == 0 else 1 for 色 in self.像素)
                if 越界
                else (int.from_bytes(低, "little") | int.from_bytes(高, "little")).to_bytes(
                    数, "little"
                )
            )
            输出[3::4] = 色键.translate(透明表)
        else:
            输出[3::4] = b"\xff" * 数
        return bytes(输出)

    def api_PPM(self) -> bytes:
        rgba = self.api_RGBA()
        像素 = bytearray()
        for 位置 in range(0, len(rgba), 4):
            像素.extend(rgba[位置 : 位置 + 3])
        return f"P6\n{self.宽} {self.高}\n255\n".encode() + 像素

    @staticmethod
    @lru_cache(maxsize=512)
    def _不透明段(arg_掩码: bytes, arg_宽: int) -> tuple[tuple[tuple[int, int], ...], ...]:
        # SPR掩码不可变，以其值和行宽缓存连续可见段；换色不影响段表。
        return tuple(
            tuple(项.span() for 项 in re.finditer(rb"[^\x00]+", arg_掩码[起 : 起 + arg_宽]))
            for 起 in range(0, len(arg_掩码), arg_宽)
        )

    def api_绘制(
        self,
        arg_源: "图像_类",
        arg_x: int,
        arg_y: int,
        arg_裁剪: tuple[int, int, int, int] | None = None,
        arg_强制不透明: bool = False,
    ) -> None:
        左 = arg_x - arg_源.原点x
        顶 = arg_y - arg_源.原点y
        裁左, 裁顶, 裁右, 裁底 = arg_裁剪 if arg_裁剪 is not None else (0, 0, self.宽, self.高)
        起x, 终x = max(0, 裁左, 左), min(self.宽, 裁右, 左 + arg_源.宽)
        起y, 终y = max(0, 裁顶, 顶), min(self.高, 裁底, 顶 + arg_源.高)
        if 起x >= 终x or 起y >= 终y:
            return
        源像素 = arg_源.像素.copy() if arg_源 is self else arg_源.像素
        掩码 = arg_源.不透明
        目标掩码 = bytearray(self.不透明)
        有效掩码 = not 掩码 or len(掩码) == arg_源.宽 * arg_源.高
        段表 = (
            self._不透明段(掩码, arg_源.宽)
            if 掩码 and isinstance(掩码, bytes) and 有效掩码 and not arg_强制不透明
            else None
        )
        if 有效掩码 and (arg_强制不透明 or 段表 is not None):
            for y in range(起y, 终y):
                段组 = ((起x - 左, 终x - 左),) if arg_强制不透明 else 段表[y - 顶]
                for 段左, 段右 in 段组:
                    开, 末 = max(起x, 左 + 段左), min(终x, 左 + 段右)
                    if 开 >= 末:
                        continue
                    源 = (y - 顶) * arg_源.宽 + 开 - 左
                    目标 = y * self.宽 + 开
                    self.像素[目标 : 目标 + 末 - 开] = 源像素[源 : 源 + 末 - 开]
                    if 目标掩码:
                        目标掩码[目标 : 目标 + 末 - 开] = b"\x01" * (末 - 开)
            self.不透明 = bytes(目标掩码)
            return
        for y in range(起y, 终y):
            for x in range(起x, 终x):
                序号 = (y - 顶) * arg_源.宽 + x - 左
                可见 = 掩码[序号] != 0 if 掩码 else 源像素[序号] != 0
                if arg_强制不透明 or 可见:
                    目标 = y * self.宽 + x
                    self.像素[目标] = 源像素[序号]
                    if 目标掩码:
                        目标掩码[目标] = 1
        self.不透明 = bytes(目标掩码)
