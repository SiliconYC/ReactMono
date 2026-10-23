# SPDX-License-Identifier: GPL-3.0-or-later
# 派生自固定 C++ src/save.cpp；布局来自 Iru Cai 的 rich4_save_files.asm/player_info.h。
# ◑ 导入
import struct
from typing import Literal

from rich4.save_records import (
    地图摘要_类,
    地图表_类,
    存档区域_类,
    存档头_类,
    玩家记录_类,
)


# ◕ 功能
class 存档_类:
    """
    0x26 DAT 无损编解码，不解释未知字段，也不将序列化地址当作指针。

    更新日志：
    2026.10.23 - 对应 SaveFile，精确字段写入与完整区域清单。
    """

    地图起点 = 0x274B
    快照长度 = 0x2718

    def __init__(self, arg_数据: bytes) -> None:
        self.数据 = bytearray(arg_数据)
        self.区域: list[存档区域_类] = []

    def _范围(self, arg_偏移: int, arg_长度: int) -> None:
        if arg_偏移 < 0 or arg_长度 < 0 or arg_偏移 + arg_长度 > len(self.数据):
            raise ValueError("存档区域截断或越界")

    def _数(self, arg_格式: str, arg_偏移: int) -> int:
        self._范围(arg_偏移, struct.calcsize(arg_格式))
        return struct.unpack_from(arg_格式, self.数据, arg_偏移)[0]

    @classmethod
    def api_解码(cls, arg_数据: bytes) -> "存档_类":
        存档 = cls(arg_数据)
        存档._范围(0, cls.地图起点)
        if 存档._数("<I", 0) != 0x26:
            raise ValueError("不支持的存档签名，应为 0x26")
        人数 = 存档._数("<I", 12)
        if not 1 <= 人数 <= 4:
            raise ValueError("存档人数必须为 1..4")
        if 存档._数("<I", 0x1B0) > 人数 or 存档._数("<I", 0x2676) >= 人数:
            raise ValueError("存档玩家索引或人类人数越界")
        地图大小 = 存档._数("<I", 0x2747)
        if 地图大小 < 40:
            raise ValueError("存档地图头不完整")
        存档._范围(cls.地图起点, 地图大小)
        摘要 = 存档.api_地图摘要()
        区间: list[tuple[int, int]] = []
        for 表 in 摘要.表:
            末端 = 表.偏移 + (表.数量 + 1) * 表.步长
            if 表.偏移 < 40 or 末端 > 地图大小:
                raise ValueError("地图表超出地图块")
            for 起, 末 in 区间:
                if 表.偏移 < 末 and 起 < 末端:
                    raise ValueError("存档地图表重叠")
            区间.append((表.偏移, 末端))
        存档._建立区域(地图大小, 人数)
        return 存档

    def _加区域(
        self,
        arg_名称: str,
        arg_长度: int,
        arg_类别: Literal["decoded", "partially_decoded", "raw_reserved"],
    ) -> None:
        偏移 = 0 if not self.区域 else self.区域[-1].偏移 + self.区域[-1].长度
        self._范围(偏移, arg_长度)
        self.区域.append(存档区域_类(arg_名称, 偏移, arg_长度, arg_类别))

    def _建立区域(self, arg_地图长: int, arg_人数: int) -> None:
        self._加区域("header", 16, "decoded")
        self._加区域("player_records", 4 * 104, "partially_decoded")
        self._加区域("human_player_count", 4, "decoded")
        for 名称, 大小 in [
            ("raw_reserved_special_players", 5 * 16),
            ("raw_reserved_objects", 46 * 24),
        ]:
            self._加区域(名称, 大小, "raw_reserved")
        self._加区域("player_cards", 60, "decoded")
        self._加区域("player_tool_amounts", 60, "decoded")
        for 名称, 大小 in [
            ("raw_reserved_remaining_cards", 30),
            ("raw_reserved_remaining_tools", 8),
            ("raw_reserved_00499100", 4),
            ("raw_reserved_00497328", 0x6C0 * 4),
            ("raw_reserved_player_stocks", 48 * 8),
            ("raw_reserved_stocks_on_map", 12 * 0x24),
            ("raw_reserved_004967e0", 28 * 12),
        ]:
            self._加区域(名称, 大小, "raw_reserved")
        self._加区域("current_player", 4, "decoded")
        for 名称 in ["00499118", "00499110", "0049911c", "00499108"]:
            self._加区域("raw_reserved_" + 名称, 4, "raw_reserved")
        self._加区域("initial_fund", 4, "decoded")
        self._加区域("price_index", 4, "decoded")
        for 名称, 大小 in [
            ("004990e4", 4),
            ("00499084", 4),
            ("004990dc", 4),
            ("0049907c", 4),
            ("00499078", 4),
            ("004990ec", 4),
            ("004990f0", 4),
            ("004990f4", 12),
            ("00499080", 4),
            ("004990b8", 36),
            ("00496b30", 8),
            ("00496b60", 8),
            ("004990e0", 4),
            ("004990b4", 4),
            ("00499090", 36),
            ("00496b38", 37),
            ("00499088", 4),
        ]:
            self._加区域("raw_reserved_" + 名称, 大小, "raw_reserved")
        self._加区域("map_byte_size", 4, "decoded")
        self._加区域("map_header", 40, "decoded")
        self._加区域("raw_reserved_map_records", arg_地图长 - 40, "raw_reserved")
        for i in range(arg_人数):
            self._加区域(f"raw_reserved_player_snapshot_{i}", self.快照长度, "raw_reserved")
            self._加区域(f"raw_reserved_player_map_snapshot_{i}", arg_地图长, "raw_reserved")
        末端 = self.区域[-1].偏移 + self.区域[-1].长度
        if 末端 < len(self.数据):
            self._加区域("raw_reserved_trailing_bytes", len(self.数据) - 末端, "raw_reserved")

    def api_头(self) -> 存档头_类:
        return 存档头_类(
            self._数("<I", 0),
            (self.数据[4], self.数据[5], self._数("<H", 6)),
            self._数("<H", 8),
            self._数("<H", 10),
            self._数("<I", 12),
            self._数("<I", 0x1B0),
            self._数("<I", 0x2676),
            self._数("<i", 0x268A),
            self._数("<i", 0x268E),
        )

    def _玩家偏移(self, arg_槽位: int) -> int:
        if not 0 <= arg_槽位 < self._数("<I", 12):
            raise IndexError("玩家槽位越界")
        return 0x10 + arg_槽位 * 104

    def api_玩家(self, arg_槽位: int) -> 玩家记录_类:
        偏移 = self._玩家偏移(arg_槽位)
        return 玩家记录_类(
            arg_槽位,
            self._数("<I", 偏移 + 4),
            *(self._数("<H", 偏移 + x) for x in (8, 10, 12, 14)),
            *self.数据[偏移 + 16 : 偏移 + 22],
            *(self._数("<i", 偏移 + x) for x in (28, 32, 36, 40)),
            self._数("<H", 偏移 + 48),
            list(self.数据[0x654 + arg_槽位 * 15 : 0x654 + (arg_槽位 + 1) * 15]),
            list(self.数据[0x690 + arg_槽位 * 15 : 0x690 + (arg_槽位 + 1) * 15]),
        )

    def api_地图摘要(self) -> 地图摘要_类:
        表 = tuple(
            地图表_类(
                self._数("<I", self.地图起点 + i * 8),
                self._数("<I", self.地图起点 + i * 8 + 4),
                步长,
            )
            for i, 步长 in enumerate((40, 52, 56, 52, 28))
        )
        return 地图摘要_类(self._数("<I", 0x2747), 表)

    def api_区域(self) -> tuple[存档区域_类, ...]:
        return tuple(self.区域)

    def api_导出(self) -> bytes:
        return bytes(self.数据)

    def _写整数(self, arg_位置: int, arg_值: int) -> None:
        if not -2147483648 <= arg_值 <= 2147483647:
            raise ValueError("字段超出有符号 32 位范围")
        self._范围(arg_位置, 4)
        struct.pack_into("<i", self.数据, arg_位置, arg_值)

    def api_设现金(self, arg_槽位: int, arg_金额: int) -> None:
        self._写整数(self._玩家偏移(arg_槽位) + 28, arg_金额)

    def api_设银行(self, arg_槽位: int, arg_金额: int) -> None:
        self._写整数(self._玩家偏移(arg_槽位) + 32, arg_金额)
