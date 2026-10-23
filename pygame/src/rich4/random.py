# SPDX-License-Identifier: GPL-3.0-or-later
# 对应固定 C++ src/random.cpp，Watcom CRT 0x456f2d / 0x456f50。
# ◕ 功能
class 随机数_类:
    """
    每局独占原版 32 位随机流，状态可直接保存和恢复。

    更新日志：
    2026.10.23 - 实现 Watcom LCG 和明确的无符号回绕。
    """

    def __init__(self, arg_种子: int) -> None:
        self.状态 = arg_种子 & 0xFFFFFFFF

    def api_下一个(self) -> int:
        self.状态 = (self.状态 * 1103515245 + 12345) & 0xFFFFFFFF
        return (self.状态 >> 16) & 0x7FFF
