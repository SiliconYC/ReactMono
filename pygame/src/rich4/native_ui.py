# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ tools/native_ui.hpp；FreeType仅负责字形，不含游戏规则或C++引擎。
# ◑ 导入
import ctypes as c
import ctypes.util
import os
from dataclasses import dataclass
from pathlib import Path

from rich4.graphics import 图像_类


# ◕ 功能
class 原生界面_类:
    """
    原CP950/UTF8消费边界、RGB555颜色与半开矩形绘制。

    更新日志：
    2026.10.24 - 不以宿主Unicode替换策略改变坏字节后的字符位置。
    """

    墨色, 纸色, 蓝色 = 4194, 31671, 2320

    @staticmethod
    def api_繁中(arg_文: bytes) -> str:
        片, 位 = [], 0
        while 位 < len(arg_文):
            跳 = 2 if arg_文[位] >= 0x81 and 位 + 1 < len(arg_文) else 1
            字 = arg_文[位 : 位 + 跳]
            # Python的CP950复用了Big5日文区；原iconv CP950拒绝这249项。
            if 跳 == 2 and 0xC6A1 <= int.from_bytes(字, "big") <= 0xC7FC:
                片.append("?")
                位 += 跳
                continue
            try:
                片.append(字.decode("cp950"))
            except UnicodeDecodeError:
                片.append("?")
            位 += 跳
        return "".join(片)

    @staticmethod
    def api_原串(arg_文: str | bytes) -> bytes:
        return (
            arg_文 if isinstance(arg_文, bytes) else arg_文.encode("utf-8", errors="surrogatepass")
        )

    @classmethod
    def api_码点(cls, arg_文: str | bytes) -> list[int]:
        文, 位, 结果 = cls.api_原串(arg_文), 0, []
        while 位 < len(文):
            首 = 文[位]
            位 += 1
            值, 余 = 首, 0
            if 首 >= 0xF0:
                值, 余 = 首 & 7, 3
            elif 首 >= 0xE0:
                值, 余 = 首 & 15, 2
            elif 首 >= 0xC0:
                值, 余 = 首 & 31, 1
            elif 首 >= 0x80:
                结果.append(63)
                continue
            有效 = True
            for _ in range(余):
                if 位 >= len(文) or 文[位] & 0xC0 != 0x80:
                    有效 = False
                    break
                值 = (值 << 6) | (文[位] & 63)
                位 += 1
            结果.append(值 if 有效 and 值 <= 0x10FFFF else 63)
        return 结果

    @staticmethod
    def api_颜色(arg_r: int, arg_g: int, arg_b: int) -> int:
        return (
            ((arg_r & 0xFFFFFFFF) >> 3) << 10
            | ((arg_g & 0xFFFFFFFF) >> 3) << 5
            | ((arg_b & 0xFFFFFFFF) >> 3)
        ) & 65535

    @classmethod
    def api_玩家色(cls, arg_rgb: int) -> int:
        return cls.api_颜色((arg_rgb >> 16) & 255, (arg_rgb >> 8) & 255, arg_rgb & 255)

    @staticmethod
    def api_填充(arg_图: 图像_类, arg_框: tuple[int, int, int, int], arg_色: int) -> None:
        左, 顶, 右, 底 = arg_框
        左, 右 = min(max(左, 0), arg_图.宽), min(max(右, 0), arg_图.宽)
        顶, 底 = min(max(顶, 0), arg_图.高), min(max(底, 0), arg_图.高)
        if 左 >= 右 or 顶 >= 底:
            return
        行 = [arg_色 & 65535] * (右 - 左)
        for y in range(顶, 底):
            arg_图.像素[y * arg_图.宽 + 左 : y * arg_图.宽 + 右] = 行

    @classmethod
    def api_边框(cls, arg_图: 图像_类, arg_框: tuple[int, int, int, int], arg_色: int) -> None:
        左, 顶, 右, 底 = arg_框
        for 框 in (
            (左, 顶, 右, 顶 + 1),
            (左, 底 - 1, 右, 底),
            (左, 顶, 左 + 1, 底),
            (右 - 1, 顶, 右, 底),
        ):
            cls.api_填充(arg_图, 框, arg_色)

    @staticmethod
    def api_包含(arg_框: tuple[int, int, int, int], arg_x: int, arg_y: int) -> bool:
        return arg_框[0] <= arg_x < arg_框[2] and arg_框[1] <= arg_y < arg_框[3]


class _FT通用_类(c.Structure):
    """
    FreeType稳定C ABI的FT_Generic前缀。

    更新日志：
    2026.10.24 - 只读取公开字槽前缀，不声明或访问字体库私有字段。
    """

    _fields_ = [("数据", c.c_void_p), ("终结", c.c_void_p)]


