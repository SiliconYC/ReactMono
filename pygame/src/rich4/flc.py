# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/flc.cpp；原行为依据 fcn_0045144f / fcn_00450f04。
# ◑ 导入
import struct

from rich4.assets import 资源包_类
from rich4.graphics import 图像_类


# ◕ 功能
class 动画_类:
    """
    FLC 增量帧解码；透明取决于索引零，调色板变化作用于已有像素。

    更新日志：
    2026.10.23 - COLOR_256、DELTA_FLC、BLACK、BYTE_RUN、COPY 与倒带。
    """

    def __init__(self, arg_数据: bytes) -> None:
        if len(arg_数据) < 128 or self._整数(arg_数据, 4, 2) != 0xAF12:
            raise ValueError("不是 FLC 或文件头截断")
        self.数据 = arg_数据
        self.帧数 = self._整数(arg_数据, 6, 2)
        self.宽 = self._整数(arg_数据, 8, 2)
        self.高 = self._整数(arg_数据, 10, 2)
        self.间隔毫秒 = self._整数(arg_数据, 16, 4)
        if not 0 < self.宽 <= 4096 or not 0 < self.高 <= 4096:
            raise ValueError("FLC 尺寸越界")
        self.api_倒带()

    @staticmethod
    def _整数(
        arg_数据: bytes,
        arg_位置: int,
        arg_字节: int,
        arg_有符号: bool = False,
    ) -> int:
        资源包_类.api_检查范围(arg_位置, arg_字节, len(arg_数据))
        return int.from_bytes(arg_数据[arg_位置 : arg_位置 + arg_字节], "little", signed=arg_有符号)

    def api_倒带(self) -> None:
        self.游标 = 128
        self.已解帧 = 0
        self.像素索引 = bytearray(self.宽 * self.高)
        self.调色板 = [0] * 256

    def api_下一帧(self) -> bool:
        if self.已解帧 >= self.帧数:
            return False
        while self.游标 + 6 <= len(self.数据):
            大小 = self._整数(self.数据, self.游标, 4)
            类型 = self._整数(self.数据, self.游标 + 4, 2)
            if 大小 < 6:
                raise ValueError("FLC 块长度无效")
            资源包_类.api_检查范围(self.游标, 大小, len(self.数据))
            块 = self.数据[self.游标 : self.游标 + 大小]
            self.游标 += 大小
            if 类型 != 0xF1FA:
                continue
            self._应用帧(块)
            self.已解帧 += 1
            return True
        return False

    def _应用帧(self, arg_帧: bytes) -> None:
        资源包_类.api_检查范围(0, 16, len(arg_帧))
        数量 = self._整数(arg_帧, 6, 2)
        位置 = 16
        for _ in range(数量):
            大小 = self._整数(arg_帧, 位置, 4)
            类型 = self._整数(arg_帧, 位置 + 4, 2)
            if 大小 < 6:
                raise ValueError("FLC 子块长度无效")
            资源包_类.api_检查范围(位置, 大小, len(arg_帧))
            数据 = arg_帧[位置 + 6 : 位置 + 大小]
            if 类型 == 4:
                self._调色(数据)
            elif 类型 == 7:
                self._增量(数据)
            elif 类型 == 13:
                self.像素索引[:] = bytes(len(self.像素索引))
            elif 类型 == 15:
                self._游程(数据)
            elif 类型 == 16:
                资源包_类.api_检查范围(0, len(self.像素索引), len(数据))
                self.像素索引[:] = 数据[: len(self.像素索引)]
            # C++/原播放器忽略 PSTAMP 缩略图与未知子块。
            位置 += 大小

    def _调色(self, arg_数据: bytes) -> None:
        数量 = self._整数(arg_数据, 0, 2)
        位置 = 2
        索引 = 0
        for _ in range(数量):
            索引 += self._整数(arg_数据, 位置, 1)
            长度 = self._整数(arg_数据, 位置 + 1, 1) or 256
            位置 += 2
            资源包_类.api_检查范围(位置, 长度 * 3, len(arg_数据))
            for k in range(长度):
                r, g, b = struct.unpack_from("3B", arg_数据, 位置)
                self.调色板[(索引 + k) & 255] = (r >> 3) << 10 | (g >> 3) << 5 | b >> 3
                位置 += 3
            索引 += 长度

    def _游程(self, arg_数据: bytes) -> None:
        位置 = 0
        for y in range(self.高):
            位置 += 1
            x = 0
            while x < self.宽:
                数量 = self._整数(arg_数据, 位置, 1, True)
                位置 += 1
                if 数量 == 0:
                    raise ValueError("FLC 零长度 BYTE_RUN")
                长度 = abs(数量)
                if 长度 > self.宽 - x:
                    raise ValueError("FLC 游程跨越行尾")
                if 数量 > 0:
                    字节 = self._整数(arg_数据, 位置, 1)
                    片段 = bytes([字节]) * 长度
                    位置 += 1
                else:
                    资源包_类.api_检查范围(位置, 长度, len(arg_数据))
                    片段 = arg_数据[位置 : 位置 + 长度]
                    位置 += 长度
                起点 = y * self.宽 + x
                self.像素索引[起点 : 起点 + 长度] = 片段
                x += 长度

    def _增量(self, arg_数据: bytes) -> None:
        行数 = self._整数(arg_数据, 0, 2)
        位置 = 2
        y = 0
        while 行数 > 0:
            末像素: int | None = None
            while True:
                操作 = self._整数(arg_数据, 位置, 2)
                位置 += 2
                if 操作 & 0xC000 == 0xC000:
                    y += 65536 - 操作
                elif 操作 & 0xC000 == 0x8000:
                    末像素 = 操作 & 255
                elif 操作 & 0x4000:
                    raise ValueError("未定义 DELTA_FLC 操作码")
                else:
                    break
            if y >= self.高:
                raise ValueError("FLC 增量行越界")
            x = 0
            for _ in range(操作):
                x += self._整数(arg_数据, 位置, 1)
                数量 = self._整数(arg_数据, 位置 + 1, 1, True)
                位置 += 2
                长度 = abs(数量) * 2
                if x > self.宽 or 长度 > self.宽 - x:
                    raise ValueError("FLC 增量游程跨行")
                if 数量 >= 0:
                    资源包_类.api_检查范围(位置, 长度, len(arg_数据))
                    片段 = arg_数据[位置 : 位置 + 长度]
                    位置 += 长度
                else:
                    资源包_类.api_检查范围(位置, 2, len(arg_数据))
                    片段 = arg_数据[位置 : 位置 + 2] * (-数量)
                    位置 += 2
                起点 = y * self.宽 + x
                self.像素索引[起点 : 起点 + 长度] = 片段
                x += 长度
            if 末像素 is not None:
                self.像素索引[y * self.宽 + self.宽 - 1] = 末像素
            y += 1
            行数 -= 1

    def api_图像(self) -> 图像_类:
        return 图像_类(
            self.宽,
            self.高,
            [self.调色板[i] for i in self.像素索引],
            不透明=bytes(i != 0 for i in self.像素索引),
        )
