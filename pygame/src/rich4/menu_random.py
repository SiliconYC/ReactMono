# SPDX-License-Identifier: GPL-3.0-or-later
# 固定menus.cpp的新局补位独占std::mt19937；不能用于取代规则的Watcom随机流。
# ◕ 功能
class 菜单随机_类:
    """
    原新局界面MT19937的32位种子、624词状态和原始输出，不使用Python随机协议。

    更新日志：
    2026.10.24 - UI补位私有随机流，与游戏规则随机数隔离。
    """

    def __init__(self, arg_种子: int = 1) -> None:
        self.api_播种(arg_种子)

    def api_播种(self, arg_种子: int) -> None:
        self._词 = [arg_种子 & 0xFFFFFFFF]
        for i in range(1, 624):
            old = self._词[-1]
            self._词.append((1812433253 * (old ^ (old >> 30)) + i) & 0xFFFFFFFF)
        self._位 = 0

    def api_取(self) -> int:
        i = self._位
        y = (self._词[i] & 0x80000000) | (self._词[(i + 1) % 624] & 0x7FFFFFFF)
        self._词[i] = self._词[(i + 397) % 624] ^ (y >> 1) ^ (0x9908B0DF if y & 1 else 0)
        y = self._词[i]
        self._位 = (i + 1) % 624
        y ^= y >> 11
        y ^= (y << 7) & 0x9D2C5680
        y ^= (y << 15) & 0xEFC60000
        return y ^ (y >> 18)
