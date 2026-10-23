# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/terrain.cpp；16.16扫描和有符号除法须按原整数规则执行。
# ◑ 导入
import struct
from collections.abc import Sequence
from dataclasses import dataclass

from rich4.assets import 资源包_类
from rich4.graphics import 图像_类


# ◕ 功能
@dataclass
class 地面_类:
    """
    GND调色板、索引图和32×32纹理，保留原保留字段。

    更新日志：
    2026.10.23 - 对应 terrain::Ground/parse_ground/render_overview。
    """

    宽瓦片: int
    高瓦片: int
    保留: int
    调色板: tuple[int, ...]
    索引: list[int]
    纹理: bytes

    def api_瓦片数(self) -> int:
        return len(self.纹理) // 1024

    def api_瓦片(self, arg_号: int) -> bytes:
        if not 0 <= arg_号 < self.api_瓦片数():
            raise IndexError("GND瓦片索引越界")
        return self.纹理[arg_号 * 1024 : (arg_号 + 1) * 1024]

    @classmethod
    def api_解码(cls, arg_数据: bytes) -> "地面_类":
        资源包_类.api_检查范围(0, 16, len(arg_数据))
        签名, 宽, 高, 数, 保留 = struct.unpack_from("<4sHHII", arg_数据)
        if 签名 != b"GND\0" or 宽 == 0 or 高 == 0 or 数 == 0:
            raise ValueError("GND签名、尺寸或瓦片数量无效")
        资源包_类.api_检查范围(16, 512, len(arg_数据))
        调色 = struct.unpack_from("<256H", arg_数据, 16)
        索引数 = 宽 * 高
        if 索引数 > (len(arg_数据) - 528) // 2:
            raise ValueError("GND瓦片索引截断")
        偏移 = 528 + 索引数 * 2
        if 数 > (len(arg_数据) - 偏移) // 1024:
            raise ValueError("GND纹理截断")
        索引 = list(struct.unpack_from(f"<{索引数}H", arg_数据, 528))
        if any(i >= 数 for i in 索引):
            raise ValueError("GND引用不存在的瓦片")
        return cls(宽, 高, 保留, 调色, 索引, arg_数据[偏移 : 偏移 + 数 * 1024])

    def api_总览(self, arg_像素上限: int = 16 * 1024 * 1024) -> 图像_类:
        宽, 高 = self.宽瓦片 * 32, self.高瓦片 * 32
        if 宽 <= 0 or 高 <= 0 or 宽 > arg_像素上限 // 高:
            raise ValueError("GND总览超过像素上限")
        if len(self.索引) != self.宽瓦片 * self.高瓦片:
            raise ValueError("GND索引数与尺寸不符")
        图 = 图像_类(宽, 高, [0] * (宽 * 高))
        for 行 in range(self.高瓦片):
            for 列 in range(self.宽瓦片):
                瓦 = self.api_瓦片(self.索引[行 * self.宽瓦片 + 列])
                for y in range(32):
                    起 = (行 * 32 + y) * 宽 + 列 * 32
                    图.像素[起 : 起 + 32] = [self.调色板[i] for i in 瓦[y * 32 : (y + 1) * 32]]
        return 图


@dataclass(slots=True)
class 扫描行_类:
    """
    每次瓦片绘制独占临时扫描状态，纹理侧由原边方向决定。

    更新日志：
    2026.10.23 - 对应 Scanline。
    """

    左: int = 0x7FFF0000
    右: int = -2147483648
    左u: int = 0
    左v: int = 0
    右u: int = 0
    右v: int = 0