class _FT向量_类(c.Structure):
    """
    FT_Vector中的FT_Pos使用宿主C long。

    更新日志：
    2026.10.24 - 按Win32/LP64各自ABI自然对齐。
    """

    _fields_ = [("x", c.c_long), ("y", c.c_long)]


class _FT位图_类(c.Structure):
    """
    FT_Bitmap公开布局，保留有符号行距和原像素模式。

    更新日志：
    2026.10.24 - 遮罩复制到Python后不再引用临时FT字槽内存。
    """

    _fields_ = [
        ("行数", c.c_uint),
        ("宽", c.c_uint),
        ("行距", c.c_int),
        ("缓冲", c.c_void_p),
        ("灰阶数", c.c_ushort),
        ("模式", c.c_ubyte),
        ("调色模式", c.c_ubyte),
        ("调色板", c.c_void_p),
    ]


class _FT字槽_类(c.Structure):
    """
    FT_GlyphSlotRec截至bitmap_top的公开前缀。

    更新日志：
    2026.10.24 - metrics八个FT_Pos及两个FT_Fixed均为C long。
    """

    _fields_ = [
        ("库", c.c_void_p),
        ("字面", c.c_void_p),
        ("后继", c.c_void_p),
        ("编号", c.c_uint),
        ("通用", _FT通用_类),
        ("度量", c.c_long * 8),
        ("横前进", c.c_long),
        ("竖前进", c.c_long),
        ("前进", _FT向量_类),
        ("格式", c.c_uint),
        ("位图", _FT位图_类),
        ("位图左", c.c_int),
        ("位图顶", c.c_int),
    ]


class _FT字面_类(c.Structure):
    """
    FT_FaceRec截至glyph的公开前缀。

    更新日志：
    2026.10.24 - 不猜测padding；由ctypes按C指针、long和short对齐。
    """

    _fields_ = [
        ("五项长量", c.c_long * 5),
        ("家族", c.c_char_p),
        ("风格", c.c_char_p),
        ("固定尺寸数", c.c_int),
        ("固定尺寸", c.c_void_p),
        ("字图数", c.c_int),
        ("字图", c.c_void_p),
        ("通用", _FT通用_类),
        ("边界", c.c_long * 4),
        ("em", c.c_ushort),
        ("七项短量", c.c_short * 7),
        ("字槽", c.POINTER(_FT字槽_类)),
    ]


@dataclass(frozen=True)
class 字形_类:
    """
    与原Glyph相同的灰度遮罩、原点和整数前进量。

    更新日志：
    2026.10.24 - 缓存与FT_Load_Char随后覆盖的内存隔离。
    """

    宽: int
    高: int
    左: int
    顶: int
    前进: int
    遮罩: bytes


@dataclass(frozen=True)
class 文字样式_类:
    """
    原TextStyle的块布局、粗体/阴影/描边参数。

    更新日志：
    2026.10.24 - 默认颜色0与普通draw默认墨色不同，按源保留。
    """

    大小: int = 16
    颜色: int = 0
    粗体: bool = False
    阴影: bool = False
    描边: bool = False
    效果: int = 0
    行距: int = 2


