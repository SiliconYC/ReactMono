# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/direction.cpp，保留 INT32_MIN 的 x86 NEG 回绕。
# ◕ 功能
class 方向_类:
    """
    原八方向编码与整数角度舍入。

    更新日志：
    2026.10.23 - 对应 direction::from_delta。
    """

    @staticmethod
    def api_计算(arg_dx: int, arg_dy: int) -> int:
        x位 = arg_dx & 0xFFFFFFFF
        y位 = -arg_dy & 0xFFFFFFFF
        if (x位 | y位) == 0:
            return 2
        x = (-x位 & 0xFFFFFFFF) if x位 & 0x80000000 else x位
        y = (-y位 & 0xFFFFFFFF) if y位 & 0x80000000 else y位
        比值 = min(x, y) * 2048 // max(x, y)
        角 = 0 if 比值 < 849 else 0x1000 if 比值 == 849 else 0x2000
        if x < y:
            角 = 0x4000 - 角
        if x位 & 0x80000000:
            角 = 0x8000 + 角 if y位 & 0x80000000 else 0x8000 - 角
        elif y位 & 0x80000000:
            角 = -角
        象限 = (((角 & 0xFFFF) >> 12) + 1) >> 1 & 7
        return (2, 3, 4, 5, 6, 7, 0, 1)[象限]