class 地形_类:
    """
    原16.16四边形扫描；点顺序为(y,x)，裁剪框为(左,顶,右,底)。

    更新日志：
    2026.10.23 - 对应 draw_tile与其全部有符号整数辅助函数。
    """

    @staticmethod
    def _整数(arg_值: int) -> int:
        return ((arg_值 + 0x80000000) & 0xFFFFFFFF) - 0x80000000

    @classmethod
    def _定点(cls, arg_值: int) -> int:
        return cls._整数(arg_值 << 16)

    @staticmethod
    def _除(arg_值: int, arg_除数: int) -> int:
        商 = abs(arg_值) // abs(arg_除数)
        return -商 if (arg_值 < 0) != (arg_除数 < 0) else 商

    @classmethod
    def _步进(cls, arg_值: int, arg_步: int, arg_数: int = 1) -> int:
        return cls._整数(arg_值 + arg_步 * arg_数)

    @classmethod
    def _扫边(
        cls,
        arg_首: tuple[int, int],
        arg_末: tuple[int, int],
        arg_首纹: tuple[int, int],
        arg_末纹: tuple[int, int],
        arg_纹差: tuple[int, int],
        arg_框: tuple[int, int, int, int],
        arg_行: list[扫描行_类],
        arg_首行: int,
    ) -> int:
        高 = arg_末[0] - arg_首[0]
        if 高 == 0:
            return arg_首行
        if not -32768 <= 高 <= 32767:
            raise ValueError("地形边高超出原有符号16位域")
        顶, 底, 纹 = arg_首, arg_末, arg_首纹
        if 高 < 0:
            顶, 底, 纹 = arg_末, arg_首, arg_末纹
        if 底[0] <= arg_框[1] or 顶[0] >= arg_框[3]:
            return arg_首行
        顶行, 底行 = max(顶[0], arg_框[1]), min(底[0], arg_框[3])
        arg_首行 = min(arg_首行, 顶行)
        du, dv = (cls._除(cls._定点(值), 高) for 值 in arg_纹差)
        u = cls._整数(cls._定点(纹[0]) | (0xFFFF if du < 0 else 0))
        v = cls._整数(cls._定点(纹[1]) | (0xFFFF if dv < 0 else 0))
        x = cls._定点(顶[1])
        dx = cls._除(cls._整数(cls._定点(底[1]) - x), abs(高))
        跳过 = 顶行 - 顶[0]
        u, v, x = cls._步进(u, du, 跳过), cls._步进(v, dv, 跳过), cls._步进(x, dx, 跳过)
        for y in range(顶行, 底行):
            行 = arg_行[y]
            已改 = False
            if x < 行.左:
                行.左, 已改 = x, True
            if x > 行.右:
                行.右, 已改 = x, True
            if 已改:
                if 高 < 0:
                    行.左u, 行.左v = u, v
                else:
                    行.右u, 行.右v = u, v
            u, v, x = cls._步进(u, du), cls._步进(v, dv), cls._步进(x, dx)
        return arg_首行

    @classmethod
    def api_绘瓦片(
        cls,
        arg_目标: 图像_类,
        arg_纹理: bytes,
        arg_调色: Sequence[int],
        arg_角: Sequence[tuple[int, int]],
        arg_框: tuple[int, int, int, int],
    ) -> None:
        宽, 高 = arg_目标.宽, arg_目标.高
        if not 0 < 宽 <= 32767 or not 0 < 高 <= 32767 or len(arg_目标.像素) != 宽 * 高:
            raise ValueError("地形目标尺寸或存储错误")
        if arg_目标.不透明 and len(arg_目标.不透明) != 宽 * 高:
            raise ValueError("地形目标掩码存储错误")
        if len(arg_纹理) != 1024 or len(arg_调色) != 256 or len(arg_角) != 4:
            raise ValueError("地形参数维度不符")
        if any(not -32768 <= 值 <= 32767 for 点 in arg_角 for 值 in 点):
            raise ValueError("地形角点超出原16位类型域")
        左, 顶, 右, 底 = (
            max(arg_框[0], 0),
            max(arg_框[1], 0),
            min(arg_框[2], 宽),
            min(arg_框[3], 高),
        )
        if 左 >= 右 or 顶 >= 底:
            return
        框 = 左, 顶, 右, 底
        纹 = ((0, 0), (31, 0), (31, 31), (0, 31))
        差 = ((32, 0), (0, 32), (-32, 0), (0, -32))
        行组 = [扫描行_类() for _ in range(高)]
        首行 = 高
        for 边 in range(4):
            后 = (边 + 1) % 4
            首行 = cls._扫边(arg_角[边], arg_角[后], 纹[边], 纹[后], 差[边], 框, 行组, 首行)
        掩码 = bytearray(arg_目标.不透明)
        for y in range(首行, 高):
            行 = 行组[y]
            if 行.左 == 0x7FFF0000:
                break
            行左, 行右 = 行.左 >> 16, 行.右 >> 16
            跨 = 行右 - 行左
            if 跨 <= 0 or 行右 <= 左 or 行左 >= 右:
                continue
            du = cls._除(cls._整数(行.右u - 行.左u), 跨)
            dv = cls._除(cls._整数(行.右v - 行.左v), 跨)
            起, 终 = max(行左, 左), min(行右, 右)
            u, v = cls._步进(行.左u, du, 起 - 行左), cls._步进(行.左v, dv, 起 - 行左)
            for x in range(起, 终):
                纹x, 纹y = u >> 16 & 31, v >> 16 & 31
                号 = y * 宽 + x
                arg_目标.像素[号] = arg_调色[arg_纹理[纹y * 32 + 纹x]]
                if 掩码:
                    掩码[号] = 1
                u, v = cls._步进(u, du), cls._步进(v, dv)
        arg_目标.不透明 = bytes(掩码)