class 字体_类:
    """
    与固定原生版同一FreeType调用和RGB555混合，规则仍完全由Python执行。

    更新日志：
    2026.10.24 - 支持宿主FreeType及Pygame随附库；字体本身从外部读取。
    2026.10.24 - 原单色遮罩用连续行段复制，不改变灰度路径或目标透明遮罩。
    """

    @staticmethod
    def _载库(arg_库: str | None) -> tuple[c.CDLL, str]:
        候选 = [arg_库] if arg_库 else []
        if not arg_库:
            找 = ctypes.util.find_library("freetype")
            if 找:
                候选.append(找)
            for 名 in (
                "/opt/homebrew/opt/freetype/lib/libfreetype.6.dylib",
                "/usr/local/opt/freetype/lib/libfreetype.6.dylib",
            ):
                if Path(名).is_file():
                    候选.append(名)
            import pygame._freetype

            路 = Path(pygame._freetype.__file__)
            候选.append(str(路))
            for 根 in (路.parent, 路.parent.parent / "pygame.libs"):
                if 根.is_dir():
                    候选.extend(str(p) for p in 根.glob("*freetype*.dll"))
                    候选.extend(str(p) for p in 根.glob("*freetype*.so*"))
        for 名 in 候选:
            try:
                库 = c.CDLL(名)
                getattr(库, "FT_Init_FreeType")
                return 库, 名
            except (OSError, AttributeError):
                continue
        raise RuntimeError("Cannot load FreeType from the host or Pygame installation")

    def __init__(self, arg_路径: Path, arg_库: str | None = None) -> None:
        self._库 = c.c_void_p()
        self._字面 = c.POINTER(_FT字面_类)()
        self._缓存: dict[tuple[int, int, bool], 字形_类] = {}
        self._接口, self.库路径 = self._载库(arg_库)
        self._接口.FT_Init_FreeType.argtypes = [c.POINTER(c.c_void_p)]
        self._接口.FT_New_Face.argtypes = [
            c.c_void_p,
            c.c_char_p,
            c.c_long,
            c.POINTER(c.POINTER(_FT字面_类)),
        ]
        self._接口.FT_Set_Pixel_Sizes.argtypes = [c.POINTER(_FT字面_类), c.c_uint, c.c_uint]
        self._接口.FT_Load_Char.argtypes = [c.POINTER(_FT字面_类), c.c_ulong, c.c_int32]
        self._接口.FT_Done_Face.argtypes = [c.POINTER(_FT字面_类)]
        self._接口.FT_Done_FreeType.argtypes = [c.c_void_p]
        for 名 in (
            "FT_Init_FreeType",
            "FT_New_Face",
            "FT_Set_Pixel_Sizes",
            "FT_Load_Char",
            "FT_Done_Face",
            "FT_Done_FreeType",
        ):
            getattr(self._接口, 名).restype = c.c_int
        if self._接口.FT_Init_FreeType(c.byref(self._库)):
            raise RuntimeError("Cannot initialize FreeType")
        if self._接口.FT_New_Face(self._库, os.fsencode(arg_路径), 0, c.byref(self._字面)):
            self.api_关闭()
            raise RuntimeError(f"Cannot load Chinese font: {arg_路径}")

    def api_关闭(self) -> None:
        if self._字面:
            self._接口.FT_Done_Face(self._字面)
            self._字面 = c.POINTER(_FT字面_类)()
        if self._库.value:
            self._接口.FT_Done_FreeType(self._库)
            self._库.value = None

    def __del__(self) -> None:
        if hasattr(self, "_接口"):
            self.api_关闭()

    def _字形(self, arg_字: int, arg_大小: int, arg_单色: bool = False) -> 字形_类:
        键 = (arg_大小, arg_字, arg_单色)
        if 键 in self._缓存:
            return self._缓存[键]
        if not self._字面:
            raise RuntimeError("font is closed")
        if self._接口.FT_Set_Pixel_Sizes(self._字面, 0, arg_大小) or self._接口.FT_Load_Char(
            self._字面, arg_字, 4
        ):
            raise RuntimeError("Cannot rasterize font glyph")
        槽 = self._字面.contents.字槽.contents
        图, 遮 = 槽.位图, bytearray()
        for 行 in range(图.行数):
            偏 = (行 if 图.行距 >= 0 else 图.行数 - 1 - 行) * abs(图.行距)
            片 = c.string_at(图.缓冲 + 偏, abs(图.行距))
            for 列 in range(图.宽):
                遮.append(
                    ((片[列 // 8] >> (7 - 列 % 8)) & 1) * 255
                    if 图.模式 == 1
                    else (255 if 片[列] >= 56 else 0)
                    if arg_单色
                    else 片[列]
                )
        字 = 字形_类(图.宽, 图.行数, 槽.位图左, 槽.位图顶, 槽.前进.x >> 6, bytes(遮))
        self._缓存[键] = 字
        return 字

    def api_测量(self, arg_文: str | bytes, arg_大小: int = 16, arg_单色: bool = False) -> int:
        return sum(self._字形(字, arg_大小, arg_单色).前进 for 字 in 原生界面_类.api_码点(arg_文))

    def api_墨框(
        self, arg_文: str | bytes, arg_大小: int = 16, arg_间距: int = 0, arg_单色: bool = False
    ) -> tuple[int, int, int, int]:
        框, x, 有 = (0, 0, 0, 0), 0, False
        for 号 in 原生界面_类.api_码点(arg_文):
            字 = self._字形(号, arg_大小, arg_单色)
            if 字.宽 and 字.高:
                墨 = (x + 字.左, arg_大小 - 字.顶, x + 字.左 + 字.宽, arg_大小 - 字.顶 + 字.高)
                框 = (
                    (min(框[0], 墨[0]), min(框[1], 墨[1]), max(框[2], 墨[2]), max(框[3], 墨[3]))
                    if 有
                    else 墨
                )
                有 = True
            x += 字.前进 + arg_间距
        return 框

    @staticmethod
    def _绘二值(
        arg_图: 图像_类,
        arg_字: 字形_类,
        arg_x: int,
        arg_y: int,
        arg_色: int,
    ) -> None:
        左, 右 = max(0, arg_x), min(arg_图.宽, arg_x + arg_字.宽)
        顶, 底 = max(0, arg_y), min(arg_图.高, arg_y + arg_字.高)
        if 左 >= 右 or 顶 >= 底:
            return
        # 原单色只有0/255，覆盖时RGB555最高位被丢弃。普通blit会更新目标掩码，不能代用。
        段表 = 图像_类._不透明段(arg_字.遮罩, arg_字.宽)
        色 = arg_色 & 32767
        for y in range(顶, 底):
            for 段左, 段右 in 段表[y - arg_y]:
                开, 末 = max(左, arg_x + 段左), min(右, arg_x + 段右)
                if 开 < 末:
                    i = y * arg_图.宽 + 开
                    arg_图.像素[i : i + 末 - 开] = [色] * (末 - 开)

    def api_绘制(
        self,
        arg_图: 图像_类,
        arg_文: str | bytes,
        arg_x: int,
        arg_y: int,
        arg_大小: int = 16,
        arg_色: int = 原生界面_类.墨色,
        arg_折宽: int = 0,
        arg_单色: bool = False,
    ) -> None:
        起x, x, y = arg_x, arg_x, arg_y
        for 号 in 原生界面_类.api_码点(arg_文):
            if 号 == 10:
                x, y = 起x, y + arg_大小 + 5
                continue
            字 = self._字形(号, arg_大小, arg_单色)
            if arg_折宽 > 0 and x > 起x and x + 字.前进 > 起x + arg_折宽:
                x, y = 起x, y + arg_大小 + 5
            if arg_单色:
                self._绘二值(arg_图, 字, x + 字.左, y + arg_大小 - 字.顶, arg_色)
                x += 字.前进
                continue
            for 行 in range(字.高):
                dy = y + arg_大小 - 字.顶 + 行
                if not 0 <= dy < arg_图.高:
                    continue
                for 列 in range(字.宽):
                    dx = x + 字.左 + 列
                    if not 0 <= dx < arg_图.宽:
                        continue
                    盖 = 字.遮罩[行 * 字.宽 + 列]
                    if not 盖:
                        continue
                    索 = dy * arg_图.宽 + dx
                    背, 混 = arg_图.像素[索], 0
                    for 移 in (0, 5, 10):
                        前色, 背色 = (arg_色 >> 移) & 31, (背 >> 移) & 31
                        混 |= ((前色 * 盖 + 背色 * (255 - 盖) + 127) // 255) << 移
                    arg_图.像素[索] = 混
            x += 字.前进

    def api_块范围(self, arg_文: str | bytes, arg_式: 文字样式_类) -> tuple[int, int]:
        加 = int(arg_式.粗体) + int(arg_式.阴影) + (2 if arg_式.描边 else 0)
        行 = 原生界面_类.api_原串(arg_文).split(b"\n")
        宽 = max(self.api_测量(文, arg_式.大小) + 加 for 文 in 行)
        高 = (
            len(行) * (arg_式.大小 + arg_式.行距)
            - arg_式.行距
            + (2 if arg_式.阴影 or arg_式.描边 else 0)
        )
        return 宽, 高

    def api_绘块(
        self,
        arg_图: 图像_类,
        arg_文: str | bytes,
        arg_x: int,
        arg_y: int,
        arg_式: 文字样式_类,
        arg_居中: bool = False,
    ) -> None:
        块宽 = self.api_块范围(arg_文, arg_式)[0] if arg_居中 else 0
        for i, 文 in enumerate(原生界面_类.api_原串(arg_文).split(b"\n")):
            x, y = arg_x, arg_y + i * (arg_式.大小 + arg_式.行距)
            if arg_居中:
                差 = (
                    块宽
                    - self.api_测量(文, arg_式.大小)
                    - int(arg_式.粗体)
                    - int(arg_式.阴影)
                    - (2 if arg_式.描边 else 0)
                )
                x += abs(差) // 2 * (-1 if 差 < 0 else 1)

            def 描(arg_dx: int, arg_dy: int, arg_色: int) -> None:
                self.api_绘制(arg_图, 文, x + arg_dx, y + arg_dy, arg_式.大小, arg_色)
                if arg_式.粗体:
                    self.api_绘制(arg_图, 文, x + arg_dx + 1, y + arg_dy, arg_式.大小, arg_色)

            if arg_式.描边:
                for dx, dy in ((0, 1), (2, 1), (1, 0), (1, 2)):
                    描(dx, dy, arg_式.效果)
                描(1, 1, arg_式.颜色)
            else:
                if arg_式.阴影:
                    描(1, 1, arg_式.效果)
                描(0, 0, arg_式.颜色)
