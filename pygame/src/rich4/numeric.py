# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ include/rich4/legacy_float.hpp，所有中间舍入用整数表达。
# ◑ 导入
from __future__ import annotations

import struct
from dataclasses import dataclass


# ◕ 功能
class 数值范围错误_类(ValueError):
    """
    区别有限输入的目标浮点范围错误与非法输入/除零。

    更新日志：
    2026.10.23 - 对应 C++ Extended 存储的 std::out_of_range。
    """


@dataclass(frozen=True)
class 扩展数_类:
    """
    有限 x87 64 位有效数；每次运算舍入，落盘再按 IEEE ties-to-even 舍入。

    更新日志：
    2026.10.23 - 对应 numeric::Extended，不依赖宿主 long double 或浮点控制字。
    """

    有效数: int = 0
    指数: int = 0
    负: bool = False

    @classmethod
    def api_归一(
        cls,
        arg_值: int,
        arg_指数: int,
        arg_负: bool = False,
    ) -> 扩展数_类:
        if not 0 <= arg_值 < 1 << 128:
            raise ValueError("扩展归一输入超出无符号128位域")
        if arg_值 == 0:
            return cls()
        长度 = arg_值.bit_length()
        if 长度 > 64:
            移位 = 长度 - 64
            余 = arg_值 & ((1 << 移位) - 1)
            中点 = 1 << (移位 - 1)
            arg_值 >>= 移位
            if 余 > 中点 or (余 == 中点 and arg_值 & 1):
                arg_值 += 1
            arg_指数 += 移位
            if arg_值 == 1 << 64:
                arg_值 >>= 1
                arg_指数 += 1
        else:
            arg_值 <<= 64 - 长度
            arg_指数 -= 64 - 长度
        return cls(arg_值, arg_指数, arg_负)

    @classmethod
    def api_从值(cls, arg_值: float | int) -> 扩展数_类:
        原位 = struct.unpack("<Q", struct.pack("<d", float(arg_值)))[0]
        指数位 = (原位 >> 52) & 2047
        if 指数位 == 2047:
            raise ValueError("扩展运算要求有限输入")
        尾数 = (原位 & 0xFFFFFFFFFFFFF) | (0 if 指数位 == 0 else 0x10000000000000)
        return cls.api_归一(尾数, -1074 if 指数位 == 0 else 指数位 - 1075, bool(原位 >> 63))

    def __neg__(self) -> 扩展数_类:
        return 扩展数_类(self.有效数, self.指数, not self.负)

    def __add__(self, arg_另: 扩展数_类) -> 扩展数_类:
        if not self.有效数:
            return arg_另
        if not arg_另.有效数:
            return self
        大, 小 = self, arg_另
        if 大.指数 < 小.指数 or (大.指数 == 小.指数 and 大.有效数 < 小.有效数):
            大, 小 = 小, 大
        差 = 大.指数 - 小.指数
        大值 = 大.有效数 << 3
        if 差 <= 3:
            小值 = 小.有效数 << (3 - 差)
        elif 差 >= 67:
            小值 = 1
        else:
            位移 = 差 - 3
            小值 = 小.有效数 >> 位移
            小值 |= int(bool(小.有效数 & ((1 << 位移) - 1)))
        return self.api_归一(大值 + 小值 if 大.负 == 小.负 else 大值 - 小值, 大.指数 - 3, 大.负)

    def __sub__(self, arg_另: 扩展数_类) -> 扩展数_类:
        return self + -arg_另

    def __mul__(self, arg_另: 扩展数_类) -> 扩展数_类:
        return self.api_归一(
            self.有效数 * arg_另.有效数, self.指数 + arg_另.指数, self.负 != arg_另.负
        )

    def __truediv__(self, arg_另: 扩展数_类) -> 扩展数_类:
        if not arg_另.有效数:
            raise ValueError("扩展运算除零")
        if not self.有效数:
            return 扩展数_类()
        移位 = 63 if self.有效数 >= arg_另.有效数 else 64
        被除数 = self.有效数 << 移位
        商, 余 = divmod(被除数, arg_另.有效数)
        if 余 * 2 > arg_另.有效数 or (余 * 2 == arg_另.有效数 and 商 & 1):
            商 += 1
        return self.api_归一(商, self.指数 - arg_另.指数 - 移位, self.负 != arg_另.负)

    def _存储位(self, arg_双: bool) -> int:
        if not self.有效数:
            return 0
        幂 = self.指数 + 63
        精度, 最小, 最大, 偏置, 符号位 = (
            (53, -1022, 1023, 1023, 63) if arg_双 else (24, -126, 127, 127, 31)
        )
        if not 最小 <= 幂 <= 最大:
            raise 数值范围错误_类("扩展运算超出目标正常浮点范围")
        移位 = 64 - 精度
        舍入 = self.有效数 >> 移位
        丢弃 = self.有效数 & ((1 << 移位) - 1)
        中点 = 1 << (移位 - 1)
        if 丢弃 > 中点 or (丢弃 == 中点 and 舍入 & 1):
            舍入 += 1
            if 舍入 == 1 << 精度:
                舍入 >>= 1
                幂 += 1
        if 幂 > 最大:
            raise 数值范围错误_类("扩展浮点存储溢出")
        return (
            (int(self.负) << 符号位)
            | ((幂 + 偏置) << (精度 - 1))
            | (舍入 & ((1 << (精度 - 1)) - 1))
        )

    def api_单精度位(self) -> int:
        return self._存储位(False)

    def api_双精度位(self) -> int:
        return self._存储位(True)

    def api_单精度(self) -> float:
        return struct.unpack("<f", struct.pack("<I", self.api_单精度位()))[0]

    def api_双精度(self) -> float:
        return struct.unpack("<d", struct.pack("<Q", self.api_双精度位()))[0]

    def api_整数(self) -> int:
        if not self.有效数 or self.指数 <= -64:
            return 0
        if self.指数 >= 0:
            return -2147483648
        大小 = self.有效数 >> -self.指数
        if 大小 > (0x80000000 if self.负 else 0x7FFFFFFF):
            return -2147483648
        return -大小 if self.负 else 大小
