# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/graphics.cpp 和 src/assets.cpp::parse_graphics。
# ◑ 导入
import struct
from dataclasses import dataclass

from rich4.assets import 资源包_类


# ◕ 功能
@dataclass
class 图像_类:
    """
    保留 RGB555 与独立透明掩码，显示边界才转换为 RGBA。

    更新日志：
    2026.10.23 - 对应 Image/decode_frame/blit/to_argb8888。
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

    def api_RGBA(self, arg_透明: bool = False) -> bytes:
        输出 = bytearray(len(self.像素) * 4)
        for i, 色 in enumerate(self.像素):
            # C++ 保留 RGB555→565 后绿色的最低位为零，不能用常规 5→8 扩展替代。
            绿色 = ((色 >> 5) & 31) * 2 * 255 // 63
            alpha = 255
            if self.不透明:
                alpha = 255 if self.不透明[i] else 0
            elif arg_透明 and 色 == 0:
                alpha = 0
            输出[i * 4 : i * 4 + 4] = bytes(
                [
                    ((色 >> 10) & 31) * 255 // 31,
                    绿色,
                    (色 & 31) * 255 // 31,
                    alpha,
                ]
            )
        return bytes(输出)

    def api_PPM(self) -> bytes:
        rgba = self.api_RGBA()
        像素 = bytearray()
        for 位置 in range(0, len(rgba), 4):
            像素.extend(rgba[位置 : 位置 + 3])
        return f"P6\n{self.宽} {self.高}\n255\n".encode() + 像素

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
        源像素 = arg_源.像素.copy() if arg_源 is self else arg_源.像素
        掩码 = arg_源.不透明
        目标掩码 = bytearray(self.不透明)
        for y in range(max(0, 裁顶, 顶), min(self.高, 裁底, 顶 + arg_源.高)):
            for x in range(max(0, 裁左, 左), min(self.宽, 裁右, 左 + arg_源.宽)):
                序号 = (y - 顶) * arg_源.宽 + x - 左
                可见 = 掩码[序号] != 0 if 掩码 else 源像素[序号] != 0
                if arg_强制不透明 or 可见:
                    目标 = y * self.宽 + x
                    self.像素[目标] = 源像素[序号]
                    if 目标掩码:
                        目标掩码[目标] = 1
        self.不透明 = bytes(目标掩码)
