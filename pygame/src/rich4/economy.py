# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/economy.cpp，街名按原始编码字节比较。
# ◑ 导入
import struct
from dataclasses import dataclass


# ◕ 功能
@dataclass
class 地产经济_类:
    """
    原 52 字节地产记录中的经济字段，未解释字段由完整地图模型保留。

    更新日志：
    2026.10.23 - 对应 LandEconomyRecord 与 decode_land_economy_record。
    """

    街道名: bytes
    连锁: int
    业主: int
    等级: int
    各级租金: tuple[int, ...]

    @classmethod
    def api_解码(cls, arg_数据: bytes) -> "地产经济_类":
        if len(arg_数据) != 52:
            raise ValueError("地产记录必须为 52 字节")
        名字 = arg_数据[4:20]
        if 0 not in 名字:
            raise ValueError("地产名字缺少 NUL")
        return cls(
            名字.split(b"\0", 1)[0],
            arg_数据[0x18],
            arg_数据[0x19],
            arg_数据[0x1A],
            struct.unpack_from("<6H", arg_数据, 0x20),
        )


class 经济_类:
    """
    精确街区汇总和连锁计费；有符号 32 位乘法结果按 x86 低位解释。

    更新日志：
    2026.10.23 - 对应 chain_store_count 和 land_toll。
    """

    @staticmethod
    def api_连锁数(arg_地产: list[地产经济_类], arg_业主: int) -> int:
        return sum(地.连锁 != 0 and 地.业主 == arg_业主 for 地 in arg_地产)

    @staticmethod
    def api_通行费(
        arg_地产: list[地产经济_类],
        arg_业主: int,
        arg_物价: int,
        arg_街道: bytes | None = None,
    ) -> int:
        总额 = 0
        for 地 in arg_地产:
            if 地.业主 != arg_业主:
                continue
            if arg_街道 is None:
                if 地.连锁:
                    总额 += 2000
            elif not 地.连锁 and 地.街道名.split(b"\0", 1)[0] == arg_街道.split(b"\0", 1)[0]:
                if not 0 <= 地.等级 < 6:
                    raise ValueError("匹配的普通地产等级超出 0..5")
                总额 += 地.各级租金[地.等级]
        位 = (总额 * arg_物价) & 0xFFFFFFFF
        return 位 - 0x100000000 if 位 & 0x80000000 else 位
